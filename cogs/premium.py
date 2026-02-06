import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile, db
from config import (
    BOT_COLOR, CREDIT_TO_PCREDIT_RATE, PCREDIT_TO_AICREDIT_RATE, 
    PCREDIT_SHOP, AI_NAME, AI_CHAT_COOLDOWN_HOURS, AI_CHAT_DURATION_MINUTES,
    OPENROUTER_API_KEY, AI_MODEL, AI_PERSONALITY
)
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json

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
            await interaction.response.send_message(f"❌ You don't have enough pCredits! You need {item['price']} pCredits.", ephemeral=True)
            return

        # Handle purchase logic
        updates = {"pcredits": user['pcredits'] - item['price']}
        if item_key == "team_slot":
            updates["max_teams"] = user.get("max_teams", 1) + 1
        elif item_key == "project_slots":
            updates["max_projects"] = user.get("max_projects", 2) + 5
        # Add other logic as needed

        await UserProfile.update_user(self.user_id, updates)
        await interaction.response.send_message(f"✅ Successfully purchased **{item['name']}**!", ephemeral=True)

class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def get_ai_response(self, prompt, user_id):
        if not OPENROUTER_API_KEY:
            return "❌ AI is currently unavailable (API Key missing)."

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are {AI_NAME}. {AI_PERSONALITY}"},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            async with self.session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await resp.text()
                    print(f"AI API Error: {resp.status} - {error_text}")
                    return "❌ Sorry, I encountered an error while processing your request."
        except Exception as e:
            print(f"AI Connection Error: {e}")
            return "❌ I'm having trouble connecting to the AI service right now."

    @app_commands.command(name="convert", description="Convert 1000 credits to 1 pCredit")
    async def convert(self, interaction: discord.Interaction, amount: int = 1):
        if amount <= 0:
            await interaction.response.send_message("Please enter a valid amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        total_cost = amount * CREDIT_TO_PCREDIT_RATE
        
        if user.get('studio_credits', 0) < total_cost:
            await interaction.response.send_message(f"❌ Not enough credits! You need {total_cost} credits to get {amount} pCredits.", ephemeral=True)
            return

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": user['studio_credits'] - total_cost,
            "pcredits": user.get('pcredits', 0) + amount
        })
        
        await interaction.response.send_message(f"✅ Converted {total_cost} Credits to **{amount} pCredit(s)**!", ephemeral=True)

    @app_commands.command(name="convert_ai", description="Convert 1 pCredit to 10 AI credits")
    async def convert_ai(self, interaction: discord.Interaction, amount: int = 1):
        user = await UserProfile.get_user(interaction.user.id)
        if user.get('pcredits', 0) < amount:
            await interaction.response.send_message(f"❌ Not enough pCredits!", ephemeral=True)
            return

        await UserProfile.update_user(interaction.user.id, {
            "pcredits": user['pcredits'] - amount,
            "ai_credits": user.get('ai_credits', 0) + (amount * PCREDIT_TO_AICREDIT_RATE)
        })
        await interaction.response.send_message(f"✅ Converted {amount} pCredit(s) to **{amount * PCREDIT_TO_AICREDIT_RATE} AI Credits**!", ephemeral=True)

    @app_commands.command(name="pshop", description="Open the pCredit Shop")
    async def pshop(self, interaction: discord.Interaction):
        user = await UserProfile.get_user(interaction.user.id)
        embed = discord.Embed(title="💎 pCredit Premium Shop", color=discord.Color.gold())
        embed.add_field(name="Your Balance", value=f"💎 {user.get('pcredits', 0)} pCredits", inline=False)
        
        for key, item in PCREDIT_SHOP.items():
            embed.add_field(name=item['name'], value=f"Price: {item['price']} pCredits\n{item['description']}", inline=True)
            
        await interaction.response.send_message(embed=embed, view=PremiumShopView(interaction.user.id), ephemeral=True)

    @app_commands.command(name="setup_ai", description="[Admin] Set up the AI channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.ai_channel_id = channel.id
        await interaction.response.send_message(f"✅ AI has been set up in {channel.mention}!", ephemeral=True)

    @app_commands.command(name="temp_chat_ai", description="Create a secret 1-hour AI chat channel")
    async def temp_chat(self, interaction: discord.Interaction):
        user = await UserProfile.get_user(interaction.user.id)
        
        # Check cooldown
        last_used = user.get('temp_chat_cooldown')
        if last_used:
            cooldown_time = datetime.fromisoformat(last_used)
            if datetime.utcnow() < cooldown_time + timedelta(hours=AI_CHAT_COOLDOWN_HOURS):
                await interaction.response.send_message("❌ Cooldown! You can use this once every 4 hours.", ephemeral=True)
                return

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ai-chat-{interaction.user.name}", overwrites=overwrites)
        await UserProfile.update_user(interaction.user.id, {"temp_chat_cooldown": datetime.utcnow().isoformat()})
        
        await interaction.response.send_message(f"✅ Secret AI channel created: {channel.mention}. It will be deleted in 1 hour.", ephemeral=True)
        await channel.send(f"Welcome {interaction.user.mention}! I am {AI_NAME}. How can I help you today?")
        
        # Start a loop to listen for messages in this channel
        # Note: In a real bot, you'd handle this via the on_message listener with channel ID checks
        
        await asyncio.sleep(AI_CHAT_DURATION_MINUTES * 60)
        await channel.delete(reason="Temporary AI chat expired")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # Check if it's the public AI channel or a temp chat channel
        is_temp_chat = message.channel.name.startswith("ai-chat-")
        if not is_temp_chat and (not self.ai_channel_id or message.channel.id != self.ai_channel_id):
            return
        
        user = await UserProfile.get_user(message.author.id)
        
        # Only public channels deduct credits; temp chats are free once created
        if not is_temp_chat:
            if user.get('ai_credits', 0) <= 0:
                await message.reply(f"❌ You don't have enough AI Credits. Convert pCredits to AI Credits to chat with {AI_NAME}!")
                return
            await UserProfile.update_user(message.author.id, {"ai_credits": user['ai_credits'] - 1})
        
        async with message.channel.typing():
            response = await self.get_ai_response(message.content, message.author.id)
            await message.reply(response)

async def setup(bot):
    await bot.add_cog(PremiumCog(bot))
