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

        # Track loaded cogs
        loaded = []
        failed = []

        try:
            for filename in sorted(os.listdir(cogs_dir)):
                if filename.endswith(".py") and not filename.startswith("_"):
                    cog_name = filename[:-3]
                    try:
                        await self.load_extension(f"cogs.{cog_name}")
                        loaded.append(cog_name)
                        print(f"  ✓ Loaded cog: {cog_name}")
                    except Exception as e:
                        failed.append(cog_name)
                        print(f"  ✗ Failed to load {cog_name}: {e}")
                        import traceback
                        traceback.print_exc()
        except FileNotFoundError:
            print(f"  ⚠️ Cogs directory '{cogs_dir}' not found")
        except Exception as e:
            print(f"  ✗ Error loading cogs: {e}")

        print(f"\n📦 Cogs: {len(loaded)} loaded, {len(failed)} failed")
        if failed:
            print(f"  ⚠️ Failed: {', '.join(failed)}")

    async def on_ready(self):
        """Bot ready event"""
        print(f"\n✓ Bot logged in as {self.user}")
        print(f"✓ Bot ID: {self.user.id}")

        if self._synced:
            print("✓ Already synced, skipping...")
            return

        await asyncio.sleep(1)

        # List all registered commands
        cmds = self.tree.get_commands()
        print(f"\n📋 Registered Application Commands ({len(cmds)}):")
        for cmd in sorted(cmds, key=lambda c: c.name):
            print(f"  ✓ /{cmd.name}")

        # Sync to guild
        try:
            guild = discord.Object(id=self.guild_id)

            # Copy global commands to guild so they appear instantly
            self.tree.copy_global_to(guild=guild)

            print(f"\n🔄 Syncing {len(cmds)} commands to guild {self.guild_id}...")
            synced = await self.tree.sync(guild=guild)
            print(f"✓ Successfully synced {len(synced)} command(s)")
            self._synced = True

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

        # Create profile
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

        # Welcome DM
        try:
            embed = discord.Embed(
                title="Welcome to Ashtrails' Studio! 🎨",
                description=(
                    "We're glad to have you! 🎉\n\n"
                    "**Get started:**\n"
                    "• Use `/start` in the server to set up your profile\n"
                    "• Use `/daily` to claim your first credits\n"
                    "• Use `/help` to see all commands\n\n"
                    "See you in the server! 🚀"
                ),
                color=3092790
            )
            embed.set_footer(text="Ashtrails' Studio — Roblox Developer Community")
            await member.send(embed=embed)
        except discord.Forbidden:
            print(f"Could not DM {member.name}")

    async def on_message(self, message):
        if message.author.bot:
            await self.process_commands(message)
            return

        # Track message stats and give XP
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
                pass  # Silent fail for message tracking

        await self.process_commands(message)

    async def on_voice_state_update(self, member, before, after):
        """Track voice channel time for XP"""
        if member.bot:
            return

        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            self._voice_times[member.id] = datetime.utcnow()

        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            join_time = self._voice_times.pop(member.id, None)
            if join_time:
                minutes = int((datetime.utcnow() - join_time).total_seconds() / 60)
                if minutes > 0:
                    try:
                        user = await UserProfile.get_user(member.id)
                        if user:
                            current_voice = user.get('voice_minutes', 0)
                            await UserProfile.update_user(member.id, {
                                "voice_minutes": current_voice + minutes
                            })
                            # Give XP for voice time (1 XP per minute, max 60)
                            xp_gain = min(minutes, 60)
                            await UserProfile.add_xp(member.id, xp_gain)
                    except Exception:
                        pass


