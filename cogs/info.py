import discord
from discord.ext import commands
from discord import app_commands
from config import BOT_COLOR, GUILD_ID
from database import UserProfile


class SetupRoleSelect(discord.ui.Select):
    """Multi-role select for setup command"""
    
    def __init__(self, user_id: int, guild_id: int):
        self.user_id = user_id
        self.guild_id = guild_id
        
        options = [
            discord.SelectOption(label="Builder", emoji="🏗️", description="Build structures and environments"),
            discord.SelectOption(label="Scripter", emoji="📝", description="Write Lua/Luau scripts"),
            discord.SelectOption(label="UI Designer", emoji="🎨", description="Design user interfaces"),
            discord.SelectOption(label="Mesh Creator", emoji="⚙️", description="Create 3D meshes"),
            discord.SelectOption(label="Animator", emoji="🎬", description="Animate characters & objects"),
            discord.SelectOption(label="Modeler", emoji="🟦", description="Model 3D assets"),
        ]
        
        super().__init__(
            placeholder="Select your roles (you can choose multiple!)",
            min_values=1,
            max_values=6,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        roles = self.values
        roles_str = ", ".join(roles)
        
        user = await UserProfile.get_user(self.user_id)
        if not user:
            await UserProfile.create_user(self.user_id, interaction.user.name)
        
        await UserProfile.update_user(self.user_id, {
            "roles": roles,
            "rank": "Beginner",
            "experience_months": 0
        })
        
        # Assign Discord roles
        try:
            guild = interaction.client.get_guild(self.guild_id) or await interaction.client.fetch_guild(self.guild_id)
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            
            for role in roles:
                role_obj = discord.utils.get(guild.roles, name=role)
                if role_obj:
                    await member.add_roles(role_obj)
                    print(f"✓ Assigned role {role} to {member.name}")
        except Exception as e:
            print(f"✗ Could not assign roles: {e}")
        
        embed = discord.Embed(
            title="✓ Roles Selected!",
            description=f"Great! You selected **{roles_str}** as your roles.\n\nHow much experience do you have?",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Examples",
            value="`1 day` `7 days` `1 month` `6 months` `1 year` `2 years` or `skip` for beginner",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class SetupRoleView(discord.ui.View):
    """Role selection for /setup command"""
    
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.add_item(SetupRoleSelect(user_id, guild_id))


class HelpView(discord.ui.View):
    """Help menu navigation"""
    
    def __init__(self):
        super().__init__(timeout=60)
    
    @discord.ui.button(label="Getting Started", emoji="🚀", style=discord.ButtonStyle.blurple)
    async def getting_started(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Getting Started",
            color=BOT_COLOR
        )
        embed.add_field(
            name="1. Set Your Role",
            value="When you joined, you got DM'd to choose your role (Builder, Scripter, etc.)",
            inline=False
        )
        embed.add_field(
            name="2. Level Up",
            value="Gain XP by chatting, completing quests, and helping others",
            inline=False
        )
        embed.add_field(
            name="3. Earn Credits",
            value="Complete `/quest` daily tasks and sell code at `/shop`",
            inline=False
        )
        embed.add_field(
            name="4. Join Teams",
            value="Use `/team` to create or join teams for collaborative projects",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Commands", emoji="⚙️", style=discord.ButtonStyle.success)
    async def commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="All Commands",
            color=BOT_COLOR
        )
        embed.add_field(name="/profile", value="View your or someone's profile and stats", inline=False)
        embed.add_field(name="/shop", value="Browse marketplace, sell code, view history", inline=False)
        embed.add_field(name="/team", value="Create or manage teams for projects", inline=False)
        embed.add_field(name="/find", value="Find developers by role and experience", inline=False)
        embed.add_field(name="/quest", value="View daily quests and earn rewards", inline=False)
        embed.add_field(name="/review", value="AI code review and optimization tips", inline=False)
        embed.add_field(name="/card", value="Generate your developer portfolio card", inline=False)
        embed.add_field(name="/leaderboard", value="View top developers of the week", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Ranks & Progression", emoji="👑", style=discord.ButtonStyle.secondary)
    async def ranks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Rank System",
            color=BOT_COLOR
        )
        embed.add_field(name="🥚 Beginner", value="0 months experience or fresh accounts", inline=False)
        embed.add_field(name="🌱 Learner", value="> 1 month experience", inline=False)
        embed.add_field(name="🔥 Expert", value="> 1 year experience", inline=False)
        embed.add_field(name="👑 Master", value="> 3 years experience", inline=False)
        embed.add_field(
            name="Benefits",
            value="Higher ranks unlock:\n💰 Lower marketplace taxes\n🚀 Access to Pro-Dev channels\n📊 Marketplace priority",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class InfoCog(commands.Cog):
    """Help, Info, and Settings"""
    
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    @bot.tree.command(name="help", description="Get help and documentation")
    async def help_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        view = HelpView()
        
        embed = discord.Embed(
            title="Ashtrails' Studio Bot Help",
            description="Welcome! Learn how to use the bot and grow your skills.",
            color=BOT_COLOR
        )
        
        await interaction.followup.send(embed=embed, view=view)
    
    @bot.tree.command(name="stats", description="View server and bot statistics")
    async def stats_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            from database import _memory_users, _memory_teams, _memory_marketplace
            user_count = len(_memory_users)
            team_count = len(_memory_teams)
            listing_count = len(_memory_marketplace)
        except:
            user_count = 0
            team_count = 0
            listing_count = 0
        
        embed = discord.Embed(
            title="Ashtrails' Studio Statistics",
            color=BOT_COLOR
        )
        embed.add_field(name="Active Developers", value=str(user_count), inline=True)
        embed.add_field(name="Active Teams", value=str(team_count), inline=True)
        embed.add_field(name="Marketplace Listings", value=str(listing_count), inline=True)
        
        await interaction.followup.send(embed=embed)
    
    @bot.tree.command(name="setup", description="Setup your profile and choose your role")
    async def setup_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
        
        embed = discord.Embed(
            title="Ashtrails' Studio Setup 🎨",
            description="Select your role to get started.",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Choose Your Path",
            value="Click the button below to select your role.",
            inline=False
        )
        
        view = SetupRoleView(interaction.user.id, GUILD_ID)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @bot.tree.command(name="start", description="🎯 START HERE - Setup your profile")
    async def start_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
        
        embed = discord.Embed(
            title="Welcome to Ashtrails' Studio! 🎨",
            description="Select your role to get started.",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Choose Your Path",
            value="Click the dropdown below to select your role(s).",
            inline=False
        )
        
        view = SetupRoleView(interaction.user.id, GUILD_ID)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    await bot.add_cog(InfoCog(bot))