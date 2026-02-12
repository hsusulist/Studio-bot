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
        await interaction.response.defer(ephemeral=True)
        user = await UserProfile.get_user(self.target_user_id)

        if not user:
            await interaction.followup.send("User not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Stats - {user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(name="Level", value=f"🎯 {user.get('level', 1)}", inline=True)
        embed.add_field(name="XP", value=f"✨ {user.get('xp', 0)}", inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user.get('reputation', 0)}", inline=True)
        embed.add_field(name="Voice Minutes", value=f"🎤 {user.get('voice_minutes', 0)}", inline=True)
        embed.add_field(name="Messages", value=f"💬 {user.get('message_count', 0)}", inline=True)
        embed.add_field(name="Reviews Given", value=f"📝 {user.get('reviews_given', 0)}", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Portfolio", emoji="🎮", style=discord.ButtonStyle.success)
    async def portfolio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = await UserProfile.get_user(self.target_user_id)

        if not user:
            await interaction.followup.send("User not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Portfolio - {user.get('username', 'Unknown')}",
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
        await interaction.response.defer(ephemeral=True)
        user = await UserProfile.get_user(self.target_user_id)

        if not user:
            await interaction.followup.send("User not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Rank - {user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(name="Current Rank", value=f"**{user.get('rank', 'Beginner')}**", inline=False)

        roles = user.get('roles', [])
        roles_str = ", ".join(roles) if roles else user.get('role', 'N/A')
        embed.add_field(name="Role", value=f"**{roles_str}**", inline=False)
        embed.add_field(name="Experience", value=f"**{user.get('experience_months', 0)} months**", inline=False)

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

    @app_commands.command(name="profile", description="View your or someone's profile")
    @app_commands.describe(user="The user to view (leave empty for yourself)")
    async def profile_cmd(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        target_user = await UserProfile.get_user(target.id)

        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)

        view = ProfileView(interaction.user.id, target.id)

        roles = target_user.get('roles', ['Unknown'])
        roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)

        embed = discord.Embed(
            title=f"{roles_str} | {target_user.get('rank', 'Beginner')}",
            description=f"**{target.mention}**",
            color=BOT_COLOR
        )

        embed.add_field(name="🎯 Level", value=str(target_user.get('level', 1)), inline=True)
        embed.add_field(name="⭐ Reputation", value=str(target_user.get('reputation', 0)), inline=True)
        embed.add_field(name="✨ XP", value=str(target_user.get('xp', 0)), inline=True)

        embed.set_thumbnail(url=target.display_avatar.url)

        created_at = target_user.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.utcnow()
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        embed.set_footer(text=f"Member since {created_at.strftime('%B %d, %Y')}")

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="leaderboard", description="View the studio leaderboard")
    async def leaderboard_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top_users = await UserProfile.get_top_users(10)

        embed = discord.Embed(
            title="🏆 Top 10 Developers of the Week",
            color=BOT_COLOR
        )

        if not top_users:
            embed.description = "No users yet!"
            await interaction.followup.send(embed=embed)
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i, user in enumerate(top_users):
            medal = medals[i] if i < len(medals) else "❌"
            roles = user.get('roles', [])
            role_str = roles[0] if roles else user.get('role', 'Unknown')
            embed.add_field(
                name=f"{medal} {user.get('username', 'Unknown')}",
                value=f"Level {user.get('level', 1)} | {role_str} | ⭐ {user.get('reputation', 0)}",
                inline=False
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))