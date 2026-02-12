import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR
from datetime import datetime
import asyncio
import io
import re


# ============================================================
# TRADE SESSION DATA
# ============================================================

class TradeSession:
    """Stores all data for an active trade"""

    def __init__(self, trade_id: str, user1_id: int, user2_id: int, guild_id: int):
        self.trade_id = trade_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.guild_id = guild_id

        # Items each user is offering
        self.user1_items = []  # List of TradeItem
        self.user2_items = []

        # Confirmation status
        self.user1_confirmed = False
        self.user2_confirmed = False

        # Channel IDs
        self.category_id = None
        self.user1_channel_id = None
        self.user2_channel_id = None
        self.overview_channel_id = None

        # State
        self.state = "pending"  # pending, active, confirmed, completed, cancelled
        self.created_at = datetime.utcnow()

        # File upload mode tracking
        self.awaiting_file_from = None  # user_id if someone clicked "Add File"

    def get_items(self, user_id: int):
        if user_id == self.user1_id:
            return self.user1_items
        elif user_id == self.user2_id:
            return self.user2_items
        return []

    def add_item(self, user_id: int, item):
        if user_id == self.user1_id:
            self.user1_items.append(item)
        elif user_id == self.user2_id:
            self.user2_items.append(item)
        # Reset confirmations when items change
        self.user1_confirmed = False
        self.user2_confirmed = False

    def remove_item(self, user_id: int, index: int):
        items = self.get_items(user_id)
        if 0 <= index < len(items):
            removed = items.pop(index)
            self.user1_confirmed = False
            self.user2_confirmed = False
            return removed
        return None

    def confirm(self, user_id: int):
        if user_id == self.user1_id:
            self.user1_confirmed = True
        elif user_id == self.user2_id:
            self.user2_confirmed = True

    def unconfirm(self, user_id: int):
        if user_id == self.user1_id:
            self.user1_confirmed = False
        elif user_id == self.user2_id:
            self.user2_confirmed = False

    def both_confirmed(self):
        return self.user1_confirmed and self.user2_confirmed

    def get_other_user(self, user_id: int):
        if user_id == self.user1_id:
            return self.user2_id
        return self.user1_id


class TradeItem:
    """Represents a single item in a trade"""

    def __init__(self, item_type: str, **kwargs):
        self.item_type = item_type  # "credits", "pcredits", "ai_credits", "code", "file", "custom"
        self.data = kwargs
        self.added_at = datetime.utcnow()

    def display(self, index: int) -> str:
        emoji_map = {
            "credits": "💰",
            "pcredits": "💎",
            "ai_credits": "🤖",
            "code": "📝",
            "file": "📁",
            "custom": "📦",
        }
        emoji = emoji_map.get(self.item_type, "📦")

        if self.item_type == "credits":
            return f"`{index + 1}.` {emoji} **{self.data.get('amount', 0):,}** Studio Credits"
        elif self.item_type == "pcredits":
            return f"`{index + 1}.` {emoji} **{self.data.get('amount', 0):,}** pCredits"
        elif self.item_type == "ai_credits":
            return f"`{index + 1}.` {emoji} **{self.data.get('amount', 0):,}** AI Credits"
        elif self.item_type == "code":
            lang = self.data.get('language', 'lua')
            lines = self.data.get('line_count', 0)
            name = self.data.get('name', 'Code Snippet')
            return f"`{index + 1}.` {emoji} **{name}** ({lang}, {lines} lines)"
        elif self.item_type == "file":
            fname = self.data.get('filename', 'unknown')
            size = self.data.get('size', 0)
            size_str = f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
            return f"`{index + 1}.` {emoji} **{fname}** ({size_str})"
        elif self.item_type == "custom":
            desc = self.data.get('description', 'Custom item')
            return f"`{index + 1}.` {emoji} **{desc}**"
        return f"`{index + 1}.` {emoji} Unknown item"


# ============================================================
# ACTIVE TRADES MANAGER
# ============================================================

class TradeManager:
    """Manages all active trades"""

    def __init__(self):
        self.trades = {}  # trade_id -> TradeSession
        self.user_trades = {}  # user_id -> trade_id (one trade per user)
        self.pending_requests = {}  # target_user_id -> {from_id, guild_id, message}
        self._counter = 0

    def create_trade_id(self) -> str:
        self._counter += 1
        return f"trade_{int(datetime.utcnow().timestamp())}_{self._counter}"

    def get_user_trade(self, user_id: int) -> TradeSession:
        trade_id = self.user_trades.get(user_id)
        if trade_id:
            return self.trades.get(trade_id)
        return None

    def is_user_trading(self, user_id: int) -> bool:
        trade = self.get_user_trade(user_id)
        return trade is not None and trade.state in ("pending", "active")

    def create_session(self, user1_id: int, user2_id: int, guild_id: int) -> TradeSession:
        trade_id = self.create_trade_id()
        session = TradeSession(trade_id, user1_id, user2_id, guild_id)
        self.trades[trade_id] = session
        self.user_trades[user1_id] = trade_id
        self.user_trades[user2_id] = trade_id
        return session

    def end_session(self, trade_id: str):
        session = self.trades.get(trade_id)
        if session:
            self.user_trades.pop(session.user1_id, None)
            self.user_trades.pop(session.user2_id, None)
            del self.trades[trade_id]

    def get_trade_by_channel(self, channel_id: int) -> TradeSession:
        for trade in self.trades.values():
            if channel_id in (trade.user1_channel_id, trade.user2_channel_id, trade.overview_channel_id):
                return trade
        return None


