import discord
from discord.ext import commands
from discord import app_commands
from database import TeamData, UserProfile, MarketplaceData
from config import BOT_COLOR
import uuid
from datetime import datetime


class TeamActionView(discord.ui.View):
    """Team management buttons"""
    
    def __init__(self, team_id: str, user_id: int):
        super().__init__(timeout=60)
        self.team_id = team_id
        self.user_id = user_id
    
    @discord.ui.button(label="Members", emoji="👥", style=discord.ButtonStyle.blurple)
    async def members(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"Team Members - {team['name']}",
            color=BOT_COLOR
        )
        
        for member_id in team.get('members', []):
            embed.add_field(name=f"<@{member_id}>", value="Team Member", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Progress", emoji="📈", style=discord.ButtonStyle.success)
    async def progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"Progress - {team['name']}",
            description=f"**Project:** {team['project']}",
            color=BOT_COLOR
        )
        
        progress = team.get('progress', 0)
        bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        embed.add_field(
            name="Development Progress",
            value=f"{bar} {progress}%",
            inline=False
        )
        embed.add_field(name="Shared Wallet", value=f"💰 {team.get('shared_wallet', 0)} Credits", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Milestone", emoji="🎯", style=discord.ButtonStyle.secondary)
    async def milestone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"Milestones - {team['name']}",
            color=BOT_COLOR
        )
        
        milestones = team.get('milestones', [])
        if milestones:
            for milestone in milestones if isinstance(milestones, list) else [milestones]:
                embed.add_field(name="🎯 " + str(milestone), value="Completed", inline=False)
        else:
            embed.description = "No milestones set yet"
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class SellScriptModal(discord.ui.Modal):
    """Modal for creating script listings"""
    
    def __init__(self, user_id: int):
        super().__init__(title="Sell Script")
        self.user_id = user_id
        
        self.script_name = discord.ui.TextInput(
            label="Script Name",
            placeholder="e.g., Combat System v2.0",
            required=True,
            max_length=100
        )
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="What does your script do?",
            required=True,
            style=discord.TextStyle.long,
            max_length=500
        )
        self.price = discord.ui.TextInput(
            label="Price (Studio Credits)",
            placeholder="e.g., 500",
            required=True,
            max_length=10
        )
        
        self.add_item(self.script_name)
        self.add_item(self.description)
        self.add_item(self.price)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            price = int(self.price.value)
            
            if price <= 0:
                embed = discord.Embed(
                    title="✗ Invalid Price",
                    description="Price must be greater than 0",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            listing = {
                "_id": f"{self.user_id}-{self.script_name.value[:20].replace(' ', '_')}-{int(datetime.utcnow().timestamp())}",
                "seller_id": self.user_id,
                "seller_name": interaction.user.name,
                "title": self.script_name.value,
                "description": self.description.value,
                "price": price
            }
            
            await MarketplaceData.create_listing(listing)
            
            embed = discord.Embed(
                title="✓ Listing Created!",
                description=f"**{self.script_name.value}** is now for sale!",
                color=discord.Color.green()
            )
            embed.add_field(name="Price", value=f"💰 {price} Credits", inline=True)
            embed.add_field(name="Status", value="🟢 Active", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="✗ Invalid Price",
                description="Price must be a number (e.g., 500)",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in SellScriptModal: {e}")
            embed = discord.Embed(
                title="✗ Error Creating Listing",
                description="Something went wrong. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class SellView(discord.ui.View):
    """Sell code marketplace buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Create Listing", emoji="📝", style=discord.ButtonStyle.success)
    async def create_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SellScriptModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="View Marketplace", emoji="🛍️", style=discord.ButtonStyle.blurple)
    async def view_marketplace(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        listings = await MarketplaceData.get_user_listings(self.user_id)
        
        if not listings:
            embed = discord.Embed(
                title="My Listings",
                description="You don't have any listings yet.",
                color=BOT_COLOR
            )
        else:
            embed = discord.Embed(
                title="My Listings",
                description=f"You have {len(listings)} listing(s)",
                color=BOT_COLOR
            )
            for listing in listings[:5]:
                embed.add_field(
                    name=f"{listing.get('title')} - {listing.get('price')}💰",
                    value=f"Sold: {listing.get('sold', 0)}",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class TeamSelectionView(discord.ui.View):
    """Team creation/joining buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Create Team", emoji="👥", style=discord.ButtonStyle.success)
    async def create_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CreateTeamModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="My Teams", emoji="📊", style=discord.ButtonStyle.blurple)
    async def my_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        teams = await TeamData.get_user_teams(self.user_id)
        
        if not teams:
            embed = discord.Embed(
                title="My Teams",
                description="You aren't in any teams yet. Create one or ask to join!",
                color=BOT_COLOR
            )
        else:
            embed = discord.Embed(
                title="My Teams",
                description=f"You're in {len(teams)} team(s)",
                color=BOT_COLOR
            )
            for team in teams:
                embed.add_field(
                    name=f"🏢 {team['name']}",
                    value=f"Project: {team['project']}\nMembers: {len(team.get('members', []))}",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Browse Teams", emoji="🔍", style=discord.ButtonStyle.secondary)
    async def browse_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        teams = await TeamData.get_all_teams()
        
        if not teams:
            embed = discord.Embed(
                title="Available Teams",
                description="No public teams available yet",
                color=BOT_COLOR
            )
        else:
            embed = discord.Embed(
                title="Available Teams",
                description=f"{len(teams)} team(s) available",
                color=BOT_COLOR
            )
            for team in teams[:10]:
                embed.add_field(
                    name=team['name'],
                    value=f"Project: {team['project']}",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class CreateTeamModal(discord.ui.Modal):
    """Modal for creating teams"""
    
    def __init__(self, user_id: int):
        super().__init__(title="Create New Team")
        self.user_id = user_id
        
        self.team_name = discord.ui.TextInput(
            label="Team Name",
            placeholder="e.g., Swift Builders",
            required=True,
            max_length=30
        )
        self.project = discord.ui.TextInput(
            label="Project Name",
            placeholder="e.g., Sword Combat System",
            required=True,
            max_length=50
        )
        
        self.add_item(self.team_name)
        self.add_item(self.project)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        team_id = str(uuid.uuid4())[:8]
        team_name = self.team_name.value
        project = self.project.value
        
        try:
            await TeamData.create_team(team_id, self.user_id, team_name, project)
            
            # Try to create Discord channels
            guild = interaction.guild
            channels_created = False
            
            if guild:
                try:
                    category = await guild.create_category(name=team_name[:30])
                    await guild.create_text_channel(name="team-chat", category=category, topic=f"Team chat for {team_name}")
                    await guild.create_voice_channel(name="team-voice", category=category)
                    channels_created = True
                except Exception as e:
                    print(f"Error creating team channels: {e}")
            
            embed = discord.Embed(
                title="✓ Team Created!",
                description=f"**{team_name}** has been created!",
                color=discord.Color.green()
            )
            embed.add_field(name="Team ID", value=f"`{team_id}`", inline=True)
            embed.add_field(name="Project", value=project, inline=True)
            if channels_created:
                embed.add_field(name="Channels", value="✓ Created", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in CreateTeamModal: {e}")
            embed = discord.Embed(
                title="✗ Error Creating Team",
                description="Failed to create team. Try again later.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class TeamCog(commands.Cog):
    """Team Management Commands"""
    
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    @bot.tree.command(name="team", description="Manage or create a team")
    async def team_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
        
        view = TeamSelectionView(interaction.user.id)
        embed = discord.Embed(
            title="Team Management",
            description="Create teams, collaborate on projects, and earn together!",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Options",
            value="👥 Create - Start a new team\n📊 My Teams - View your teams\n🔍 Browse - Find teams to join",
            inline=False
        )
        await interaction.followup.send(embed=embed, view=view)
    
    await bot.add_cog(TeamCog(bot))