import discord
from discord.ext import commands
import os
import asyncio
from config import DISCORD_TOKEN, GUILD_ID
from database import UserProfile
from datetime import datetime

# Intents configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class StudioBot(commands.Bot):
    """Main Discord Bot Class"""
    
    def __init__(self):
        super().__init__(
            command_prefix="/",
            intents=intents,
            help_command=None
        )
        self.guild_id = GUILD_ID
    
    async def setup_hook(self):
        """Load all cogs"""
        # Load cogs from cogs folder
        cogs_dir = "cogs"
        try:
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    cog_name = filename[:-3]
                    try:
                        await self.load_extension(f"cogs.{cog_name}")
                        print(f"✓ Loaded cog: {cog_name}")
                    except Exception as e:
                        print(f"✗ Failed to load {cog_name}: {e}")
        except Exception as e:
            print(f"✗ Error loading cogs: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        print(f"✓ Bot logged in as {self.user}")
        
        # Wait a moment to ensure all cogs are loaded
        await asyncio.sleep(0.5)
        
        # Manually load premium cog if not loaded
        if "cogs.premium" not in self.extensions:
            try:
                await self.load_extension("cogs.premium")
                print("✓ Loaded cog: premium")
            except Exception as e:
                print(f"✗ Failed to load premium: {e}")
        
        cmds = self.tree.get_commands()
        print(f"\n📋 Registered commands ({len(cmds)}):")
        for cmd in cmds:
            print(f"  - /{cmd.name}: {cmd.description}")
        
        # Sync commands to guild
        try:
            print("\n🔄 Syncing commands globally...")
            synced = await self.tree.sync()
            print(f"✓ Synced {len(synced)} command(s) globally")
            if synced:
                for cmd in synced:
                    print(f"  ✓ {cmd.name}")
        except Exception as e:
            print(f"✗ Failed to sync command tree: {e}")
            import traceback
            traceback.print_exc()
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Developers Build the Next Big Thing | /help"
            )
        )
    
    async def on_member_join(self, member):
        """Send welcome DM on user join and assign Members role"""
        if member.bot:
            return
        
        # Create user profile if doesn't exist
        user = await UserProfile.get_user(member.id)
        if not user:
            await UserProfile.create_user(member.id, member.name)
        
        # Assign Members role
        try:
            guild = self.get_guild(self.guild_id) or await self.fetch_guild(self.guild_id)
            members_role = discord.utils.get(guild.roles, name="Members")
            if members_role:
                await member.add_roles(members_role)
                print(f"✓ Assigned Members role to {member.name}")
        except Exception as e:
            print(f"✗ Could not assign Members role: {e}")
        
        # Send welcome DM
        try:
            embed = discord.Embed(
                title="Welcome to Ashtrails' Studio! 🎨",
                description="Select your path to get started.",
                color=3092790
            )
            embed.add_field(
                name="Let's Set You Up",
                value="Click the button below to choose your role.",
                inline=False
            )
            
            view = RoleSelectionView(member.id, self.guild_id)
            await member.send(embed=embed, view=view)
        except discord.Forbidden:
            print(f"Could not DM {member.name}")
    
    async def on_message(self, message):
        """Handle experience input in DMs and track stats in guild messages"""
        # Ignore bot messages
        if message.author.bot:
            await self.process_commands(message)
            return
        
        # Track stats for guild messages
        if message.guild:
            try:
                user = await UserProfile.get_user(message.author.id)
                if user:
                    # Track message count and XP
                    new_msg_count = user.get('message_count', 0) + 1
                    await UserProfile.update_user(message.author.id, {
                        "message_count": new_msg_count
                    })
                    # Award 5 XP per message
                    await UserProfile.add_xp(message.author.id, 5)
                    print(f"✓ Tracked message from {message.author.name} - now {new_msg_count} msgs, +5 XP")
            except Exception as e:
                print(f"✗ Error tracking message stats: {e}")
        
        # Handle DM experience input
        if not isinstance(message.channel, discord.DMChannel):
            await self.process_commands(message)
            return
        
        # Get user and check if they selected a role(s)
        user = await UserProfile.get_user(message.author.id)
        print(f"DEBUG: User profile: {user}")
        if not user or not user.get('roles'):
            print(f"DEBUG: No user or no roles, skipping")
            await self.process_commands(message)
            return
        
        # Check if they already have experience set (skip if already processed)
        exp_months = user.get('experience_months', 0)
        rank = user.get('rank', 'Unknown')
        print(f"DEBUG: experience_months={exp_months}, rank={rank}")
        if exp_months > 0 or rank != 'Beginner':
            print(f"DEBUG: User already has experience or rank is not Beginner, skipping")
            await self.process_commands(message)
            return
        
        # Parse experience input
        content = message.content.strip().lower()
        experience_months = 0
        rank = 'Beginner'
        
        print(f"DEBUG: Parsing experience input: '{content}'")
        
        if content in ['skip', '0', 'beginner', 'start']:
            experience_months = 0
            rank = 'Beginner'
        else:
            import re
            # Parse formats like "1 day", "6 months", "2 years", "1.5 years", etc.
            match = re.match(r'([0-9.]+)\s*(day|month|year)s?', content)
            print(f"DEBUG: Regex match result: {match}")
            
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                print(f"DEBUG: Parsed value={value}, unit={unit}")
                
                if unit == 'day':
                    experience_months = int(value / 30)  # Convert days to months
                elif unit == 'month':
                    experience_months = int(value)
                elif unit == 'year':
                    experience_months = int(value * 12)
            else:
                # Try parsing as just a number (for backwards compatibility)
                try:
                    value = float(content)
                    experience_months = int(value * 12)  # Assume years if just number
                except ValueError:
                    embed = discord.Embed(
                        title="Invalid Input",
                        description="Please enter experience like:\n`1 day` `7 days` `1 month` `6 months` `1 year` `2 years` or `skip`",
                        color=discord.Color.red()
                    )
                    await message.reply(embed=embed)
                    return
            
            # Determine rank based on months
            if experience_months == 0:
                rank = 'Beginner'
            elif experience_months >= 36:
                rank = 'Master'
            elif experience_months >= 12:
                rank = 'Expert'
            elif experience_months >= 1:
                rank = 'Learner'
            else:
                rank = 'Beginner'
            
            print(f"DEBUG: Calculated experience_months={experience_months}, rank={rank}")
        
        # Update user profile
        print(f"DEBUG: Updating user profile with experience_months={experience_months}, rank={rank}")
        try:
            await UserProfile.update_user(message.author.id, {
                "experience_months": experience_months,
                "rank": rank
            })
            print(f"✓ Updated user profile successfully")
        except Exception as e:
            print(f"✗ Error updating user profile: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"Could not save your experience: {str(e)}",
                color=discord.Color.red()
            )
            await message.reply(embed=embed)
            return
        
        # Assign rank role and update nickname
        try:
            guild = self.get_guild(self.guild_id) or await self.fetch_guild(self.guild_id)
            member = guild.get_member(message.author.id)
            
            if member:
                # Assign rank role
                rank_role = discord.utils.get(guild.roles, name=f"[{rank}]")
                if rank_role:
                    await member.add_roles(rank_role)
                    print(f"✓ Assigned rank {rank} to {member.name}")
                else:
                    print(f"⚠️ Rank role '[{rank}]' not found in guild - creating or skipping")
                
                # Update nickname
                roles = user.get('roles', ['Unknown'])
                role_str = roles[0] if roles else 'Unknown'  # Use first role for nickname
                new_nickname = f"[{role_str} | {rank}] {message.author.name}"[:32]  # Discord limit is 32 chars
                try:
                    await member.edit(nick=new_nickname)
                    print(f"✓ Updated nickname for {member.name}: {new_nickname}")
                except Exception as e:
                    print(f"✗ Could not update nickname: {e}")
            else:
                print(f"✗ Member {message.author.id} not found in guild")
        except Exception as e:
            print(f"✗ Error in role assignment: {e}")
        
        # Send confirmation
        try:
            embed = discord.Embed(
                title="✓ Setup Complete!",
                description=f"Welcome to Ashtrails' Studio, **{message.author.mention}**!",
                color=discord.Color.green()
            )
            roles = user.get('roles', ['Unknown'])
            roles_str = ", ".join(roles) if isinstance(roles, list) else str(roles)
            embed.add_field(name="Your Roles", value=roles_str, inline=True)
            embed.add_field(name="Your Rank", value=rank, inline=True)
            
            # Display experience in readable format
            if experience_months == 0:
                exp_str = "Beginner (0 days)"
            elif experience_months < 1:
                days = int(experience_months * 30)
                exp_str = f"{days} days"
            elif experience_months < 12:
                exp_str = f"{experience_months} months"
            else:
                years = experience_months // 12
                remaining_months = experience_months % 12
                if remaining_months > 0:
                    exp_str = f"{years}y {remaining_months}m"
                else:
                    exp_str = f"{years} year{'s' if years > 1 else ''}"
            
            embed.add_field(name="Experience", value=exp_str, inline=True)
            embed.add_field(
                name="Next Steps",
                value="Go to the server and check out `/help` for all available commands!",
                inline=False
            )
            
            await message.reply(embed=embed)
            print(f"✓ Sent confirmation to {message.author.name}")
        except Exception as e:
            print(f"✗ Error sending confirmation: {e}")
    
    async def on_voice_state_update(self, member, before, after):
        """Track voice minutes when user joins/leaves voice channel"""
        if member.bot:
            return
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            print(f"📢 {member.name} joined voice channel")
            # Set start time (we'll use this to calculate duration)
            if not hasattr(member, '_voice_join_time'):
                member._voice_join_time = {}
            member._voice_join_time[after.channel.id] = datetime.utcnow()
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            try:
                if hasattr(member, '_voice_join_time') and before.channel.id in member._voice_join_time:
                    join_time = member._voice_join_time[before.channel.id]
                    duration = (datetime.utcnow() - join_time).total_seconds() / 60  # Minutes
                    
                    # Update user profile
                    user = await UserProfile.get_user(member.id)
                    if user:
                        voice_mins = user.get('voice_minutes', 0) + int(duration)
                        await UserProfile.update_user(member.id, {
                            "voice_minutes": voice_mins
                        })
                        # Award 1 XP per minute in voice
                        await UserProfile.add_xp(member.id, int(duration))
                        print(f"✓ {member.name} left voice - +{int(duration)} mins, +{int(duration)} XP")
                    
                    del member._voice_join_time[before.channel.id]
            except Exception as e:
                print(f"✗ Error tracking voice minutes: {e}")