# ==================== OWNER COMMANDS ====================
@commands.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    """Sync all slash commands to guild"""
    try:
        bot = ctx.bot
        guild = discord.Object(id=bot.guild_id)

        # Copy global commands to guild
        bot.tree.copy_global_to(guild=guild)

        # Sync to guild
        synced = await bot.tree.sync(guild=guild)

        # List them
        cmd_names = sorted([cmd.name for cmd in synced])
        cmd_list = "\n".join([f"  ✓ /{name}" for name in cmd_names])

        await ctx.send(
            f"✅ Synced **{len(synced)}** commands to guild!\n"
            f"```\n{cmd_list}\n```"
        )
    except Exception as e:
        await ctx.send(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


@commands.command(name="sync_clear")
@commands.is_owner()
async def sync_clear(ctx):
    """Clear all commands from guild, then re-sync everything"""
    try:
        bot = ctx.bot
        guild = discord.Object(id=bot.guild_id)

        # Step 1: Clear guild commands
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print("✓ Cleared guild commands")

        # Step 2: Wait a moment
        await ctx.send("🗑️ Cleared all guild commands. Re-syncing in 2 seconds...")
        await asyncio.sleep(2)

        # Step 3: Copy global commands to guild and sync
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)

        cmd_names = sorted([cmd.name for cmd in synced])
        cmd_list = "\n".join([f"  ✓ /{name}" for name in cmd_names])

        await ctx.send(
            f"✅ Re-synced **{len(synced)}** commands!\n"
            f"```\n{cmd_list}\n```"
        )
        bot._synced = True

    except Exception as e:
        await ctx.send(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


@commands.command(name="sync_global")
@commands.is_owner()
async def sync_global(ctx):
    """Sync commands globally (takes up to 1 hour to propagate)"""
    try:
        bot = ctx.bot
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced **{len(synced)}** commands globally. May take up to 1 hour.")
    except Exception as e:
        await ctx.send(f"✗ Error: {e}")


@commands.command(name="reload")
@commands.is_owner()
async def reload_cog(ctx, cog_name: str = None):
    """Reload a specific cog or all cogs"""
    bot = ctx.bot
    cogs_dir = "cogs"

    if cog_name:
        # Reload specific cog
        ext_name = f"cogs.{cog_name}"
        try:
            try:
                await bot.unload_extension(ext_name)
            except commands.ExtensionNotLoaded:
                pass
            await bot.load_extension(ext_name)
            await ctx.send(f"✅ Reloaded `{cog_name}`")
        except Exception as e:
            await ctx.send(f"✗ Failed to reload `{cog_name}`: {e}")
    else:
        # Reload all cogs
        loaded = []
        failed = []

        for filename in sorted(os.listdir(cogs_dir)):
            if filename.endswith(".py") and not filename.startswith("_"):
                name = filename[:-3]
                ext = f"cogs.{name}"
                try:
                    try:
                        await bot.unload_extension(ext)
                    except commands.ExtensionNotLoaded:
                        pass
                    await bot.load_extension(ext)
                    loaded.append(name)
                except Exception as e:
                    failed.append(f"{name}: {e}")

        msg = f"✅ Reloaded **{len(loaded)}** cogs"
        if failed:
            msg += f"\n✗ Failed **{len(failed)}**:\n" + "\n".join(failed)
        await ctx.send(msg)


@commands.command(name="listcmds")
@commands.is_owner()
async def list_commands(ctx):
    """List all registered slash commands"""
    bot = ctx.bot
    cmds = bot.tree.get_commands()

    if not cmds:
        await ctx.send("❌ No commands registered!")
        return

    cmd_names = sorted([cmd.name for cmd in cmds])
    cmd_list = "\n".join([f"  /{name}" for name in cmd_names])

    await ctx.send(
        f"📋 **{len(cmds)} Registered Commands:**\n"
        f"```\n{cmd_list}\n```"
    )


@commands.command(name="listcogs")
@commands.is_owner()
async def list_cogs(ctx):
    """List all loaded cogs"""
    bot = ctx.bot
    cogs = bot.cogs

    if not cogs:
        await ctx.send("❌ No cogs loaded!")
        return

    cog_list = "\n".join([f"  ✓ {name}" for name in sorted(cogs.keys())])

    await ctx.send(
        f"📦 **{len(cogs)} Loaded Cogs:**\n"
        f"```\n{cog_list}\n```"
    )


def run_bot():
    bot = StudioBot()

    # Add owner-only prefix commands
    bot.add_command(sync_commands)
    bot.add_command(sync_clear)
    bot.add_command(sync_global)
    bot.add_command(reload_cog)
    bot.add_command(list_commands)
    bot.add_command(list_cogs)

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()