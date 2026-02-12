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
            discord.SelectOption(label=item['name'], value=key, description=f"{item['price']} pCredits - {item['description']}")
            for key, item in PCREDIT_SHOP.items()
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        item_key = select.values[0]
        item = PCREDIT_SHOP[item_key]

        user = await UserProfile.get_user(self.user_id)
        if user.get('pcredits', 0) < item['price']:
            await interaction.response.send_message(f"Not enough pCredits. You need {item['price']}.", ephemeral=True)
            return

        updates = {"pcredits": user['pcredits'] - item['price']}
        if item_key == "team_slot":
            updates["max_teams"] = user.get("max_teams", 1) + 1
        elif item_key == "project_slots":
            updates["max_projects"] = user.get("max_projects", 2) + 5

        await UserProfile.update_user(self.user_id, updates)
        await interaction.response.send_message(f"Purchased **{item['name']}**.", ephemeral=True)


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None
        self.session = None
        self.agent = AgentMode(genai_client, AI_MODEL, AI_PERSONALITY)

    async def get_ai_response(self, message):
        context = await ai_handler.get_context(message.channel, before=message, user_id=message.author.id)

        mode_info = "You are in NORMAL CHAT MODE. You are NOT in agent mode. Just respond naturally to the user's message like a normal chat assistant. Do NOT create task plans or do deep analysis. Just answer directly."

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

    @app_commands.command(name="convert", description="Convert 1000 credits to 1 pCredit")
    async def convert(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount <= 0:
            await interaction.followup.send("Please enter a valid amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        total_cost = amount * CREDIT_TO_PCREDIT_RATE

        if user.get('studio_credits', 0) < total_cost:
            await interaction.followup.send(f"Not enough credits. You need {total_cost} credits for {amount} pCredits.", ephemeral=True)
            return

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": user['studio_credits'] - total_cost,
            "pcredits": user.get('pcredits', 0) + amount
        })

        await interaction.followup.send(f"Converted {total_cost} Credits to **{amount} pCredit(s)**.", ephemeral=True)

    @app_commands.command(name="convert_ai", description="Convert 1 pCredit to 10 AI credits")
    async def convert_ai(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if user.get('pcredits', 0) < amount:
            await interaction.followup.send("Not enough pCredits.", ephemeral=True)
            return

        await UserProfile.update_user(interaction.user.id, {
            "pcredits": user['pcredits'] - amount,
            "ai_credits": user.get('ai_credits', 0) + (amount * PCREDIT_TO_AICREDIT_RATE)
        })
        await interaction.followup.send(f"Converted {amount} pCredit(s) to **{amount * PCREDIT_TO_AICREDIT_RATE} AI Credits**.", ephemeral=True)

    @app_commands.command(name="pshop", description="Open the pCredit Shop")
    async def pshop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        embed = discord.Embed(title="Premium Shop", color=discord.Color.gold())
        embed.add_field(name="Balance", value=f"{user.get('pcredits', 0)} pCredits", inline=False)

        for key, item in PCREDIT_SHOP.items():
            embed.add_field(name=item['name'], value=f"{item['price']} pCredits\n{item['description']}", inline=True)

        await interaction.followup.send(embed=embed, view=PremiumShopView(interaction.user.id), ephemeral=True)

    @app_commands.command(name="setup_ai", description="[Admin] Set up the AI channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        self.ai_channel_id = channel.id
        await interaction.followup.send(f"AI channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="temp_chat_ai", description="Create a temporary AI chat channel")
    async def temp_chat(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        last_used = user.get('temp_chat_cooldown')
        if last_used:
            cooldown_time = datetime.fromisoformat(last_used)
            if datetime.utcnow() < cooldown_time + timedelta(hours=AI_CHAT_COOLDOWN_HOURS):
                await interaction.followup.send("Cooldown active. You can use this once every 4 hours.", ephemeral=True)
                return

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, create_public_threads=True, manage_threads=True)
        }

        channel = await guild.create_text_channel(name=f"ai-chat-{interaction.user.name}", overwrites=overwrites)
        await UserProfile.update_user(interaction.user.id, {"temp_chat_cooldown": datetime.utcnow().isoformat()})

        await interaction.followup.send(f"Channel created: {channel.mention}. Expires in 1 hour.", ephemeral=True)

        # Clean welcome message
        welcome_embed = discord.Embed(
            title=f"{AI_NAME}",
            description=(
                f"Welcome, {interaction.user.mention}. This channel expires in 1 hour.\n\n"
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
        welcome_embed.set_footer(text="Normal chat costs 1 credit per message. Admins bypass all costs.")
        await channel.send(embed=welcome_embed)

        await asyncio.sleep(AI_CHAT_DURATION_MINUTES * 60)
        try:
            await channel.delete(reason="Temporary AI chat expired")
        except:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_temp_chat = hasattr(message.channel, 'name') and message.channel.name.startswith("ai-chat-")
        if not is_temp_chat and (not self.ai_channel_id or message.channel.id != self.ai_channel_id):
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
            if not is_temp_chat and not is_admin:
                if user.get('ai_credits', 0) < 5:
                    await message.reply(f"Super Agent requires 5 AI Credits per message. You have {user.get('ai_credits', 0)}.")
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=True)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="Super Agent — Online",
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
            if not is_temp_chat and not is_admin:
                if user.get('ai_credits', 0) < 3:
                    await message.reply(f"Agent mode requires 3 AI Credits per message. You have {user.get('ai_credits', 0)}.")
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=False)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="Agent Mode — Online",
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
                await message.reply(
                    f"**{mode_name} — Disconnected**\n\n"
                    f"Back to normal chat. Your projects are saved.\n"
                    f"Use `change to agent mode` or `change to super agent` anytime."
                )
            else:
                await message.reply("You're not in agent mode.")
            return

        # ========== MODE SWITCHES ==========
        elif content_lower in ("upgrade to super", "switch to super agent"):
            if self.agent.is_agent_mode(message.author.id) and not self.agent.is_super_agent(message.author.id):
                self.agent.sessions[message.author.id]["super"] = True
                await message.reply("Upgraded to **Super Agent**. Full pipeline active. Cost: 5 credits/msg.")
                return

        elif content_lower in ("downgrade to agent", "switch to agent"):
            if self.agent.is_agent_mode(message.author.id) and self.agent.is_super_agent(message.author.id):
                self.agent.sessions[message.author.id]["super"] = False
                await message.reply("Switched to **Normal Agent**. Cost: 3 credits/msg.")
                return

        # ========== HANDLE AGENT MODE MESSAGES ==========
        if self.agent.is_agent_mode(message.author.id):
            is_super = self.agent.is_super_agent(message.author.id)
            credit_cost = 5 if is_super else 3

            if not is_temp_chat and not is_admin:
                if user.get('ai_credits', 0) < credit_cost:
                    mode_name = "Super Agent" if is_super else "Agent"
                    await message.reply(
                        f"{mode_name} costs {credit_cost} AI Credits per message. "
                        f"You have {user.get('ai_credits', 0)}.\n"
                        f"Type `exit agent mode` to switch to normal chat."
                    )
                    return

                original_credits = user['ai_credits']
                await UserProfile.update_user(message.author.id, {"ai_credits": original_credits - credit_cost})

            try:
                async with message.channel.typing():
                    await self.agent.handle_message(message)
            except Exception as e:
                # Refund on failure
                if not is_temp_chat and not is_admin:
                    await UserProfile.update_user(message.author.id, {"ai_credits": original_credits})
                    await message.reply(f"An error occurred. Your {credit_cost} credits have been refunded.")
                else:
                    await message.reply(f"An error occurred: {str(e)[:200]}")
                print(f"[Agent Error] {e}")
            return

        # ========== NORMAL AI CHAT ==========
        if not is_temp_chat and not is_admin:
            if user.get('ai_credits', 0) <= 0:
                await message.reply(
                    f"You don't have enough AI Credits to chat with {AI_NAME}.\n\n"
                    f"**Get credits:**\n"
                    f"`/convert` — Studio Credits to pCredits\n"
                    f"`/convert_ai` — pCredits to AI Credits"
                )
                return
            await UserProfile.update_user(message.author.id, {"ai_credits": user['ai_credits'] - 1})

        async with message.channel.typing():
            response = await self.get_ai_response(message)
            await ai_handler.send_response(
                message=message,
                ai_text=response,
                user_name=message.author.display_name
            )


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))