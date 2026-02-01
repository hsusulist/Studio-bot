import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR
from datetime import datetime

class ProfileView(discord.ui.View):
    """Profile viewing buttons"""
    
    def __init__(self, user_id: int, target_user_id: int = None):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.target_user_id = target_user_id or user_id
    
    @discord.ui.button(label="Stats", emoji="📊", style=discord.ButtonStyle.blurple)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.target_user_id)
        
        embed = discord.Embed(
            title=f"Stats - {user['username']}",
            color=BOT_COLOR
        )
        embed.add_field(name="Level", value=f"🎯 {user['level']}", inline=True)
        embed.add_field(name="XP", value=f"✨ {user['xp']}", inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
        embed.add_field(name="Voice Minutes", value=f"🎤 {user['voice_minutes']}", inline=True)
        embed.add_field(name="Messages", value=f"💬 {user['message_count']}", inline=True)
        embed.add_field(name="Reviews Given", value=f"📝 {user['reviews_given']}", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Portfolio", emoji="🎮", style=discord.ButtonStyle.success)
    async def portfolio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.target_user_id)
        
        embed = discord.Embed(
            title=f"Portfolio - {user['username']}",
            color=BOT_COLOR
        )
        
        games = user.get('portfolio_games', [])
        if games:
            for game in games:
                embed.add_field(name=game, value="🎮 Featured Game", inline=False)
        else:
            embed.description = "No games in portfolio yet"
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Rank Info", emoji="👑", style=discord.ButtonStyle.secondary)
    async def rank_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.target_user_id)
        
        embed = discord.Embed(
            title=f"Rank - {user['username']}",
            color=BOT_COLOR
        )
        embed.add_field(name="Current Rank", value=f"**{user['rank']}**", inline=False)
        embed.add_field(name="Role", value=f"**{user['role']}**", inline=False)
        embed.add_field(name="Experience", value=f"**{user['experience_months']} months**", inline=False)
        
        embed.add_field(
            name="Rank Tiers",
            value="🥚 **Beginner** → 🌱 **Learner** → 🔥 **Expert** → 👑 **Master**",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class ProfileCog(commands.Cog):
    """Profile and Stats Commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def profile(self, interaction: discord.Interaction):
        """View your profile"""
        await interaction.response.defer()
        target = interaction.user
        target_user = await UserProfile.get_user(target.id)
        
        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)
        
        view = ProfileView(interaction.user.id, target.id)
        
        # Create main profile embed
        roles = target_user.get('roles', ['Unknown'])
        roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
        embed = discord.Embed(
            title=f"{roles_str} | {target_user['rank']}",
            description=f"**{target.mention}**",
            color=BOT_COLOR
        )
        
        embed.add_field(name="🎯 Level", value=str(target_user['level']), inline=True)
        embed.add_field(name="⭐ Reputation", value=str(target_user['reputation']), inline=True)
        embed.add_field(name="✨ XP", value=str(target_user['xp']), inline=True)
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Member since {target_user['created_at'].strftime('%B %d, %Y')}")
        
        await interaction.followup.send(embed=embed, view=view)
    
    async def leaderboard(self, interaction: discord.Interaction):
        """View top developers"""
        await interaction.response.defer()
        top_users = await UserProfile.get_top_users(10)
        
        embed = discord.Embed(
            title="🏆 Top 10 Developers of the Week",
            color=BOT_COLOR
        )
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, user in enumerate(top_users):
            medal = medals[i] if i < len(medals) else "❌"
            embed.add_field(
                name=f"{medal} {user['username']}",
                value=f"Level {user['level']} | {user['role']} | ⭐ {user['reputation']}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    @bot.tree.command(name="profile", description="View your profile")
    async def profile_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        target = interaction.user
        target_user = await UserProfile.get_user(target.id)
        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)
        view = ProfileView(interaction.user.id, target.id)
        embed = discord.Embed(
            title=f"{target_user['role']} | {target_user['rank']}",
            description=f"**{target.mention}**",
            color=BOT_COLOR
        )
        embed.add_field(name="🎯 Level", value=str(target_user['level']), inline=True)
        embed.add_field(name="⭐ Reputation", value=str(target_user['reputation']), inline=True)
        embed.add_field(name="✨ XP", value=str(target_user['xp']), inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Member since {target_user['created_at'].strftime('%B %d, %Y')}")
        await interaction.followup.send(embed=embed, view=view)
    
    @bot.tree.command(name="leaderboard", description="View the studio leaderboard")
    async def leaderboard_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        top_users = await UserProfile.get_top_users(10)
        embed = discord.Embed(
            title="🏆 Top 10 Developers of the Week",
            color=BOT_COLOR
        )
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_users):
            medal = medals[i] if i < len(medals) else "❌"
            embed.add_field(
                name=f"{medal} {user['username']}",
                value=f"Level {user['level']} | {user['role']} | ⭐ {user['reputation']}",
                inline=False
            )
        await interaction.followup.send(embed=embed)
    
    await bot.add_cog(ProfileCog(bot))
