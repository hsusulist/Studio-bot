import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile, MarketplaceData, TransactionData, UPLOADS_DIR
from config import BOT_COLOR
import os
import uuid
from datetime import datetime

# ==================== CATEGORY EMOJIS ====================
CATEGORY_EMOJIS = {
    "code": "📝",
    "build": "🏗️",
    "ui": "🎨"
}


# ==================== SHOP MAIN VIEW ====================
class ShopView(discord.ui.View):
    """Main shop navigation"""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.current_page = 1
        self.category = None
        self.sort_by = "newest"
        self.search_query = None

    @discord.ui.button(label="All", emoji="🛍️", style=discord.ButtonStyle.blurple, row=0)
    async def all_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.category = None
        self.current_page = 1
        await self.show_listings(interaction)

    @discord.ui.button(label="Code", emoji="📝", style=discord.ButtonStyle.secondary, row=0)
    async def code_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.category = "code"
        self.current_page = 1
        await self.show_listings(interaction)

    @discord.ui.button(label="Builds", emoji="🏗️", style=discord.ButtonStyle.secondary, row=0)
    async def build_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.category = "build"
        self.current_page = 1
        await self.show_listings(interaction)

    @discord.ui.button(label="UIs", emoji="🎨", style=discord.ButtonStyle.secondary, row=0)
    async def ui_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.category = "ui"
        self.current_page = 1
        await self.show_listings(interaction)

    @discord.ui.button(label="Search", emoji="🔍", style=discord.ButtonStyle.success, row=1)
    async def search(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SearchModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Sort", emoji="📊", style=discord.ButtonStyle.secondary, row=1)
    async def sort(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = SortSelectView(self)
        embed = discord.Embed(
            title="📊 Sort Listings",
            description="Choose how to sort the listings:",
            color=BOT_COLOR
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=2)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
            await self.show_listings(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, row=2)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.show_listings(interaction)

    @discord.ui.button(label="My Balance", emoji="💰", style=discord.ButtonStyle.success, row=2)
    async def balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await UserProfile.get_user(self.user_id)
        if not user:
            await UserProfile.create_user(self.user_id, interaction.user.name)
            user = await UserProfile.get_user(self.user_id)

        embed = discord.Embed(
            title="💰 Your Balance",
            color=BOT_COLOR
        )
        embed.add_field(name="Credits", value=f"**{user.get('studio_credits', 0)}** 💰", inline=True)
        embed.add_field(name="Seller Rating", value=f"⭐ {user.get('seller_rating', 5.0)}/5", inline=True)
        embed.add_field(name="Can Sell", value="✅ Yes" if user.get('can_sell', True) else "❌ No", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_listings(self, interaction: discord.Interaction):
        """Show listings with current filters"""
        if not interaction.response.is_done():
            await interaction.response.defer()

        result = await MarketplaceData.get_listings(
            category=self.category,
            search=self.search_query,
            sort_by=self.sort_by,
            page=self.current_page,
            per_page=5
        )

        listings = result['listings']
        total = result['total']
        page = result['page']
        total_pages = result['total_pages']

        if page < 1:
            page = 1
        if total_pages < 1:
            total_pages = 1
        self.current_page = page

        category_text = self.category.upper() if self.category else "ALL"
        search_text = f" | Search: '{self.search_query}'" if self.search_query else ""

        embed = discord.Embed(
            title=f"🛍️ Marketplace - {category_text}{search_text}",
            description=f"**{total}** listings found | Page **{page}/{total_pages}**\n\nUse `/buy <ID>` to purchase!",
            color=BOT_COLOR
        )

        if not listings:
            embed.add_field(
                name="No listings found",
                value="Try a different category or search term.\nOr be the first to sell with `/sell`!",
                inline=False
            )
        else:
            for listing in listings:
                cat_emoji = CATEGORY_EMOJIS.get(listing.get('category', 'code'), '📝')
                rating = listing.get('rating', 0)
                stars = "⭐" * int(rating) + "☆" * (5 - int(rating)) if rating > 0 else "No ratings"
                lid = listing.get('listing_id', listing.get('_id', 'N/A'))

                embed.add_field(
                    name=f"{cat_emoji} {listing.get('title', 'Untitled')} | ID: `{lid}`",
                    value=f"💰 **{listing.get('price', 0)}** Credits | {stars}\n"
                          f"📊 Sold: {listing.get('sold', 0)} | By: <@{listing.get('seller_id', 0)}>",
                    inline=False
                )

        embed.set_footer(text=f"Sort: {self.sort_by} | Use buttons to navigate")
        await interaction.edit_original_response(embed=embed, view=self)


# ==================== SEARCH MODAL ====================
class SearchModal(discord.ui.Modal):
    def __init__(self, shop_view: ShopView):
        super().__init__(title="🔍 Search Marketplace")
        self.shop_view = shop_view

        self.search_input = discord.ui.TextInput(
            label="Search Term",
            placeholder="Enter title or description to search...",
            required=True,
            max_length=100
        )
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.shop_view.search_query = self.search_input.value
        self.shop_view.current_page = 1
        await self.shop_view.show_listings(interaction)


# ==================== SORT SELECT ====================
class SortSelectView(discord.ui.View):
    def __init__(self, shop_view: ShopView):
        super().__init__(timeout=30)
        self.shop_view = shop_view

    @discord.ui.select(
        placeholder="Select sort order...",
        options=[
            discord.SelectOption(label="Newest First", value="newest", emoji="🆕"),
            discord.SelectOption(label="Oldest First", value="oldest", emoji="📅"),
            discord.SelectOption(label="Price: Low to High", value="price_low", emoji="💰"),
            discord.SelectOption(label="Price: High to Low", value="price_high", emoji="💎"),
            discord.SelectOption(label="Best Rating", value="rating", emoji="⭐"),
            discord.SelectOption(label="Best Selling", value="best_selling", emoji="🔥"),
        ]
    )
    async def sort_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.shop_view.sort_by = select.values[0]
        self.shop_view.current_page = 1
        await self.shop_view.show_listings(interaction)


# ==================== SELL VIEW ====================
class SellView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="Sell Code", emoji="📝", style=discord.ButtonStyle.blurple)
    async def sell_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your sell menu!", ephemeral=True)
            return
        can_sell, reason = await MarketplaceData.can_user_sell(self.user_id)
        if not can_sell:
            embed = discord.Embed(title="❌ Cannot Sell", description=reason, color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        modal = SellCodeModal(self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Sell Build", emoji="🏗️", style=discord.ButtonStyle.success)
    async def sell_build(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your sell menu!", ephemeral=True)
            return
        can_sell, reason = await MarketplaceData.can_user_sell(self.user_id)
        if not can_sell:
            embed = discord.Embed(title="❌ Cannot Sell", description=reason, color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="🏗️ Sell Build",
            description="To sell a build:\n\n"
                        "1. Click the button below\n"
                        "2. Fill in the details\n"
                        "3. **Upload your .rbxm or .rbxmx file** in the next message\n\n"
                        "⚠️ File must be under 8MB",
            color=BOT_COLOR
        )
        view = SellFileView(self.user_id, "build")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Sell UI", emoji="🎨", style=discord.ButtonStyle.secondary)
    async def sell_ui(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your sell menu!", ephemeral=True)
            return
        can_sell, reason = await MarketplaceData.can_user_sell(self.user_id)
        if not can_sell:
            embed = discord.Embed(title="❌ Cannot Sell", description=reason, color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="🎨 Sell UI",
            description="To sell a UI:\n\n"
                        "1. Click the button below\n"
                        "2. Fill in the details\n"
                        "3. **Upload your .rbxm or .rbxmx file** in the next message\n\n"
                        "⚠️ File must be under 8MB",
            color=BOT_COLOR
        )
        view = SellFileView(self.user_id, "ui")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="My Listings", emoji="📋", style=discord.ButtonStyle.secondary)
    async def my_listings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your sell menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        listings = await MarketplaceData.get_user_listings(self.user_id)

        if not listings:
            embed = discord.Embed(
                title="📋 My Listings",
                description="You don't have any listings yet!",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 My Listings",
            description=f"You have **{len(listings)}** listing(s)",
            color=BOT_COLOR
        )

        for listing in listings[:10]:
            cat_emoji = CATEGORY_EMOJIS.get(listing.get('category', 'code'), '📝')
            status = "🟢 Active" if listing.get('status') == 'active' else "🔴 Inactive"
            lid = listing.get('listing_id', listing.get('_id', 'N/A'))

            embed.add_field(
                name=f"{cat_emoji} {listing.get('title')} | `{lid}`",
                value=f"💰 {listing.get('price')} | Sold: {listing.get('sold', 0)} | {status}",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)


# ==================== SELL CODE MODAL ====================
class SellCodeModal(discord.ui.Modal):
    def __init__(self, user_id: int):
        super().__init__(title="📝 Sell Code")
        self.user_id = user_id

        self.title_input = discord.ui.TextInput(
            label="Title",
            placeholder="e.g., Combat System v2.0",
            required=True,
            max_length=100
        )
        self.description_input = discord.ui.TextInput(
            label="Description",
            placeholder="What does your code do?",
            required=True,
            style=discord.TextStyle.long,
            max_length=500
        )
        self.code_input = discord.ui.TextInput(
            label="Code (Lua/Luau)",
            placeholder="Paste your code here...",
            required=True,
            style=discord.TextStyle.long,
            max_length=2000
        )
        self.price_input = discord.ui.TextInput(
            label="Price (Credits)",
            placeholder="e.g., 500",
            required=True,
            max_length=10
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.code_input)
        self.add_item(self.price_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            price = int(self.price_input.value)
            if price <= 0:
                raise ValueError("Price must be positive")

            listing_id = str(uuid.uuid4())[:8].upper()

            listing = {
                "listing_id": listing_id,
                "seller_id": self.user_id,
                "seller_name": interaction.user.name,
                "title": self.title_input.value,
                "description": self.description_input.value,
                "code": self.code_input.value,
                "price": price,
                "category": "code",
                "status": "active",
                "sold": 0,
                "rating": 0,
                "ratings_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }

            await MarketplaceData.create_listing(listing)

            # Update seller sales_count for quest tracking
            user = await UserProfile.get_user(self.user_id)
            if user:
                await UserProfile.update_user(self.user_id, {
                    "sales_count": user.get('sales_count', 0) + 1
                })

            embed = discord.Embed(
                title="✅ Listing Created!",
                description="Your code is now for sale!",
                color=discord.Color.green()
            )
            embed.add_field(name="Title", value=self.title_input.value, inline=True)
            embed.add_field(name="Price", value=f"💰 {price}", inline=True)
            embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Price",
                description="Price must be a positive number!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


# ==================== SELL FILE VIEW ====================
class SellFileView(discord.ui.View):
    def __init__(self, user_id: int, category: str):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.category = category

    @discord.ui.button(label="Enter Details", emoji="📝", style=discord.ButtonStyle.blurple)
    async def enter_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your sell menu!", ephemeral=True)
            return
        modal = SellFileModal(self.user_id, self.category)
        await interaction.response.send_modal(modal)


class SellFileModal(discord.ui.Modal):
    def __init__(self, user_id: int, category: str):
        super().__init__(title=f"{'🏗️' if category == 'build' else '🎨'} Sell {category.title()}")
        self.user_id = user_id
        self.category = category

        self.title_input = discord.ui.TextInput(
            label="Title",
            placeholder=f"e.g., {'Medieval Castle' if category == 'build' else 'Modern UI Kit'}",
            required=True,
            max_length=100
        )
        self.description_input = discord.ui.TextInput(
            label="Description",
            placeholder=f"Describe your {category}...",
            required=True,
            style=discord.TextStyle.long,
            max_length=500
        )
        self.price_input = discord.ui.TextInput(
            label="Price (Credits)",
            placeholder="e.g., 1000",
            required=True,
            max_length=10
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.price_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            price = int(self.price_input.value)
            if price <= 0:
                raise ValueError("Price must be positive")

            embed = discord.Embed(
                title=f"📁 Upload Your {self.category.title()} File",
                description=f"**Title:** {self.title_input.value}\n"
                            f"**Price:** 💰 {price} Credits\n\n"
                            f"Now please **send your .rbxm or .rbxmx file** in this channel.\n\n"
                            f"⚠️ You have 60 seconds to upload!",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            def check(m):
                return (m.author.id == self.user_id and
                        m.attachments and
                        m.attachments[0].filename.endswith(('.rbxm', '.rbxmx', '.lua', '.txt')))

            try:
                msg = await interaction.client.wait_for('message', timeout=60.0, check=check)

                attachment = msg.attachments[0]

                if attachment.size > 8 * 1024 * 1024:
                    await msg.reply("❌ File too large! Maximum 8MB.", delete_after=10)
                    return

                file_name = f"{self.user_id}_{int(datetime.utcnow().timestamp())}_{attachment.filename}"
                file_path = os.path.join(UPLOADS_DIR, file_name)
                await attachment.save(file_path)

                listing_id = str(uuid.uuid4())[:8].upper()

                listing = {
                    "listing_id": listing_id,
                    "seller_id": self.user_id,
                    "seller_name": interaction.user.name,
                    "title": self.title_input.value,
                    "description": self.description_input.value,
                    "price": price,
                    "category": self.category,
                    "file_path": file_path,
                    "file_name": attachment.filename,
                    "status": "active",
                    "sold": 0,
                    "rating": 0,
                    "ratings_count": 0,
                    "created_at": datetime.utcnow().isoformat()
                }

                await MarketplaceData.create_listing(listing)

                # Update sales_count for quest tracking
                user = await UserProfile.get_user(self.user_id)
                if user:
                    await UserProfile.update_user(self.user_id, {
                        "sales_count": user.get('sales_count', 0) + 1
                    })

                try:
                    await msg.delete()
                except Exception:
                    pass

                embed = discord.Embed(
                    title="✅ Listing Created!",
                    description=f"Your {self.category} is now for sale!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Title", value=self.title_input.value, inline=True)
                embed.add_field(name="Price", value=f"💰 {price}", inline=True)
                embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)
                embed.add_field(name="File", value=f"📁 {attachment.filename}", inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)

            except TimeoutError:
                embed = discord.Embed(
                    title="❌ Timeout",
                    description="You didn't upload a file in time. Please try again.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Price",
                description="Price must be a positive number!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


# ==================== RATE SELLER VIEW ====================
class RateSellerView(discord.ui.View):
    def __init__(self, listing_id: str, seller_id: int, buyer_id: int):
        super().__init__(timeout=300)
        self.listing_id = listing_id
        self.seller_id = seller_id
        self.buyer_id = buyer_id

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.secondary)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 1)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.secondary)
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 2)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 3)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.blurple)
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.success)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 5)

    async def submit_rating(self, interaction: discord.Interaction, rating: int):
        if interaction.user.id != self.buyer_id:
            await interaction.response.send_message("Only the buyer can rate!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await MarketplaceData.add_rating(self.listing_id, self.seller_id, rating)

        # Track reviews_given for quest
        user = await UserProfile.get_user(self.buyer_id)
        if user:
            await UserProfile.update_user(self.buyer_id, {
                "reviews_given": user.get('reviews_given', 0) + 1
            })

        embed = discord.Embed(
            title="⭐ Thanks for Rating!",
            description=f"You gave a {rating}-star rating.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        self.stop()


# ==================== SHOP COG ====================
class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse the marketplace")
    async def shop_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)

        view = ShopView(interaction.user.id)

        embed = discord.Embed(
            title="🛍️ Marketplace",
            description="Browse and buy assets from other developers!\n\n"
                        "Use the category buttons to filter, or search for something specific.",
            color=BOT_COLOR
        )
        embed.add_field(name="📝 Code", value="Scripts, modules, systems", inline=True)
        embed.add_field(name="🏗️ Builds", value="Maps, models, environments", inline=True)
        embed.add_field(name="🎨 UIs", value="GUIs, menus, HUDs", inline=True)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="sell", description="Sell your asset on the marketplace")
    async def sell_cmd(self, interaction: discord.Interaction):
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)

        view = SellView(interaction.user.id)
        embed = discord.Embed(
            title="💰 Sell on Marketplace",
            description="Choose what you want to sell today!\n\n"
                        "📝 **Code:** Paste Lua/Luau code snippet\n"
                        "🏗️ **Builds:** Upload .rbxm/.rbxmx model file\n"
                        "🎨 **UIs:** Upload .rbxm/.rbxmx UI model",
            color=BOT_COLOR
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="buy", description="Buy a listing by ID")
    @app_commands.describe(listing_id="The listing ID to purchase")
    async def buy_cmd(self, interaction: discord.Interaction, listing_id: str):
        await interaction.response.defer(ephemeral=True)

        listing_id = listing_id.strip().upper()

        listing = await MarketplaceData.get_listing_by_id(listing_id)
        if not listing:
            embed = discord.Embed(
                title="❌ Not Found",
                description=f"No listing found with ID `{listing_id}`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if listing.get('status') != 'active':
            embed = discord.Embed(
                title="❌ Unavailable",
                description="This listing is no longer available.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        seller_id = listing.get('seller_id')
        price = listing.get('price', 0)

        if seller_id == interaction.user.id:
            embed = discord.Embed(
                title="❌ Error",
                description="You can't buy your own listing!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        buyer = await UserProfile.get_user(interaction.user.id)
        if not buyer:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            buyer = await UserProfile.get_user(interaction.user.id)

        buyer_credits = buyer.get('studio_credits', 0)
        if buyer_credits < price:
            embed = discord.Embed(
                title="❌ Insufficient Credits",
                description=f"You need **{price}** credits but only have **{buyer_credits}**.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Deduct from buyer
        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": buyer_credits - price,
            "purchases_count": buyer.get('purchases_count', 0) + 1
        })

        # Add to seller
        seller = await UserProfile.get_user(seller_id)
        if seller:
            await UserProfile.update_user(seller_id, {
                "studio_credits": seller.get('studio_credits', 0) + price
            })

        # Update listing sold count
        await MarketplaceData.increment_sold(listing_id)

        # Record transaction
        transaction = {
            "transaction_id": str(uuid.uuid4())[:8].upper(),
            "listing_id": listing_id,
            "buyer_id": interaction.user.id,
            "seller_id": seller_id,
            "price": price,
            "title": listing.get('title', 'Unknown'),
            "category": listing.get('category', 'code'),
            "timestamp": datetime.utcnow().isoformat()
        }
        await TransactionData.create_transaction(transaction)

        cat_emoji = CATEGORY_EMOJIS.get(listing.get('category', 'code'), '📝')

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{listing.get('title')}** for **{price}** credits!",
            color=discord.Color.green()
        )
        embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)
        embed.add_field(name="Category", value=f"{cat_emoji} {listing.get('category', 'code').title()}", inline=True)
        embed.add_field(name="Remaining Balance", value=f"💰 {buyer_credits - price}", inline=True)

        if listing.get('category') == 'code' and listing.get('code'):
            code_text = listing['code']
            if len(code_text) > 1900:
                code_text = code_text[:1900] + "\n-- ... truncated"
            embed.add_field(
                name="📝 Your Code",
                value=f"```lua\n{code_text}\n```",
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

        # Send file via DM if file listing
        if listing.get('file_path') and os.path.exists(listing['file_path']):
            try:
                dm_embed = discord.Embed(
                    title=f"📁 Your Purchase: {listing.get('title')}",
                    description="Here is the file you purchased!",
                    color=discord.Color.green()
                )
                file = discord.File(listing['file_path'], filename=listing.get('file_name', 'file.rbxm'))
                await interaction.user.send(embed=dm_embed, file=file)
            except discord.Forbidden:
                await interaction.followup.send(
                    "⚠️ I couldn't DM you the file. Please enable DMs from server members!",
                    ephemeral=True
                )

        # Rating prompt
        rate_view = RateSellerView(listing_id, seller_id, interaction.user.id)
        rate_embed = discord.Embed(
            title="⭐ Rate the Seller",
            description=f"How would you rate this purchase from <@{seller_id}>?",
            color=BOT_COLOR
        )
        await interaction.followup.send(embed=rate_embed, view=rate_view, ephemeral=True)

    @app_commands.command(name="myid", description="View your unique Player ID")
    async def myid_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        player_id = user.get('player_id')
        if not player_id or player_id == 'N/A':
            player_id = f"DEV-{str(interaction.user.id)[-6:]}-{str(uuid.uuid4())[:4].upper()}"
            await UserProfile.update_user(interaction.user.id, {"player_id": player_id})

        embed = discord.Embed(
            title="🆔 Your Player ID",
            description=f"```{player_id}```",
            color=BOT_COLOR
        )
        embed.add_field(name="Username", value=interaction.user.name, inline=True)
        embed.add_field(name="Level", value=str(user.get('level', 1)), inline=True)
        embed.add_field(name="Rank", value=user.get('rank', 'Beginner'), inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ShopCog(bot))