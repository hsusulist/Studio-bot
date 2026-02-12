import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile, db
from config import (
    BOT_COLOR, CREDIT_TO_PCREDIT_RATE, PCREDIT_TO_AICREDIT_RATE,
    PCREDIT_SHOP, AI_NAME, AI_CHAT_COOLDOWN_HOURS, AI_CHAT_DURATION_MINUTES,
    AI_MODEL, AI_PERSONALITY
)
from datetime import datetime, timedelta
import asyncio
import os
from google import genai

from ai_tools import ai_handler
from agent_core import AgentMode

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

genai_client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL
    }
)


class PremiumShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Select an item to buy",
        options=[
            discord.SelectOption(
                label=item['name'],
                value=key,
                description=f"{item['price']} pCredits - {item['description']}"
            )
            for key, item in PCREDIT_SHOP.items()
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return

        item_key = select.values[0]
        item = PCREDIT_SHOP[item_key]

        user = await UserProfile.get_user(self.user_id)
        if not user:
            await interaction.response.send_message("Profile not found. Use `/start` first.", ephemeral=True)
            return

        current_pcredits = user.get('pcredits', 0)
        if current_pcredits < item['price']:
            await interaction.response.send_message(
                f"Not enough pCredits. You need **{item['price']}** but have **{current_pcredits}**.",
                ephemeral=True
            )
            return

        updates = {"pcredits": current_pcredits - item['price']}
        if item_key == "team_slot":
            updates["max_teams"] = user.get("max_teams", 1) + 1
        elif item_key == "project_slots":
            updates["max_projects"] = user.get("max_projects", 2) + 5

        await UserProfile.update_user(self.user_id, updates)
        await interaction.response.send_message(
            f"✅ Purchased **{item['name']}** for **{item['price']}** pCredits!",
            ephemeral=True
        )


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None
        self.session = None
        self.agent = AgentMode(genai_client, AI_MODEL, AI_PERSONALITY)

    async def get_ai_response(self, message):
        context = await ai_handler.get_context(message.channel, before=message, user_id=message.author.id)

        mode_info = (
            "You are in NORMAL CHAT MODE. You are NOT in agent mode. "
            "Just respond naturally to the user's message like a normal chat assistant. "
            "Do NOT create task plans or do deep analysis. Just answer directly."
        )

        system_prompt = f"You are {AI_NAME}. {AI_PERSONALITY}\n\nCURRENT MODE: {mode_info}"
        full_prompt = (
            f"System: {system_prompt}\n\n"
            f"=== RECENT CONVERSATION ===\n"
            f"{context}\n\n"
            f"=== CURRENT MESSAGE ===\n"
            f"{message.author.display_name}: {message.content}\n\n"
            f"Respond to the current message. You are in normal chat mode — just answer directly."
        )

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: genai_client.models.generate_content(
                    model=AI_MODEL,
                    contents=full_prompt
                )
            )
            return response.text or "No response generated."
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"AI Error: {str(e)}"

    @app_commands.command(name="convert", description="Convert Studio Credits to pCredits")
    @app_commands.describe(amount="Number of pCredits to buy (each costs configured rate in credits)")
    async def convert(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount <= 0:
            await interaction.followup.send("❌ Please enter a positive amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        total_cost = amount * CREDIT_TO_PCREDIT_RATE
        current_credits = user.get('studio_credits', 0)
        current_pcredits = user.get('pcredits', 0)

        if current_credits < total_cost:
            embed = discord.Embed(
                title="❌ Not Enough Credits",
                description=(
                    f"You need **{total_cost}** Studio Credits for **{amount}** pCredit(s).\n"
                    f"You currently have **{current_credits}** Studio Credits.\n"
                    f"You're short by **{total_cost - current_credits}** credits."
                ),
                color=discord.Color.red()
            )
            embed.add_field(
                name="Rate",
                value=f"1 pCredit = {CREDIT_TO_PCREDIT_RATE} Studio Credits",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Do the conversion
        new_credits = current_credits - total_cost
        new_pcredits = current_pcredits + amount

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": new_credits,
            "pcredits": new_pcredits
        })

        embed = discord.Embed(
            title="✅ Conversion Successful!",
            description=f"Converted **{total_cost}** Studio Credits → **{amount}** pCredit(s)",
            color=discord.Color.green()
        )
        embed.add_field(name="Studio Credits", value=f"💰 {current_credits} → {new_credits}", inline=True)
        embed.add_field(name="pCredits", value=f"💎 {current_pcredits} → {new_pcredits}", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="convert_ai", description="Convert pCredits to AI Credits")
    @app_commands.describe(amount="Number of pCredits to convert (each gives configured rate in AI credits)")
    async def convert_ai(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount <= 0:
            await interaction.followup.send("❌ Please enter a positive amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_pcredits = user.get('pcredits', 0)
        current_ai = user.get('ai_credits', 0)
        ai_gained = amount * PCREDIT_TO_AICREDIT_RATE

        if current_pcredits < amount:
            embed = discord.Embed(
                title="❌ Not Enough pCredits",
                description=(
                    f"You need **{amount}** pCredit(s) but only have **{current_pcredits}**.\n"
                    f"You're short by **{amount - current_pcredits}** pCredits.\n\n"
                    f"Use `/convert` to get more pCredits from Studio Credits."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Do the conversion
        new_pcredits = current_pcredits - amount
        new_ai = current_ai + ai_gained

        await UserProfile.update_user(interaction.user.id, {
            "pcredits": new_pcredits,
            "ai_credits": new_ai
        })

        embed = discord.Embed(
            title="✅ Conversion Successful!",
            description=f"Converted **{amount}** pCredit(s) → **{ai_gained}** AI Credits",
            color=discord.Color.green()
        )
        embed.add_field(name="pCredits", value=f"💎 {current_pcredits} → {new_pcredits}", inline=True)
        embed.add_field(name="AI Credits", value=f"🤖 {current_ai} → {new_ai}", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="pshop", description="Open the pCredit Shop")
    async def pshop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        embed = discord.Embed(title="💎 Premium Shop", color=discord.Color.gold())
        embed.add_field(
            name="Your Balance",
            value=f"💎 **{user.get('pcredits', 0)}** pCredits",
            inline=False
        )

        for key, item in PCREDIT_SHOP.items():
            embed.add_field(
                name=f"{item['name']} — {item['price']} pCredits",
                value=item['description'],
                inline=True
            )

        await interaction.followup.send(
            embed=embed,
            view=PremiumShopView(interaction.user.id),
            ephemeral=True
        )

    @app_commands.command(name="setup_ai", description="[Admin] Set up the AI channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        self.ai_channel_id = channel.id
        await interaction.followup.send(f"✅ AI channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="temp_chat_ai", description="Create a temporary AI chat channel")
    async def temp_chat(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        last_used = user.get('temp_chat_cooldown')
        if last_used:
            try:
                cooldown_time = datetime.fromisoformat(last_used)
                time_since = (datetime.utcnow() - cooldown_time).total_seconds()
                cooldown_seconds = AI_CHAT_COOLDOWN_HOURS * 3600

                if time_since < cooldown_seconds:
                    remaining = cooldown_seconds - time_since
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)

                    embed = discord.Embed(
                        title="⏰ Cooldown Active",
                        description=f"You can use this again in **{hours}h {minutes}m**.",
                        color=discord.Color.orange()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            except Exception:
                pass

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                create_public_threads=True,
                manage_threads=True
            )
        }

        channel = await guild.create_text_channel(
            name=f"ai-chat-{interaction.user.name}",
            overwrites=overwrites
        )
        await UserProfile.update_user(interaction.user.id, {
            "temp_chat_cooldown": datetime.utcnow().isoformat()
        })

        await interaction.followup.send(
            f"✅ Channel created: {channel.mention}. Expires in {AI_CHAT_DURATION_MINUTES} minutes.",
            ephemeral=True
        )

        welcome_embed = discord.Embed(
            title=f"🤖 {AI_NAME}",
            description=(
                f"Welcome, {interaction.user.mention}. This channel expires in "
                f"{AI_CHAT_DURATION_MINUTES} minutes.\n\n"
                f"**Modes**\n"
                f"`change to agent mode` — Task planning + code generation (3 credits/msg)\n"
                f"`change to super agent` — Full pipeline with reviews + optimization (5 credits/msg)\n"
                f"Or just type normally to chat.\n\n"
                f"**Agent Commands**\n"
                f"`creative mode on/off` · `present task on/off`\n"
                f"`templates` · `review code` · `my projects` · `load project last`\n"
                f"`exit agent mode` — Return to normal chat"
            ),
            color=0x5865F2
        )
        welcome_embed.set_footer(
            text="Normal chat costs 1 credit per message. Admins bypass all costs."
        )
        await channel.send(embed=welcome_embed)

        await asyncio.sleep(AI_CHAT_DURATION_MINUTES * 60)
        try:
            await channel.delete(reason="Temporary AI chat expired")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_temp_chat = (
            hasattr(message.channel, 'name')
            and message.channel.name.startswith("ai-chat-")
        )

        if not is_temp_chat and (
            not self.ai_channel_id or message.channel.id != self.ai_channel_id
        ):
            return

        if message.content.startswith(("!", "/")):
            return

        if len(message.content.strip()) < 2:
            return

        user = await UserProfile.get_user(message.author.id)
        if not user:
            await UserProfile.create_user(message.author.id, message.author.name)
            user = await UserProfile.get_user(message.author.id)

        # Safe admin check
        is_admin = False
        if message.guild and hasattr(message.author, 'guild_permissions'):
            is_admin = message.author.guild_permissions.administrator

        content_lower = message.content.strip().lower()

        # ========== SUPER AGENT ACTIVATION ==========
        if content_lower == "change to super agent":
            if not is_admin:
                current_ai = user.get('ai_credits', 0)
                if current_ai < 5:
                    await message.reply(
                        f"Super Agent requires **5 AI Credits** per message. "
                        f"You have **{current_ai}**.\n"
                        f"Use `/convert_ai` to get more."
                    )
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=True)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="⚡ Super Agent — Online",
                description=(
                    "Full development pipeline activated.\n\n"
                    "**Pipeline**\n"
                    "Build code > Self-review > Optimize > Verify alignment > Final review\n\n"
                    "**Post-processing**\n"
                    "Cross-file connector · Exploit scanner · Setup script · Test guide\n\n"
                    "**Settings**\n"
                    "`creative mode on/off` — Toggle experimental features\n"
                    "`present task on/off` — Toggle plan approval\n\n"
                    "**Cost:** 5 AI Credits per message (admins bypassed)\n\n"
                    "Type `exit agent mode` to disconnect.\n"
                    "What are we building?"
                ),
                color=0x5865F2
            )
            await message.reply(embed=activate_embed)
            return

        # ========== NORMAL AGENT ACTIVATION ==========
        elif content_lower == "change to agent mode":
            if not is_admin:
                current_ai = user.get('ai_credits', 0)
                if current_ai < 3:
                    await message.reply(
                        f"Agent mode requires **3 AI Credits** per message. "
                        f"You have **{current_ai}**.\n"
                        f"Use `/convert_ai` to get more."
                    )
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=False)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="🤖 Agent Mode — Online",
                description=(
                    "Task planning and code generation activated.\n\n"
                    "**Pipeline**\n"
                    "Analyze request > Plan tasks > Execute > Present results\n\n"
                    "**Settings**\n"
                    "`creative mode on/off` — Toggle extra features (default: off)\n"
                    "`present task on/off` — Toggle plan approval (default: off)\n\n"
                    "**Commands**\n"
                    "`templates` · `review code` · `my projects` · `load project last`\n\n"
                    "**Upgrade:** `change to super agent` for full pipeline\n"
                    "**Cost:** 3 AI Credits per message\n\n"
                    "Type `exit agent mode` to go back.\n"
                    "What do you want to build?"
                ),
                color=0x5865F2
            )
            await message.reply(embed=activate_embed)
            return

        # ========== AGENT MODE DEACTIVATION ==========
        elif content_lower == "exit agent mode":
            if self.agent.is_agent_mode(message.author.id):
                was_super = self.agent.is_super_agent(message.author.id)
                self.agent.deactivate(message.author.id)
                mode_name = "Super Agent" if was_super else "Agent"

                deactivate_embed = discord.Embed(
                    title=f"🔌 {mode_name} — Disconnected",
                    description=(
                        "Back to normal chat. Your projects are saved.\n"
                        "Use `change to agent mode` or `change to super agent` anytime."
                    ),
                    color=0x5865F2
                )
                await message.reply(embed=deactivate_embed)
            else:
                await message.reply("You're not in agent mode.")
            return

        # ========== MODE SWITCHES ==========
        elif content_lower in ("upgrade to super", "switch to super agent"):
            if self.agent.is_agent_mode(message.author.id) and not self.agent.is_super_agent(message.author.id):
                if not is_admin:
                    current_ai = user.get('ai_credits', 0)
                    if current_ai < 5:
                        await message.reply(
                            f"Super Agent requires **5 AI Credits** per message. "
                            f"You have **{current_ai}**."
                        )
                        return
                self.agent.sessions[message.author.id]["super"] = True
                await message.reply(
                    "⚡ Upgraded to **Super Agent**. Full pipeline active. Cost: 5 credits/msg."
                )
                return

        elif content_lower in ("downgrade to agent", "switch to agent"):
            if self.agent.is_agent_mode(message.author.id) and self.agent.is_super_agent(message.author.id):
                self.agent.sessions[message.author.id]["super"] = False
                await message.reply(
                    "🤖 Switched to **Normal Agent**. Cost: 3 credits/msg."
                )
                return

        # ========== HANDLE AGENT MODE MESSAGES ==========
        if self.agent.is_agent_mode(message.author.id):
            is_super = self.agent.is_super_agent(message.author.id)
            credit_cost = 5 if is_super else 3

            # Re-fetch user to get latest balance
            user = await UserProfile.get_user(message.author.id)
            current_ai = user.get('ai_credits', 0) if user else 0

            if not is_admin:
                if current_ai < credit_cost:
                    mode_name = "Super Agent" if is_super else "Agent"
                    await message.reply(
                        f"**{mode_name}** costs **{credit_cost}** AI Credits per message. "
                        f"You have **{current_ai}**.\n"
                        f"Type `exit agent mode` to switch to normal chat (1 credit/msg).\n"
                        f"Use `/convert_ai` to get more credits."
                    )
                    return

                # Deduct credits BEFORE processing
                await UserProfile.update_user(message.author.id, {
                    "ai_credits": current_ai - credit_cost
                })

            try:
                async with message.channel.typing():
                    await self.agent.handle_message(message)
            except Exception as e:
                # Refund on failure
                if not is_admin:
                    await UserProfile.update_user(message.author.id, {
                        "ai_credits": current_ai
                    })
                    await message.reply(
                        f"❌ An error occurred. Your **{credit_cost}** credits have been refunded."
                    )
                else:
                    await message.reply(f"❌ An error occurred: {str(e)[:200]}")
                print(f"[Agent Error] {e}")
            return

        # ========== NORMAL AI CHAT ==========
        # Re-fetch user to get latest balance
        user = await UserProfile.get_user(message.author.id)
        current_ai = user.get('ai_credits', 0) if user else 0

        if not is_admin:
            if current_ai <= 0:
                await message.reply(
                    f"You don't have enough AI Credits to chat with {AI_NAME}.\n\n"
                    f"**Get credits:**\n"
                    f"`/convert` — Studio Credits → pCredits\n"
                    f"`/convert_ai` — pCredits → AI Credits"
                )
                return

            # Deduct 1 credit
            await UserProfile.update_user(message.author.id, {
                "ai_credits": current_ai - 1
            })

        try:
            async with message.channel.typing():
                response = await self.get_ai_response(message)
                await ai_handler.send_response(
                    message=message,
                    ai_text=response,
                    user_name=message.author.display_name
                )
        except Exception as e:
            # Refund on failure
            if not is_admin:
                await UserProfile.update_user(message.author.id, {
                    "ai_credits": current_ai
                })
            await message.reply(f"❌ AI Error: {str(e)[:200]}")
            print(f"[AI Chat Error] {e}")


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))