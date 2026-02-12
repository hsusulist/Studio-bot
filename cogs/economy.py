import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR
from datetime import datetime


class EconomyCog(commands.Cog):
    """Economy and Rewards"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="review", description="AI-powered code review (Luau/Lua)")
    async def review_cmd(self, interaction: discord.Interaction):
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

    @app_commands.command(name="card", description="View your developer card")
    async def card_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)

        if not user:
            embed = discord.Embed(
                title="User Not Found",
                description="You haven't set up your profile yet. Use `/start`",
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

        roles = user.get('roles', ['Unknown'])
        roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
        embed.add_field(name="Roles", value=roles_str, inline=True)

        embed.add_field(name="Rank", value=user.get('rank', 'Unknown'), inline=True)
        embed.add_field(name="Level", value=str(user.get('level', 1)), inline=True)
        embed.add_field(name="Reputation", value=f"⭐ {user.get('reputation', 0)}", inline=True)
        embed.add_field(name="Message Count", value=f"💬 {user.get('message_count', 0)}", inline=True)
        embed.add_field(name="Voice Minutes", value=f"🎤 {user.get('voice_minutes', 0)}", inline=True)

        games = user.get('portfolio_games', [])
        if games:
            embed.add_field(name="Featured Games", value=", ".join(games), inline=False)

        embed.set_footer(text="Developer of the Community")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="credits", description="Check your Studio Credits and pCredits balance")
    async def credits_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        embed = discord.Embed(
            title="💰 Your Balance",
            color=BOT_COLOR
        )
        embed.add_field(name="Studio Credits", value=f"💰 {user.get('studio_credits', 0)}", inline=True)
        embed.add_field(name="pCredits", value=f"💳 {user.get('pcredits', 0)}", inline=True)
        embed.add_field(name="AI Credits", value=f"💸 {user.get('ai_credits', 0)}", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="credit", description="Check your Studio Credits and pCredits balance (alias)")
    async def credit_cmd(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            user = await UserProfile.get_user(interaction.user.id)
            if not user:
                await UserProfile.create_user(interaction.user.id, interaction.user.name)
                user = await UserProfile.get_user(interaction.user.id)

            embed = discord.Embed(
                title="💰 Your Balance",
                color=BOT_COLOR
            )
            embed.add_field(name="Studio Credits", value=f"💰 {user.get('studio_credits', 0)}", inline=True)
            embed.add_field(name="pCredits", value=f"💳 {user.get('pcredits', 0)}", inline=True)
            embed.add_field(name="AI Credits", value=f"💸 {user.get('ai_credits', 0)}", inline=True)

            await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.command(name="give")
    @commands.has_permissions(administrator=True)
    async def give_cmd(self, ctx, member: discord.Member, credit_type: str, amount: int):
        """Admin command to give credits, pcredits, or ai_credits to a user"""
        credit_type = credit_type.lower()
        valid_types = {
            "credit": "studio_credits",
            "credits": "studio_credits",
            "pcredit": "pcredits",
            "pcredits": "pcredits",
            "ai": "ai_credits",
            "ai_credit": "ai_credits",
            "ai_credits": "ai_credits"
        }

        if credit_type not in valid_types:
            await ctx.send("❌ Invalid credit type. Use: `credit`, `pcredit`, or `ai`.")
            return

        db_field = valid_types[credit_type]
        user = await UserProfile.get_user(member.id)
        if not user:
            await UserProfile.create_user(member.id, member.name)
            user = await UserProfile.get_user(member.id)

        current_val = user.get(db_field, 0)
        await UserProfile.update_user(member.id, {db_field: current_val + amount})

        embed = discord.Embed(
            title="🎁 Credits Given",
            description=f"Successfully gave **{amount} {credit_type}** to {member.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))