class MultiRoleSelectView(discord.ui.View):
    """Multi-role selection with dropdown"""
    
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        
        # Add role select dropdown
        role_select = RoleSelect(user_id, guild_id)
        self.add_item(role_select)


class RoleSelect(discord.ui.Select):
    """Select dropdown for multiple roles"""
    
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
        
        # Save selected roles
        roles = self.values
        roles_str = ", ".join(roles)
        
        # Initialize rank and experience_months so on_message handler can process input
        await UserProfile.update_user(self.user_id, {
            "roles": roles,
            "rank": "Beginner",
            "experience_months": 0
        })
        print(f"DEBUG: Initialized user {self.user_id} with roles={roles}, rank=Beginner, experience_months=0")
        
        # Assign Discord roles
        try:
            guild = interaction.client.get_guild(self.guild_id) or await interaction.client.fetch_guild(self.guild_id)
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            
            if not member:
                print(f"✗ Could not find member {self.user_id}")
                await interaction.followup.send("Could not assign roles - member not found", ephemeral=True)
                return
            
            for role in roles:
                role_obj = discord.utils.get(guild.roles, name=role)
                if role_obj:
                    await member.add_roles(role_obj)
                    print(f"✓ Assigned role '{role}' to {member.name}")
                else:
                    print(f"✗ Role '{role}' not found in guild")
        except Exception as e:
            print(f"✗ Error assigning roles: {e}")
            await interaction.followup.send(f"Error assigning roles: {str(e)}", ephemeral=True)
            return
        
        # Ask for experience
        embed = discord.Embed(
            title="Experience Question",
            description=f"Great! You selected **{roles_str}** as your roles.\n\nHow much experience do you have?",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Please type your experience value. Use 'day' for days, 'month' for months, and 'year' for years.",
            value="Example: `1 day` `2 days` `1 month` `2 months` `1 year` `2 years` and if you have 0 experience type `skip` to continue as a beginner",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class RoleSelectionView(discord.ui.View):
    """Old role selection buttons - kept for backwards compatibility"""
    
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
    
    @discord.ui.button(label="Builder", emoji="🏗️", style=discord.ButtonStyle.blurple)
    async def builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "Builder")
    
    @discord.ui.button(label="Scripter", emoji="📝", style=discord.ButtonStyle.blurple)
    async def scripter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "Scripter")
    
    @discord.ui.button(label="UI Designer", emoji="🎨", style=discord.ButtonStyle.blurple)
    async def ui_designer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "UI Designer")
    
    @discord.ui.button(label="Mesh Creator", emoji="⚙️", style=discord.ButtonStyle.blurple)
    async def mesh_creator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "Mesh Creator")
    
    @discord.ui.button(label="Animator", emoji="🎬", style=discord.ButtonStyle.blurple)
    async def animator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "Animator")
    
    @discord.ui.button(label="Modeler", emoji="🟦", style=discord.ButtonStyle.blurple)
    async def modeler(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role_selection(interaction, "Modeler")
    
    async def handle_role_selection(self, interaction: discord.Interaction, role: str):
        """Handle role selection and assign Discord role"""
        await interaction.response.defer(ephemeral=True)
        
        # Update user profile
        await UserProfile.update_user(self.user_id, {"role": role})
        
        # Assign Discord role
        try:
            guild = interaction.client.get_guild(self.guild_id) or await interaction.client.fetch_guild(self.guild_id)
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)
            
            # Assign role
            role_obj = discord.utils.get(guild.roles, name=role)
            if role_obj:
                await member.add_roles(role_obj)
                print(f"✓ Assigned role {role} to {member.name}")
            else:
                print(f"✗ Role {role} not found in guild")
        except Exception as e:
            print(f"✗ Could not assign role {role}: {e}")
        
        # Ask for experience
        embed = discord.Embed(
            title="Experience Question",
            description=f"Great! You selected **{role}**.\n\nHow many years of experience do you have?",
            color=3092790
        )
        embed.add_field(
            name="Examples",
            value="Type: `0` for Beginner, `1` for 1 year, `3` for 3 years, `skip` to use default",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


def run_bot():
    """Run the bot"""
    bot = StudioBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