trade_manager = TradeManager()


# ============================================================
# TRADE REQUEST VIEW (DM)
# ============================================================

class TradeRequestView(discord.ui.View):
    """Sent via DM to accept/decline a trade request"""

    def __init__(self, cog, from_user_id: int, target_user_id: int, guild_id: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.from_user_id = from_user_id
        self.target_user_id = target_user_id
        self.guild_id = guild_id
        self.responded = False

    async def on_timeout(self):
        if not self.responded:
            trade_manager.pending_requests.pop(self.target_user_id, None)
            try:
                for item in self.children:
                    item.disabled = True
            except Exception:
                pass

    @discord.ui.button(label="Accept Trade", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            return

        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        trade_manager.pending_requests.pop(self.target_user_id, None)

        # Check if either user started another trade
        if trade_manager.is_user_trading(self.from_user_id):
            await interaction.followup.send("❌ The other user is already in a trade.")
            return
        if trade_manager.is_user_trading(self.target_user_id):
            await interaction.followup.send("❌ You're already in a trade.")
            return

        await interaction.followup.send("✅ Trade accepted! Setting up trade channels...")

        # Create trade session and channels
        await self.cog.setup_trade_channels(
            interaction.client,
            self.from_user_id,
            self.target_user_id,
            self.guild_id
        )

    @discord.ui.button(label="Decline", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            return

        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        trade_manager.pending_requests.pop(self.target_user_id, None)

        decline_embed = discord.Embed(
            title="❌ Trade Declined",
            description="You declined the trade request.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=decline_embed)

        # Notify the requester
        try:
            from_user = await interaction.client.fetch_user(self.from_user_id)
            notify = discord.Embed(
                title="❌ Trade Declined",
                description=f"**{interaction.user.name}** declined your trade request.",
                color=discord.Color.red()
            )
            await from_user.send(embed=notify)
        except Exception:
            pass


# ============================================================
# ADD ITEM VIEWS
# ============================================================

class AddItemView(discord.ui.View):
    """Main control panel for adding items to a trade"""

    def __init__(self, trade: TradeSession, user_id: int):
        super().__init__(timeout=None)
        self.trade = trade
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your trade channel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Add Credits", emoji="💰", style=discord.ButtonStyle.secondary, row=0)
    async def add_credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CurrencyModal(self.trade, self.user_id, "credits", "Studio Credits")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add pCredits", emoji="💎", style=discord.ButtonStyle.secondary, row=0)
    async def add_pcredits(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CurrencyModal(self.trade, self.user_id, "pcredits", "pCredits")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add AI Credits", emoji="🤖", style=discord.ButtonStyle.secondary, row=0)
    async def add_ai_credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CurrencyModal(self.trade, self.user_id, "ai_credits", "AI Credits")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Code", emoji="📝", style=discord.ButtonStyle.secondary, row=1)
    async def add_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CodeTradeModal(self.trade, self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add File", emoji="📁", style=discord.ButtonStyle.secondary, row=1)
    async def add_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.trade.awaiting_file_from = self.user_id
        embed = discord.Embed(
            title="📁 File Upload Mode",
            description=(
                "**Send your file in the next message.**\n\n"
                "Attach any file (`.lua`, `.rbxm`, `.png`, `.json`, etc.)\n"
                "The file will be added to your trade offer.\n\n"
                "Type `cancel` to exit file upload mode."
            ),
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Add Custom Item", emoji="📦", style=discord.ButtonStyle.secondary, row=1)
    async def add_custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomItemModal(self.trade, self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove Item", emoji="🗑️", style=discord.ButtonStyle.danger, row=2)
    async def remove_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = self.trade.get_items(self.user_id)
        if not items:
            await interaction.response.send_message("You have no items to remove.", ephemeral=True)
            return

        view = RemoveItemView(self.trade, self.user_id)
        embed = discord.Embed(
            title="🗑️ Remove an Item",
            description="Select which item to remove:",
            color=discord.Color.red()
        )
        for i, item in enumerate(items):
            embed.description += f"\n{item.display(i)}"

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="✅ Confirm Trade", emoji="🤝", style=discord.ButtonStyle.success, row=3)
    async def confirm_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = self.trade.get_items(self.user_id)
        other_items = self.trade.get_items(self.trade.get_other_user(self.user_id))

        if not items and not other_items:
            await interaction.response.send_message(
                "❌ Both sides need at least some items before confirming.",
                ephemeral=True
            )
            return

        self.trade.confirm(self.user_id)

        if self.trade.both_confirmed():
            await interaction.response.defer()
            await execute_trade(interaction.client, self.trade)
        else:
            other_id = self.trade.get_other_user(self.user_id)
            embed = discord.Embed(
                title="✅ You Confirmed!",
                description=f"Waiting for <@{other_id}> to confirm...\n\nThey can see your offer has been locked in.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

            # Notify the other user
            await update_overview(interaction.client, self.trade)

    @discord.ui.button(label="❌ Cancel Trade", emoji="🚫", style=discord.ButtonStyle.danger, row=3)
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = CancelConfirmView(self.trade, self.user_id)
        await interaction.response.send_message(
            "Are you sure you want to **cancel** this trade? All items will be returned.",
            view=view,
            ephemeral=True
        )


class CancelConfirmView(discord.ui.View):
    """Confirmation before cancelling a trade"""

    def __init__(self, trade: TradeSession, user_id: int):
        super().__init__(timeout=30)
        self.trade = trade
        self.user_id = user_id

    @discord.ui.button(label="Yes, Cancel", style=discord.ButtonStyle.danger)
    async def confirm_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await cancel_trade(interaction.client, self.trade, self.user_id)

    @discord.ui.button(label="No, Keep Trading", style=discord.ButtonStyle.secondary)
    async def keep_trading(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Trade continues!", view=self)


# ============================================================
# REMOVE ITEM VIEW
# ============================================================

class RemoveItemView(discord.ui.View):
    """Buttons to remove specific items"""

    def __init__(self, trade: TradeSession, user_id: int):
        super().__init__(timeout=60)
        self.trade = trade
        self.user_id = user_id

        items = trade.get_items(user_id)
        for i, item in enumerate(items[:10]):  # Max 10 items
            emoji_map = {
                "credits": "💰", "pcredits": "💎", "ai_credits": "🤖",
                "code": "📝", "file": "📁", "custom": "📦"
            }
            emoji = emoji_map.get(item.item_type, "📦")

            # Get short label
            if item.item_type in ("credits", "pcredits", "ai_credits"):
                label = f"#{i + 1} — {item.data.get('amount', 0):,}"
            elif item.item_type == "file":
                label = f"#{i + 1} — {item.data.get('filename', '?')[:20]}"
            elif item.item_type == "code":
                label = f"#{i + 1} — {item.data.get('name', 'Code')[:20]}"
            else:
                label = f"#{i + 1} — {item.data.get('description', '?')[:20]}"

            btn = RemoveItemButton(trade, user_id, i, label, emoji)
            self.add_item(btn)


class RemoveItemButton(discord.ui.Button):
    """Individual remove button"""

    def __init__(self, trade: TradeSession, user_id: int, index: int, label: str, emoji: str):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.danger)
        self.trade = trade
        self.user_id = user_id
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return

        removed = self.trade.remove_item(self.user_id, self.index)
        if removed:
            await interaction.response.send_message(
                f"🗑️ Removed: {removed.display(0)}",
                ephemeral=True
            )
            # Update the trade display
            await update_trade_channel(interaction.client, self.trade, self.user_id)
            await update_overview(interaction.client, self.trade)
        else:
            await interaction.response.send_message("❌ Could not remove that item.", ephemeral=True)


# ============================================================
# MODALS
# ============================================================

class CurrencyModal(discord.ui.Modal):
    """Modal for adding currency to trade"""

    def __init__(self, trade: TradeSession, user_id: int, currency_type: str, currency_name: str):
        super().__init__(title=f"Add {currency_name}")
        self.trade = trade
        self.user_id = user_id
        self.currency_type = currency_type
        self.currency_name = currency_name

        self.amount_input = discord.ui.TextInput(
            label=f"Amount of {currency_name}",
            placeholder="Enter a number (e.g. 500)",
            required=True,
            max_length=15
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value.replace(",", "").strip())
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
            return

        # Verify user has enough
        user = await UserProfile.get_user(self.user_id)
        if not user:
            await interaction.response.send_message("❌ Profile not found.", ephemeral=True)
            return

        balance_map = {
            "credits": "studio_credits",
            "pcredits": "pcredits",
            "ai_credits": "ai_credits"
        }
        field = balance_map.get(self.currency_type, "studio_credits")
        current_balance = user.get(field, 0)

        # Calculate total already offered of this type
        existing_offered = sum(
            item.data.get('amount', 0)
            for item in self.trade.get_items(self.user_id)
            if item.item_type == self.currency_type
        )

        if existing_offered + amount > current_balance:
            await interaction.response.send_message(
                f"❌ You don't have enough {self.currency_name}.\n"
                f"Balance: **{current_balance:,}** | Already offering: **{existing_offered:,}** | "
                f"Trying to add: **{amount:,}**",
                ephemeral=True
            )
            return

        item = TradeItem(self.currency_type, amount=amount)
        self.trade.add_item(self.user_id, item)

        await interaction.response.send_message(
            f"✅ Added **{amount:,} {self.currency_name}** to your offer!",
            ephemeral=True
        )

        await update_trade_channel(interaction.client, self.trade, self.user_id)
        await update_overview(interaction.client, self.trade)


class CodeTradeModal(discord.ui.Modal, title="Add Code to Trade"):
    """Modal for adding code snippets"""

    code_name = discord.ui.TextInput(
        label="Code Name",
        placeholder="e.g. Combat System, DataStore Handler",
        required=True,
        max_length=100
    )

    language = discord.ui.TextInput(
        label="Language",
        placeholder="lua, python, javascript, etc.",
        required=True,
        max_length=20,
        default="lua"
    )

    code_content = discord.ui.TextInput(
        label="Code",
        placeholder="Paste your code here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    def __init__(self, trade: TradeSession, user_id: int):
        super().__init__()
        self.trade = trade
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code_content.value
        line_count = len(code.strip().split("\n"))
        name = self.code_name.value
        lang = self.language.value.lower().strip()

        item = TradeItem("code", name=name, language=lang, code=code, line_count=line_count)
        self.trade.add_item(self.user_id, item)

        await interaction.response.send_message(
            f"✅ Added code **{name}** ({lang}, {line_count} lines) to your offer!",
            ephemeral=True
        )

        await update_trade_channel(interaction.client, self.trade, self.user_id)
        await update_overview(interaction.client, self.trade)


class CustomItemModal(discord.ui.Modal, title="Add Custom Item"):
    """Modal for adding custom/miscellaneous items"""

    description = discord.ui.TextInput(
        label="Item Description",
        placeholder="e.g. UI Design for lobby, 3D Model of sword, Game testing service",
        required=True,
        max_length=200
    )

    details = discord.ui.TextInput(
        label="Additional Details (optional)",
        placeholder="Any extra info about this item...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    def __init__(self, trade: TradeSession, user_id: int):
        super().__init__()
        self.trade = trade
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        desc = self.description.value
        details = self.details.value or ""

        item = TradeItem("custom", description=desc, details=details)
        self.trade.add_item(self.user_id, item)

        await interaction.response.send_message(
            f"✅ Added custom item **{desc}** to your offer!",
            ephemeral=True
        )

        await update_trade_channel(interaction.client, self.trade, self.user_id)
        await update_overview(interaction.client, self.trade)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def build_offer_embed(trade: TradeSession, user_id: int, user_name: str) -> discord.Embed:
    """Build an embed showing one user's offer"""
    items = trade.get_items(user_id)
    is_confirmed = (trade.user1_confirmed if user_id == trade.user1_id else trade.user2_confirmed)

    status_icon = "🔒" if is_confirmed else "📝"
    status_text = "CONFIRMED" if is_confirmed else "EDITING"

    embed = discord.Embed(
        title=f"{status_icon} {user_name}'s Offer — {status_text}",
        color=discord.Color.green() if is_confirmed else 0x5865F2
    )

    if items:
        item_lines = []
        for i, item in enumerate(items):
            item_lines.append(item.display(i))
        embed.description = "\n".join(item_lines)

        # Summary
        total_credits = sum(i.data.get('amount', 0) for i in items if i.item_type == "credits")
        total_pcredits = sum(i.data.get('amount', 0) for i in items if i.item_type == "pcredits")
        total_ai = sum(i.data.get('amount', 0) for i in items if i.item_type == "ai_credits")
        file_count = sum(1 for i in items if i.item_type == "file")
        code_count = sum(1 for i in items if i.item_type == "code")
        custom_count = sum(1 for i in items if i.item_type == "custom")

        summary_parts = []
        if total_credits > 0:
            summary_parts.append(f"💰 {total_credits:,}")
        if total_pcredits > 0:
            summary_parts.append(f"💎 {total_pcredits:,}")
        if total_ai > 0:
            summary_parts.append(f"🤖 {total_ai:,}")
        if file_count > 0:
            summary_parts.append(f"📁 {file_count} file(s)")
        if code_count > 0:
            summary_parts.append(f"📝 {code_count} code(s)")
        if custom_count > 0:
            summary_parts.append(f"📦 {custom_count} item(s)")

        embed.add_field(
            name="📊 Summary",
            value=" · ".join(summary_parts) if summary_parts else "Empty",
            inline=False
        )
    else:
        embed.description = "*No items added yet*\n\nUse the buttons below to add items to your offer."

    embed.set_footer(text=f"Items: {len(items)} | Trade ID: {trade.trade_id[:15]}")
    return embed


def build_overview_embed(trade: TradeSession, user1_name: str, user2_name: str) -> discord.Embed:
    """Build the overview embed showing both sides"""
    u1_confirmed = "🔒 Confirmed" if trade.user1_confirmed else "📝 Editing"
    u2_confirmed = "🔒 Confirmed" if trade.user2_confirmed else "📝 Editing"

    embed = discord.Embed(
        title="🤝 Trade Overview",
        color=discord.Color.green() if trade.both_confirmed() else 0x5865F2
    )

    # User 1 offer
    u1_items = trade.get_items(trade.user1_id)
    if u1_items:
        u1_text = "\n".join([item.display(i) for i, item in enumerate(u1_items)])
    else:
        u1_text = "*No items yet*"
    embed.add_field(
        name=f"{'🔒' if trade.user1_confirmed else '📝'} {user1_name}'s Offer",
        value=u1_text[:1024],
        inline=False
    )

    # Separator
    embed.add_field(name="⇅", value="─────────────────────", inline=False)

    # User 2 offer
    u2_items = trade.get_items(trade.user2_id)
    if u2_items:
        u2_text = "\n".join([item.display(i) for i, item in enumerate(u2_items)])
    else:
        u2_text = "*No items yet*"
    embed.add_field(
        name=f"{'🔒' if trade.user2_confirmed else '📝'} {user2_name}'s Offer",
        value=u2_text[:1024],
        inline=False
    )

    # Status
    if trade.both_confirmed():
        embed.add_field(
            name="✅ Status",
            value="**Both users confirmed! Executing trade...**",
            inline=False
        )
    else:
        status_parts = []
        status_parts.append(f"{user1_name}: {u1_confirmed}")
        status_parts.append(f"{user2_name}: {u2_confirmed}")
        embed.add_field(
            name="📋 Status",
            value="\n".join(status_parts),
            inline=False
        )

    embed.set_footer(text=f"Trade ID: {trade.trade_id[:15]} | Both users must confirm to complete")
    embed.timestamp = trade.created_at
    return embed


async def update_trade_channel(client, trade: TradeSession, user_id: int):
    """Update the offer display in a user's trade channel"""
    channel_id = trade.user1_channel_id if user_id == trade.user1_id else trade.user2_channel_id
    if not channel_id:
        return

    try:
        channel = client.get_channel(channel_id)
        if not channel:
            channel = await client.fetch_channel(channel_id)

        user = await client.fetch_user(user_id)
        embed = build_offer_embed(trade, user_id, user.display_name)

        # Find and update or send new
        async for msg in channel.history(limit=20):
            if msg.author.id == client.user.id and msg.embeds:
                for e in msg.embeds:
                    if e.title and "Offer" in e.title:
                        view = AddItemView(trade, user_id)
                        await msg.edit(embed=embed, view=view)
                        return

        # Send new if not found
        view = AddItemView(trade, user_id)
        await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"[Trade] Update channel error: {e}")


async def update_overview(client, trade: TradeSession):
    """Update the overview channel"""
    if not trade.overview_channel_id:
        return

    try:
        channel = client.get_channel(trade.overview_channel_id)
        if not channel:
            channel = await client.fetch_channel(trade.overview_channel_id)

        user1 = await client.fetch_user(trade.user1_id)
        user2 = await client.fetch_user(trade.user2_id)
        embed = build_overview_embed(trade, user1.display_name, user2.display_name)

        # Find and update
        async for msg in channel.history(limit=20):
            if msg.author.id == client.user.id and msg.embeds:
                for e in msg.embeds:
                    if e.title and "Overview" in e.title:
                        await msg.edit(embed=embed)
                        return

        await channel.send(embed=embed)
    except Exception as e:
        print(f"[Trade] Update overview error: {e}")


# ============================================================
# TRADE EXECUTION
# ============================================================

async def execute_trade(client, trade: TradeSession):
    """Execute a confirmed trade — transfer all items"""
    trade.state = "completed"

    user1 = await UserProfile.get_user(trade.user1_id)
    user2 = await UserProfile.get_user(trade.user2_id)

    if not user1 or not user2:
        # Notify both channels
        for ch_id in [trade.user1_channel_id, trade.user2_channel_id, trade.overview_channel_id]:
            if ch_id:
                try:
                    ch = client.get_channel(ch_id) or await client.fetch_channel(ch_id)
                    await ch.send("❌ Trade failed — could not find user profiles.")
                except Exception:
                    pass
        return

    # Verify all currency amounts
    u1_credits = sum(i.data.get('amount', 0) for i in trade.user1_items if i.item_type == "credits")
    u1_pcredits = sum(i.data.get('amount', 0) for i in trade.user1_items if i.item_type == "pcredits")
    u1_ai = sum(i.data.get('amount', 0) for i in trade.user1_items if i.item_type == "ai_credits")

    u2_credits = sum(i.data.get('amount', 0) for i in trade.user2_items if i.item_type == "credits")
    u2_pcredits = sum(i.data.get('amount', 0) for i in trade.user2_items if i.item_type == "pcredits")
    u2_ai = sum(i.data.get('amount', 0) for i in trade.user2_items if i.item_type == "ai_credits")

    # Verify balances
    if user1.get('studio_credits', 0) < u1_credits:
        await notify_trade_error(client, trade, f"<@{trade.user1_id}> doesn't have enough Studio Credits!")
        return
    if user1.get('pcredits', 0) < u1_pcredits:
        await notify_trade_error(client, trade, f"<@{trade.user1_id}> doesn't have enough pCredits!")
        return
    if user1.get('ai_credits', 0) < u1_ai:
        await notify_trade_error(client, trade, f"<@{trade.user1_id}> doesn't have enough AI Credits!")
        return
    if user2.get('studio_credits', 0) < u2_credits:
        await notify_trade_error(client, trade, f"<@{trade.user2_id}> doesn't have enough Studio Credits!")
        return
    if user2.get('pcredits', 0) < u2_pcredits:
        await notify_trade_error(client, trade, f"<@{trade.user2_id}> doesn't have enough pCredits!")
        return
    if user2.get('ai_credits', 0) < u2_ai:
        await notify_trade_error(client, trade, f"<@{trade.user2_id}> doesn't have enough AI Credits!")
        return

    # Execute currency transfers
    # User1 gives, User2 receives
    await UserProfile.update_user(trade.user1_id, {
        "studio_credits": user1.get('studio_credits', 0) - u1_credits + u2_credits,
        "pcredits": user1.get('pcredits', 0) - u1_pcredits + u2_pcredits,
        "ai_credits": user1.get('ai_credits', 0) - u1_ai + u2_ai,
    })

    await UserProfile.update_user(trade.user2_id, {
        "studio_credits": user2.get('studio_credits', 0) - u2_credits + u1_credits,
        "pcredits": user2.get('pcredits', 0) - u2_pcredits + u1_pcredits,
        "ai_credits": user2.get('ai_credits', 0) - u2_ai + u1_ai,
    })

    # Send files and code to the receiving user's DMs
    try:
        user1_discord = await client.fetch_user(trade.user1_id)
        user2_discord = await client.fetch_user(trade.user2_id)

        # Send User1's items to User2
        await send_trade_items_dm(user2_discord, trade.user1_items, user1_discord.display_name)

        # Send User2's items to User1
        await send_trade_items_dm(user1_discord, trade.user2_items, user2_discord.display_name)
    except Exception as e:
        print(f"[Trade] DM delivery error: {e}")

    # Build completion embed
    completion_embed = discord.Embed(
        title="✅ Trade Complete!",
        description="All items have been transferred successfully.",
        color=discord.Color.green()
    )

    # Summary of what each user received
    u1_received = []
    if u2_credits > 0:
        u1_received.append(f"💰 {u2_credits:,} Studio Credits")
    if u2_pcredits > 0:
        u1_received.append(f"💎 {u2_pcredits:,} pCredits")
    if u2_ai > 0:
        u1_received.append(f"🤖 {u2_ai:,} AI Credits")
    u1_received.extend([
        item.display(0) for item in trade.user2_items
        if item.item_type in ("code", "file", "custom")
    ])

    u2_received = []
    if u1_credits > 0:
        u2_received.append(f"💰 {u1_credits:,} Studio Credits")
    if u1_pcredits > 0:
        u2_received.append(f"💎 {u1_pcredits:,} pCredits")
    if u1_ai > 0:
        u2_received.append(f"🤖 {u1_ai:,} AI Credits")
    u2_received.extend([
        item.display(0) for item in trade.user1_items
        if item.item_type in ("code", "file", "custom")
    ])

    completion_embed.add_field(
        name=f"📥 {user1_discord.display_name} Received",
        value="\n".join(u1_received) if u1_received else "Nothing",
        inline=False
    )
    completion_embed.add_field(
        name=f"📥 {user2_discord.display_name} Received",
        value="\n".join(u2_received) if u2_received else "Nothing",
        inline=False
    )

    completion_embed.set_footer(text="Channels will be deleted in 30 seconds.")
    completion_embed.timestamp = datetime.utcnow()

    # Send to overview
    if trade.overview_channel_id:
        try:
            ch = client.get_channel(trade.overview_channel_id) or await client.fetch_channel(trade.overview_channel_id)
            await ch.send(embed=completion_embed)
        except Exception:
            pass

    # Cleanup after delay
    await asyncio.sleep(30)
    await cleanup_trade(client, trade)


async def send_trade_items_dm(user, items, from_name):
    """Send non-currency trade items via DM"""
    code_items = [i for i in items if i.item_type == "code"]
    file_items = [i for i in items if i.item_type == "file"]
    custom_items = [i for i in items if i.item_type == "custom"]

    if not code_items and not file_items and not custom_items:
        return

    header = discord.Embed(
        title=f"📦 Trade Items from {from_name}",
        description="Here are the items you received from the trade:",
        color=discord.Color.green()
    )
    await user.send(embed=header)

    for item in code_items:
        code = item.data.get('code', '')
        name = item.data.get('name', 'code')
        lang = item.data.get('language', 'lua')

        # Send as file attachment
        ext_map = {"lua": ".lua", "python": ".py", "javascript": ".js", "typescript": ".ts", "json": ".json"}
        ext = ext_map.get(lang, ".txt")
        filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', name) + ext

        buffer = io.BytesIO(code.encode('utf-8'))
        file = discord.File(buffer, filename=filename)
        await user.send(f"📝 **{name}** ({lang}, {item.data.get('line_count', 0)} lines)", file=file)
        await asyncio.sleep(0.5)

    for item in file_items:
        file_data = item.data.get('file_bytes')
        filename = item.data.get('filename', 'file')
        if file_data:
            buffer = io.BytesIO(file_data)
            file = discord.File(buffer, filename=filename)
            await user.send(f"📁 **{filename}**", file=file)
            await asyncio.sleep(0.5)

    for item in custom_items:
        desc = item.data.get('description', 'Custom item')
        details = item.data.get('details', '')
        text = f"📦 **{desc}**"
        if details:
            text += f"\n{details}"
        await user.send(text)
        await asyncio.sleep(0.3)


async def notify_trade_error(client, trade: TradeSession, error_msg: str):
    """Notify both users of a trade error"""
    embed = discord.Embed(
        title="❌ Trade Failed",
        description=error_msg,
        color=discord.Color.red()
    )

    trade.state = "cancelled"
    trade.user1_confirmed = False
    trade.user2_confirmed = False

    for ch_id in [trade.user1_channel_id, trade.user2_channel_id, trade.overview_channel_id]:
        if ch_id:
            try:
                ch = client.get_channel(ch_id) or await client.fetch_channel(ch_id)
                await ch.send(embed=embed)
            except Exception:
                pass


async def cancel_trade(client, trade: TradeSession, cancelled_by: int):
    """Cancel an active trade"""
    trade.state = "cancelled"

    cancel_embed = discord.Embed(
        title="🚫 Trade Cancelled",
        description=f"Trade was cancelled by <@{cancelled_by}>.\nNo items were transferred.",
        color=discord.Color.red()
    )
    cancel_embed.set_footer(text="Channels will be deleted in 15 seconds.")

    for ch_id in [trade.user1_channel_id, trade.user2_channel_id, trade.overview_channel_id]:
        if ch_id:
            try:
                ch = client.get_channel(ch_id) or await client.fetch_channel(ch_id)
                await ch.send(embed=cancel_embed)
            except Exception:
                pass

    await asyncio.sleep(15)
    await cleanup_trade(client, trade)


async def cleanup_trade(client, trade: TradeSession):
    """Delete trade channels and category"""
    trade_id = trade.trade_id

    # Delete channels
    for ch_id in [trade.user1_channel_id, trade.user2_channel_id, trade.overview_channel_id]:
        if ch_id:
            try:
                ch = client.get_channel(ch_id) or await client.fetch_channel(ch_id)
                await ch.delete(reason="Trade ended")
            except Exception:
                pass

    # Delete category
    if trade.category_id:
        try:
            cat = client.get_channel(trade.category_id) or await client.fetch_channel(trade.category_id)
            await cat.delete(reason="Trade ended")
        except Exception:
            pass

    trade_manager.end_session(trade_id)


# ============================================================
# TRADING COG
# ============================================================

class TradingCog(commands.Cog):
    """Trading system for exchanging items between users"""

    def __init__(self, bot):
        self.bot = bot

    async def setup_trade_channels(self, client, user1_id: int, user2_id: int, guild_id: int):
        """Create the trade category and channels"""
        guild = client.get_guild(guild_id)
        if not guild:
            return

        user1 = await client.fetch_user(user1_id)
        user2 = await client.fetch_user(user2_id)
        member1 = guild.get_member(user1_id)
        member2 = guild.get_member(user2_id)

        if not member1 or not member2:
            return

        session = trade_manager.create_session(user1_id, user2_id, guild_id)
        session.state = "active"

        # Create category
        category_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            ),
        }

        category = await guild.create_category(
            name=f"🤝 Trade — {user1.display_name[:12]} × {user2.display_name[:12]}",
            overwrites=category_overwrites
        )
        session.category_id = category.id

        # Overview channel (both can see, neither can type)
        overview_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member1: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            member2: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            ),
        }

        overview_ch = await guild.create_text_channel(
            name="📋-trade-overview",
            category=category,
            overwrites=overview_overwrites
        )
        session.overview_channel_id = overview_ch.id

        # User 1 private channel
        u1_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member1: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            ),
        }

        u1_ch = await guild.create_text_channel(
            name=f"💼-{user1.display_name[:20]}",
            category=category,
            overwrites=u1_overwrites
        )
        session.user1_channel_id = u1_ch.id

        # User 2 private channel
        u2_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member2: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            ),
        }

        u2_ch = await guild.create_text_channel(
            name=f"💼-{user2.display_name[:20]}",
            category=category,
            overwrites=u2_overwrites
        )
        session.user2_channel_id = u2_ch.id

        # Send overview
        overview_embed = build_overview_embed(session, user1.display_name, user2.display_name)
        overview_embed.add_field(
            name="📖 How Trading Works",
            value=(
                "1️⃣ Go to **your private channel** below\n"
                "2️⃣ Use the buttons to **add items** you want to offer\n"
                "3️⃣ Both users can see the overview here\n"
                "4️⃣ When ready, click **✅ Confirm Trade**\n"
                "5️⃣ When **both** confirm, the trade executes!\n\n"
                "⚠️ Changing items resets confirmations.\n"
                "🚫 Either user can cancel anytime."
            ),
            inline=False
        )
        await overview_ch.send(embed=overview_embed)

        # Send welcome + controls to each channel
        for uid, ch in [(user1_id, u1_ch), (user2_id, u2_ch)]:
            other_id = user2_id if uid == user1_id else user1_id
            other_name = user2.display_name if uid == user1_id else user1.display_name

            welcome_embed = discord.Embed(
                title="💼 Your Trade Offer",
                description=(
                    f"This is your **private trade channel**.\n"
                    f"Trading with: **{other_name}**\n\n"
                    f"Use the buttons below to add items to your offer.\n"
                    f"The other user can see your offer in the overview channel.\n\n"
                    f"**Available Items:**\n"
                    f"💰 Studio Credits · 💎 pCredits · 🤖 AI Credits\n"
                    f"📝 Code Snippets · 📁 Files · 📦 Custom Items"
                ),
                color=0x5865F2
            )
            welcome_embed.set_footer(text="Your offer starts empty. Add items below!")

            offer_embed = build_offer_embed(session, uid, (user1 if uid == user1_id else user2).display_name)
            view = AddItemView(session, uid)

            await ch.send(embed=welcome_embed)
            await ch.send(embed=offer_embed, view=view)

        # Notify both users
        try:
            notify_embed = discord.Embed(
                title="🤝 Trade Channels Ready!",
                description=f"Your trade channels have been created in **{guild.name}**!\nGo to your private channel to start adding items.",
                color=discord.Color.green()
            )
            await user1.send(embed=notify_embed)
            await user2.send(embed=notify_embed)
        except Exception:
            pass

        # Auto-cleanup after 30 minutes
        await asyncio.sleep(1800)
        if session.state == "active":
            timeout_embed = discord.Embed(
                title="⏰ Trade Expired",
                description="This trade has expired after 30 minutes of inactivity.\nNo items were transferred.",
                color=discord.Color.orange()
            )
            for ch_id in [session.overview_channel_id, session.user1_channel_id, session.user2_channel_id]:
                if ch_id:
                    try:
                        ch = client.get_channel(ch_id) or await client.fetch_channel(ch_id)
                        await ch.send(embed=timeout_embed)
                    except Exception:
                        pass
            await asyncio.sleep(15)
            await cleanup_trade(client, session)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle file uploads in trade channels"""
        if message.author.bot:
            return

        trade = trade_manager.get_trade_by_channel(message.channel.id)
        if not trade or trade.state != "active":
            return

        # Check if this is in a user's private trade channel
        user_id = message.author.id
        is_user1_channel = message.channel.id == trade.user1_channel_id and user_id == trade.user1_id
        is_user2_channel = message.channel.id == trade.user2_channel_id and user_id == trade.user2_id

        if not is_user1_channel and not is_user2_channel:
            return

        # Check if we're awaiting a file from this user
        if trade.awaiting_file_from == user_id:
            if message.content.lower().strip() == "cancel":
                trade.awaiting_file_from = None
                await message.reply("📁 File upload cancelled.")
                return

            if message.attachments:
                trade.awaiting_file_from = None

                for attachment in message.attachments[:5]:  # Max 5 files at once
                    try:
                        file_bytes = await attachment.read()
                        item = TradeItem(
                            "file",
                            filename=attachment.filename,
                            size=attachment.size,
                            file_bytes=file_bytes,
                            content_type=attachment.content_type or "application/octet-stream"
                        )
                        trade.add_item(user_id, item)

                        size_str = f"{attachment.size:,} bytes" if attachment.size < 1024 else f"{attachment.size / 1024:.1f} KB"
                        await message.reply(f"✅ Added file **{attachment.filename}** ({size_str}) to your offer!")
                    except Exception as e:
                        await message.reply(f"❌ Failed to add **{attachment.filename}**: {str(e)[:100]}")

                await update_trade_channel(self.bot, trade, user_id)
                await update_overview(self.bot, trade)
            else:
                await message.reply("📁 Please attach a file, or type `cancel` to exit file upload mode.")


async def setup(bot):
    @bot.tree.command(name="trade", description="Start a trade with another user")
    @app_commands.describe(user="The user you want to trade with")
    async def trade_cmd(interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)

        # Validations
        if user.id == interaction.user.id:
            await interaction.followup.send("❌ You can't trade with yourself.", ephemeral=True)
            return

        if user.bot:
            await interaction.followup.send("❌ You can't trade with a bot.", ephemeral=True)
            return

        if trade_manager.is_user_trading(interaction.user.id):
            await interaction.followup.send(
                "❌ You're already in an active trade. Finish or cancel it first.",
                ephemeral=True
            )
            return

        if trade_manager.is_user_trading(user.id):
            await interaction.followup.send(
                f"❌ **{user.display_name}** is already in a trade.",
                ephemeral=True
            )
            return

        if user.id in trade_manager.pending_requests:
            await interaction.followup.send(
                f"❌ **{user.display_name}** already has a pending trade request.",
                ephemeral=True
            )
            return

        # Check if both users have profiles
        u1_profile = await UserProfile.get_user(interaction.user.id)
        if not u1_profile:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)

        u2_profile = await UserProfile.get_user(user.id)
        if not u2_profile:
            await interaction.followup.send(
                f"❌ **{user.display_name}** doesn't have a profile yet. They need to use `/start` first.",
                ephemeral=True
            )
            return

        # Send trade request DM
        request_embed = discord.Embed(
            title="🤝 Trade Request!",
            description=(
                f"**{interaction.user.display_name}** wants to trade with you!\n\n"
                f"**Server:** {interaction.guild.name}\n\n"
                f"**What you can trade:**\n"
                f"💰 Studio Credits · 💎 pCredits · 🤖 AI Credits\n"
                f"📝 Code · 📁 Files · 📦 Custom Items\n\n"
                f"Accept to create private trade channels."
            ),
            color=0x5865F2
        )
        request_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        request_embed.set_footer(text="This request expires in 5 minutes.")
        request_embed.timestamp = datetime.utcnow()

        cog = bot.get_cog("TradingCog")
        view = TradeRequestView(cog, interaction.user.id, user.id, interaction.guild.id)

        try:
            dm_msg = await user.send(embed=request_embed, view=view)
            trade_manager.pending_requests[user.id] = {
                "from_id": interaction.user.id,
                "guild_id": interaction.guild.id,
                "message": dm_msg
            }
        except discord.Forbidden:
            await interaction.followup.send(
                f"❌ Could not send DM to **{user.display_name}**. They may have DMs disabled.",
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error sending trade request: {str(e)[:100]}",
                ephemeral=True
            )
            return

        sent_embed = discord.Embed(
            title="📤 Trade Request Sent!",
            description=(
                f"Sent a trade request to **{user.display_name}**.\n"
                f"Waiting for them to accept...\n\n"
                f"The request expires in **5 minutes**."
            ),
            color=discord.Color.green()
        )
        sent_embed.set_footer(text="You'll be notified when they respond.")
        await interaction.followup.send(embed=sent_embed, ephemeral=True)

    await bot.add_cog(TradingCog(bot))