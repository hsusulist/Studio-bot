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
intents.voice_states = True

class StudioBot(commands.Bot):
    """Main Discord Bot Class"""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.guild_id = GUILD_ID
        self._voice_times = {}
        self._synced = False
    
    async def setup_hook(self):
        """Load all cogs"""
        print("\n🔧 Loading cogs...")
        cogs_dir = "cogs"
        try:
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    cog_name = filename[:-3]
                    try:
                        await self.load_extension(f"cogs.{cog_name}")
                        print(f"  ✓ Loaded cog: {cog_name}")
                    except Exception as e:
                        print(f"  ✗ Failed to load {cog_name}: {e}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            print(f"✗ Error loading cogs: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        print(f"\n✓ Bot logged in as {self.user}")
        print(f"✓ Bot ID: {self.user.id}")
        
        if self._synced:
            print("✓ Already synced, skipping...")
        else:
            await asyncio.sleep(1)
            cmds = self.tree.get_commands()
            print(f"\n📋 Registered Application Commands ({len(cmds)}):")
            for cmd in cmds:
                print(f"  ✓ /{cmd.name}")
            
            try:
                guild = discord.Object(id=self.guild_id)
                print(f"\n🔄 Syncing {len(cmds)} commands to guild {self.guild_id}...")
                
                # Sync exclusively to the guild to avoid duplicates
                synced = await self.tree.sync(guild=guild)
                print(f"✓ Successfully synced {len(synced)} command(s)")
                self._synced = True
                
                if len(synced) == 0 and len(cmds) > 0:
                    print(f"✓ All {len(cmds)} commands already up-to-date on Discord")
            except Exception as e:
                print(f"✗ Failed to sync commands: {e}")
                import traceback
                traceback.print_exc()
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Developers Build | /help"
            )
        )
    
    async def on_member_join(self, member):
        """Send welcome DM on user join and assign Members role"""
        if member.bot:
            return
        
        user = await UserProfile.get_user(member.id)
        if not user:
            await UserProfile.create_user(member.id, member.name)
        
        try:
            guild = self.get_guild(self.guild_id) or await self.fetch_guild(self.guild_id)
            members_role = discord.utils.get(guild.roles, name="Members")
            if members_role:
                await member.add_roles(members_role)
                print(f"✓ Assigned Members role to {member.name}")
        except Exception as e:
            print(f"✗ Could not assign Members role: {e}")
        
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
            # Need to define/import RoleSelectionView here or in on_ready
            # For now, keeping it minimal as requested
        except discord.Forbidden:
            print(f"Could not DM {member.name}")
    
    async def on_message(self, message):
        if message.author.bot:
            await self.process_commands(message)
            return
        
        if message.guild:
            try:
                user = await UserProfile.get_user(message.author.id)
                if user:
                    new_msg_count = user.get('message_count', 0) + 1
                    await UserProfile.update_user(message.author.id, {
                        "message_count": new_msg_count
                    })
                    await UserProfile.add_xp(message.author.id, 5)
            except Exception as e:
                print(f"✗ Error tracking message stats: {e}")
        
        await self.process_commands(message)

# Owner-only management commands
@commands.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    try:
        bot = ctx.bot
        guild = discord.Object(id=bot.guild_id)
        bot.tree.clear_commands(guild=guild)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        await ctx.send(f"✓ Synced {len(synced)} command(s) to guild")
    except Exception as e:
        await ctx.send(f"✗ Error: {e}")

@commands.command(name="sync_clear")
@commands.is_owner()
async def sync_clear(ctx):
    try:
        bot = ctx.bot
        guild = discord.Object(id=bot.guild_id)
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        bot._synced = False
        await ctx.send(f"✓ Cleared all commands! Restart bot to re-register.")
    except Exception as e:
        await ctx.send(f"✗ Error: {e}")

def run_bot():
    bot = StudioBot()
    bot.add_command(sync_commands)
    bot.add_command(sync_clear)
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    run_bot()
