import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, ROLES
import random

class RoleFilterView(discord.ui.View):
    """Role filter buttons for find command"""
    
    def __init__(self, all_users):
        super().__init__(timeout=60)
        self.all_users = all_users
        
        # Add role buttons
        for role_name in ROLES.keys():
            self.add_item(RoleFilterButton(role_name, self.all_users))
    
    @discord.ui.button(label="🔍 All Roles", style=discord.ButtonStyle.blurple)
    async def all_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show all developers"""
        if not self.all_users:
            embed = discord.Embed(
                title="No Developers Found",
                description="No developers available.",
                color=BOT_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        user = self.all_users[0]
        embed = discord.Embed(
            title=f"{user['username']}",
            description=f"**Level {user['level']}** | **{user.get('rank', 'N/A')}**",
            color=BOT_COLOR
        )
        embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
        embed.add_field(name="Role", value=user.get('role', 'N/A'), inline=True)
        embed.add_field(name="ID", value=f"`{user['_id']}`", inline=False)
        view = FindResultsView(self.all_users, 0)
        await interaction.response.edit_message(embed=embed, view=view)


class RoleFilterButton(discord.ui.Button):
    """Individual role filter button"""
    
    def __init__(self, role_name: str, all_users):
        emoji = ROLES.get(role_name, "❓")
        super().__init__(label=role_name, emoji=emoji, style=discord.ButtonStyle.secondary)
        self.role_name = role_name
        self.all_users = all_users
    
    async def callback(self, interaction: discord.Interaction):
        """Filter users by role"""
        # Check if role_name is in user's roles list
        filtered = [u for u in self.all_users if self.role_name in u.get('roles', [])]
        
        if not filtered:
            embed = discord.Embed(
                title=f"No {self.role_name}s Found",
                description=f"Try searching for a different role.",
                color=BOT_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        
        user = filtered[0]
        embed = discord.Embed(
            title=f"{ROLES.get(user['role'], '❓')} {user['username']}",
            description=f"**Level {user['level']}** | **{user.get('rank', 'N/A')}**",
            color=BOT_COLOR
        )
        embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
        embed.add_field(name="Role", value=user.get('role', 'N/A'), inline=True)
        embed.add_field(name="ID", value=f"`{user['_id']}`", inline=False)
        view = FindResultsView(filtered, 0, show_filter_btn=True)
        await interaction.response.edit_message(embed=embed, view=view)


class RecruitmentCog(commands.Cog):
    """Recruitment and Team Finding Commands"""
    
    def __init__(self, bot):
        self.bot = bot


class FindResultsView(discord.ui.View):
    """Pagination for find results"""
    
    def __init__(self, users, current_page: int, show_filter_btn: bool = False):
        super().__init__(timeout=60)
        self.users = users
        self.current_page = current_page
        self.max_page = min(len(users) - 1, 9)  # Show max 10 results
        self.show_filter_btn = show_filter_btn
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="DM Developer", emoji="💬", style=discord.ButtonStyle.success)
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = self.users[self.current_page]
        developer_id = user['_id']
        
        try:
            # Get developer user object
            developer = await interaction.client.fetch_user(developer_id)
            
            # Create contact message
            embed = discord.Embed(
                title=f"Interest from {interaction.user.name}",
                description=f"{interaction.user.mention} is interested in your profile!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Role", value=f"{ROLES.get(user.get('role', 'Unknown'), '❓')} {user['username']}", inline=False)
            embed.add_field(name="Level", value=f"⭐ Level {user['level']} | {user.get('rank', 'N/A')}", inline=True)
            embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
            embed.set_footer(text="Check DMs to reply!")
            
            # Send DM to developer
            await developer.send(embed=embed)
            
            # Confirm to user
            confirm = discord.Embed(
                title="✓ Message Sent!",
                description=f"DM sent to {developer.mention}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=confirm, ephemeral=True)
        except Exception as e:
            error = discord.Embed(
                title="✗ Could not send message",
                description=f"Error: {str(e)[:100]}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)
    
    @discord.ui.button(label="🔙 Back to Filters", style=discord.ButtonStyle.blurple)
    async def back_to_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to role filter selection"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="Find Developers by Role",
            description="Select a role to filter developers:",
            color=BOT_COLOR
        )
        view = RoleFilterView(self.users)
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _update_display(self, interaction: discord.Interaction):
        user = self.users[self.current_page]
        embed = discord.Embed(
            title=f"{ROLES.get(user.get('role', 'Unknown'), '❓')} {user['username']}",
            description=f"**Level {user['level']}** | **{user.get('rank', 'N/A')}**",
            color=BOT_COLOR
        )
        embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
        embed.add_field(name="Role", value=user.get('role', 'N/A'), inline=True)
        embed.add_field(name="ID", value=f"`{user['_id']}`", inline=False)
        embed.set_footer(text=f"Result {self.current_page + 1}/{self.max_page + 1}")
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    @bot.tree.command(name="find", description="Find developers by role")
    async def find_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Get all users
        all_users = await UserProfile.get_top_users(limit=100)
        
        if not all_users:
            embed = discord.Embed(
                title="No Developers Found",
                description="There are no developers in the server yet.",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Show role filter selection
        embed = discord.Embed(
            title="Find Developers by Role",
            description="Select a role to filter developers:",
            color=BOT_COLOR
        )
        view = RoleFilterView(all_users)
        await interaction.followup.send(embed=embed, view=view)
    
    await bot.add_cog(RecruitmentCog(bot))
