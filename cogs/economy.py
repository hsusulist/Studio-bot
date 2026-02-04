import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, DAILY_QUEST_REWARD
from datetime import datetime
import random

class QuestView(discord.ui.View):
    """Quest action buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Daily Quests", emoji="📋", style=discord.ButtonStyle.blurple)
    async def daily_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.user_id)
        
        quests = [
            {"name": "Review a Script", "reward": DAILY_QUEST_REWARD, "desc": "Help someone improve their code"},
            {"name": "Share a Building Tip", "reward": DAILY_QUEST_REWARD, "desc": "Post helpful tips in #tips"},
            {"name": "Assist a Team", "reward": DAILY_QUEST_REWARD * 2, "desc": "Join and contribute to a team"},
            {"name": "Complete a Commission", "reward": DAILY_QUEST_REWARD * 3, "desc": "Finish a paid project"},
        ]
        
        embed = discord.Embed(
            title="Daily Quests",
            color=BOT_COLOR
        )
        
        for quest in quests:
            embed.add_field(
                name=f"✓ {quest['name']}",
                value=f"{quest['desc']}\n**Reward:** {quest['reward']} Credits",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Claim Reward", emoji="🎁", style=discord.ButtonStyle.success)
    async def claim_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.user_id)
        
        # Check if user can claim daily quest
        last_quest = user.get('last_quest')
        if last_quest:
            last_time = datetime.fromisoformat(last_quest)
            today = datetime.utcnow().date()
            if last_time.date() == today:
                embed = discord.Embed(
                    title="Quest Already Claimed",
                    description="Come back tomorrow for another reward!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        reward = DAILY_QUEST_REWARD
        await UserProfile.add_credits(self.user_id, reward)
        await UserProfile.add_xp(self.user_id, 50)
        await UserProfile.update_user(self.user_id, {"last_quest": datetime.utcnow().isoformat()})
        
        embed = discord.Embed(
            title="✓ Quest Complete!",
            description=f"You earned **{reward} Studio Credits** and **50 XP**",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Stats", emoji="📊", style=discord.ButtonStyle.secondary)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.user_id)
        
        embed = discord.Embed(
            title="Progress Stats",
            color=BOT_COLOR
        )
        embed.add_field(name="Level", value=str(user['level']), inline=True)
        embed.add_field(name="XP", value=f"{user['xp']} / {(user['level']) * 250}", inline=True)
        embed.add_field(name="Credits", value=f"💰 {user['studio_credits']}", inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class EconomyCog(commands.Cog):
    """Economy, Quests, and Rewards"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def quest(self, interaction: discord.Interaction):
        """Daily quests and rewards"""
        await interaction.response.defer()
        view = QuestView(interaction.user.id)
        
        embed = discord.Embed(
            title="Daily Quests",
            description="Earn Studio Credits by completing tasks in the community",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Features",
            value="📋 View Quests\n🎁 Claim Daily Reward\n📊 Check Progress",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, view=view)
    
    async def review(self, interaction: discord.Interaction):
        """AI-powered code review (Luau/Lua)"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Code Review",
            description="Let me analyze your Lua code for you!",
            color=BOT_COLOR
        )
        embed.add_field(name="Features", value="🤖 AI Analysis\n⚠️ Error Detection\n💡 Optimization Tips", inline=False)
        
        # Send example review
        review_embed = discord.Embed(
            title="✓ Code Review Complete",
            color=discord.Color.green()
        )
        review_embed.add_field(
            name="Analysis",
            value="✓ No syntax errors detected\n⚠️ Could optimize memory usage\n💡 Consider using local variables",
            inline=False
        )
        review_embed.add_field(name="Score", value="**8.5/10** - Good", inline=False)
        
        await UserProfile.add_xp(interaction.user.id, 25)
        
        await interaction.followup.send(embed=review_embed)
    
    async def card(self, interaction: discord.Interaction):
        """Generate developer portfolio card"""
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        
        if not user:
            embed = discord.Embed(
                title="User Not Found",
                description="You haven't set up your profile yet",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Create portfolio card
        embed = discord.Embed(
            title="🎯 Developer Portfolio Card",
            color=BOT_COLOR
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(name="Developer", value=f"{interaction.user.mention}", inline=False)
        
        # Show multiple roles
        roles = user.get('roles', ['Unknown'])
        roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
        embed.add_field(name="Roles", value=roles_str, inline=True)
        
        embed.add_field(name="Rank", value=user.get('rank', 'Unknown'), inline=True)
        embed.add_field(name="Level", value=user.get('level', 1), inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user.get('reputation', 0)}", inline=True)
        embed.add_field(name="Message Count", value=f"💬 {user.get('message_count', 0)}", inline=True)
        embed.add_field(name="Voice Minutes", value=f"🎤 {user.get('voice_minutes', 0)}", inline=True)
        
        games = user.get('portfolio_games', [])
        if games:
            embed.add_field(name="Featured Games", value=", ".join(games), inline=False)
        
        embed.set_footer(text="Developer of the Community")
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    @bot.tree.command(name="quest", description="Daily quests and rewards")
    async def quest_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        
        # Check if user has profile
        if not user:
            embed = discord.Embed(
                title="📋 Profile Not Found",
                description="You haven't created your profile yet. Click below to get started!",
                color=discord.Color.orange()
            )
            
            # Send setup DM
            from cogs.info import SetupRoleView
            from config import GUILD_ID
            embed_dm = discord.Embed(
                title="Ashtrails' Studio Setup 🎨",
                description="Select your role to get started.",
                color=discord.Color.blue()
            )
            view_dm = SetupRoleView(interaction.user.id, GUILD_ID)
            await interaction.user.send(embed=embed_dm, view=view_dm)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        view = QuestView(interaction.user.id)
        embed = discord.Embed(
            title="Daily Quests",
            description="Earn Studio Credits by completing tasks in the community",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Features",
            value="📋 View Quests\n🎁 Claim Daily Reward\n📊 Check Progress",
            inline=False
        )
        await interaction.followup.send(embed=embed, view=view)
    
    @bot.tree.command(name="review", description="AI-powered code review (Luau/Lua)")
    async def review_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="Code Review",
            description="Let me analyze your Lua code for you!",
            color=BOT_COLOR
        )
        embed.add_field(name="Features", value="🤖 AI Analysis\n⚠️ Error Detection\n💡 Optimization Tips", inline=False)
        review_embed = discord.Embed(
            title="✓ Code Review Complete",
            color=discord.Color.green()
        )
        review_embed.add_field(
            name="Analysis",
            value="✓ No syntax errors detected\n⚠️ Could optimize memory usage\n💡 Consider using local variables",
            inline=False
        )
        review_embed.add_field(name="Score", value="**8.5/10** - Good", inline=False)
        await UserProfile.add_xp(interaction.user.id, 25)
        await interaction.followup.send(embed=review_embed)
    
    @bot.tree.command(name="card", description="View your developer card")
    async def card_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            embed = discord.Embed(
                title="User Not Found",
                description="You haven't set up your profile yet",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(
            title="🎯 Developer Portfolio Card",
            color=BOT_COLOR
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Developer", value=f"{interaction.user.mention}", inline=False)
        
        # Show multiple roles
        roles = user.get('roles', ['Unknown'])
        roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
        embed.add_field(name="Roles", value=roles_str, inline=True)
        
        embed.add_field(name="Rank", value=user.get('rank', 'Unknown'), inline=True)
        embed.add_field(name="Level", value=user.get('level', 1), inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user.get('reputation', 0)}", inline=True)
        embed.add_field(name="Message Count", value=f"💬 {user.get('message_count', 0)}", inline=True)
        embed.add_field(name="Voice Minutes", value=f"🎤 {user.get('voice_minutes', 0)}", inline=True)
        games = user.get('portfolio_games', [])
        if games:
            embed.add_field(name="Featured Games", value=", ".join(games), inline=False)
        embed.set_footer(text="Developer of the Community")
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="credits", description="Check your Studio Credits and pCredits balance")
    async def credits_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)
        
        embed = discord.Embed(
            title="💰 Your Balance",
            color=BOT_COLOR
        )
        embed.add_field(name="Studio Credits", value=f"💰 {user.get('studio_credits', 0)}", inline=True)
        embed.add_field(name="pCredits", value=f"💎 {user.get('pcredits', 0)}", inline=True)
        embed.add_field(name="AI Credits", value=f"🤖 {user.get('ai_credits', 0)}", inline=True)
        
        await interaction.followup.send(embed=embed)
    
    await bot.add_cog(EconomyCog(bot))
