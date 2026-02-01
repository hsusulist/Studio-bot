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
        await interaction.response.defer()
        team = await TeamData.get_team(self.team_id)
        
        embed = discord.Embed(
            title=f"Team Members - {team['name']}",
            color=BOT_COLOR
        )
        
        for member_id in team['members']:
            embed.add_field(name=f"<@{member_id}>", value="Team Member", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Progress", emoji="📈", style=discord.ButtonStyle.success)
    async def progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        team = await TeamData.get_team(self.team_id)
        
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
        await interaction.response.defer()
        team = await TeamData.get_team(self.team_id)
        
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


class TeamCog(commands.Cog):
    """Team Management Commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def team(self, interaction: discord.Interaction):
        """Manage teams - Team creation and info"""
        await interaction.response.defer()
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
    
    async def sell(self, interaction: discord.Interaction):
        """Sell code on the marketplace"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Sell Code - Marketplace",
            description="Use the buttons below to create a marketplace listing!",
            color=BOT_COLOR
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class SellScriptModal(discord.ui.Modal):
    """Modal for creating script listings"""
    
    def __init__(self, user_id: int):
        super().__init__(title="Sell Script")
        self.user_id = user_id
        
        self.script_name = discord.ui.TextInput(
            label="Script Name",
            placeholder="e.g., Combat System v2.0",
            required=True
        )
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="What does your script do?",
            required=True,
            style=discord.TextInputStyle.long
        )
        self.price = discord.ui.TextInput(
            label="Price (Studio Credits)",
            placeholder="e.g., 500",
            required=True
        )
        
        self.add_item(self.script_name)
        self.add_item(self.description)
        self.add_item(self.price)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = int(self.price.value)
            
            # Create marketplace listing
            listing = {
                "_id": str(interaction.user.id) + "-" + self.script_name.value[:20],
                "seller_id": self.user_id,
                "seller_name": interaction.user.name,
                "title": self.script_name.value,
                "description": self.description.value,
                "price": price,
                "created_at": datetime.utcnow()
            }
            
            await MarketplaceData.create_listing(listing)
            
            embed = discord.Embed(
                title="✓ Listing Created!",
                description=f"**{self.script_name.value}** is now for sale!",
                color=discord.Color.green()
            )
            embed.add_field(name="Price", value=f"💰 {price} Credits", inline=True)
            embed.add_field(name="Status", value="🟢 Active", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="✗ Invalid Price",
                description="Price must be a number (e.g., 500)",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="✗ Error Creating Listing",
                description=f"Failed to create listing: {str(e)[:100]}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class SellView(discord.ui.View):
    """Sell code marketplace buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Create Listing", emoji="📝", style=discord.ButtonStyle.success)
    async def create_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a script listing"""
        modal = SellScriptModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="View Marketplace", emoji="🛍️", style=discord.ButtonStyle.blurple)
    async def view_marketplace(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # This would show all listings
        embed = discord.Embed(
            title="Marketplace",
            description="Browse scripts created by other developers",
            color=BOT_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class TeamSelectionView(discord.ui.View):
    """Team creation/joining buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Create Team", emoji="👥", style=discord.ButtonStyle.success)
    async def create_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a new team"""
        modal = CreateTeamModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="My Teams", emoji="📊", style=discord.ButtonStyle.blurple)
    async def my_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # This would filter teams where user is a member
        embed = discord.Embed(
            title="My Teams",
            description="You aren't in any teams yet. Create one or ask to join!",
            color=BOT_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Browse Teams", emoji="🔍", style=discord.ButtonStyle.secondary)
    async def browse_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        embed = discord.Embed(
            title="Available Teams",
            description="No public teams available yet",
            color=BOT_COLOR
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
            required=True
        )
        self.project = discord.ui.TextInput(
            label="Project Name",
            placeholder="e.g., Sword Combat System",
            required=True
        )
        
        self.add_item(self.team_name)
        self.add_item(self.project)
    
    async def on_submit(self, interaction: discord.Interaction):
        team_id = str(uuid.uuid4())[:8]
        team_name = self.team_name.value
        project = self.project.value
        
        try:
            await TeamData.create_team(team_id, self.user_id, team_name, project)
            
            # Create Discord category and channels
            guild = interaction.guild
            if guild:
                try:
                    # Create category
                    category = await guild.create_category(name=team_name[:30])  # Discord limit
                    
                    # Create text channel
                    await guild.create_text_channel(
                        name="team-chat",
                        category=category,
                        topic=f"Team chat for {team_name}"
                    )
                    
                    # Create voice channel
                    await guild.create_voice_channel(
                        name="team-voice",
                        category=category
                    )
                    
                    # Create forum channels (if supported)
                    try:
                        await guild.create_forum(
                            name="bugs",
                            category=category,
                            topic="Report and discuss bugs"
                        )
                        await guild.create_forum(
                            name="to-do-list",
                            category=category,
                            topic="Track tasks and to-dos"
                        )
                    except:
                        # If forum channels aren't supported, create text channels instead
                        await guild.create_text_channel(
                            name="bugs",
                            category=category,
                            topic="Report and discuss bugs"
                        )
                        await guild.create_text_channel(
                            name="to-do-list",
                            category=category,
                            topic="Track tasks and to-dos"
                        )
                except Exception as e:
                    print(f"Error creating team channels: {e}")
            
            embed = discord.Embed(
                title="✓ Team Created!",
                description=f"**{team_name}** has been created\n\nProject: {project}\n\n✓ Discord channels created!",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="✗ Error Creating Team",
                description=f"Failed to create team. Try again later.\n\n`{str(e)[:100]}`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    @bot.tree.command(name="team", description="Manage or create a team")
    async def team_cmd(interaction: discord.Interaction):
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
    
    @bot.tree.command(name="sell", description="Sell code on the marketplace")
    async def sell_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        view = SellView(interaction.user.id)
        embed = discord.Embed(
            title="Sell Code - Marketplace",
            description="Create listings and sell your scripts to other developers!",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Features",
            value="📝 Create Listing - Post your script\n🛍️ View Marketplace - Browse all scripts",
            inline=False
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    await bot.add_cog(TeamCog(bot))
