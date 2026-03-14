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
intents.dm_messages = True  # ADD THIS for DM support


class StudioBot(commands.Bot):
    """Main Discord Bot Class"""

    # Commands that should be GLOBAL (work everywhere + DMs)
    GLOBAL_COMMANDS = {"chat_ai", "change_mode", "ai_status", "convert", "convert_ai"}

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

        # Get all registered commands
        all_commands = self.tree.get_commands()
        print(f"\n📋 Registered Application Commands ({len(all_commands)}):")
        for cmd in sorted(all_commands, key=lambda c: c.name):
            is_global = cmd.name in self.GLOBAL_COMMANDS
            tag = "🌐 GLOBAL" if is_global else "🏠 GUILD"
            print(f"  ✓ /{cmd.name} [{tag}]")

        # ============================================================
        # STEP 1: Separate global vs guild commands
        # ============================================================
        global_cmds = []
        guild_cmds = []

        for cmd in all_commands:
            if cmd.name in self.GLOBAL_COMMANDS:
                global_cmds.append(cmd)
            else:
                guild_cmds.append(cmd)

        print(f"\n🌐 Global commands: {len(global_cmds)}")
        for cmd in global_cmds:
            print(f"  → /{cmd.name}")

        print(f"🏠 Guild commands: {len(guild_cmds)}")
        for cmd in guild_cmds:
            print(f"  → /{cmd.name}")

        # ============================================================
        # STEP 2: Sync GLOBAL commands (chat_ai, change_mode, etc.)
        # ============================================================
        try:
            print(f"\n🔄 Syncing {len(global_cmds)} global commands...")
            global_synced = await self.tree.sync()
            print(f"✓ Synced {len(global_synced)} command(s) globally")
        except Exception as e:
            print(f"✗ Failed to sync global commands: {e}")
            import traceback
            traceback.print_exc()

        # ============================================================
        # STEP 3: Sync GUILD commands (all others appear instantly)
        # ============================================================
        try:
            guild = discord.Object(id=self.guild_id)

            # Copy global to guild so they also appear instantly in main server
            self.tree.copy_global_to(guild=guild)

            print(f"🔄 Syncing all commands to guild {self.guild_id}...")
            guild_synced = await self.tree.sync(guild=guild)
            print(f"✓ Synced {len(guild_synced)} command(s) to guild")
            self._synced = True

        except Exception as e:
            print(f"✗ Failed to sync guild commands: {e}")
            import traceback
            traceback.print_exc()

        # ============================================================
        # SUMMARY
        # ============================================================
        print(f"\n{'='*50}")
        print(f"  📊 Sync Summary")
        print(f"  🌐 Global: {len(global_cmds)} commands (may take up to 1hr)")
        print(f"  🏠 Guild:  {len(guild_cmds)} commands (instant)")
        print(f"  ✅ Total:  {len(all_commands)} commands")
        print(f"{'='*50}\n")

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

        # List what will be synced globally
        all_cmds = bot.tree.get_commands()
        global_cmds = [c for c in all_cmds if c.name in bot.GLOBAL_COMMANDS]
        guild_cmds = [c for c in all_cmds if c.name not in bot.GLOBAL_COMMANDS]

        # Sync globally
        synced = await bot.tree.sync()

        # Also sync to guild for instant access
        guild = discord.Object(id=bot.guild_id)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

        global_list = "\n".join([f"  🌐 /{c.name}" for c in sorted(global_cmds, key=lambda x: x.name)])
        guild_list = "\n".join([f"  🏠 /{c.name}" for c in sorted(guild_cmds, key=lambda x: x.name)])

        await ctx.send(
            f"✅ Synced **{len(synced)}** commands!\n\n"
            f"**🌐 Global Commands** (work everywhere + DMs, up to 1hr):\n"
            f"```\n{global_list}\n```\n"
            f"**🏠 Guild Commands** (this server only, instant):\n"
            f"```\n{guild_list}\n```"
        )
    except Exception as e:
        await ctx.send(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


@commands.command(name="sync_full")
@commands.is_owner()
async def sync_full(ctx):
    """Full sync: clear everything, then re-sync global + guild properly"""
    try:
        bot = ctx.bot
        guild = discord.Object(id=bot.guild_id)

        await ctx.send("🔄 Starting full sync...\n`Step 1/4` Clearing guild commands...")

        # Step 1: Clear guild commands
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        await asyncio.sleep(1)

        await ctx.send("`Step 2/4` Syncing global commands...")

        # Step 2: Sync global commands
        global_synced = await bot.tree.sync()
        await asyncio.sleep(1)

        await ctx.send("`Step 3/4` Copying to guild for instant access...")

        # Step 3: Copy global to guild + sync guild
        bot.tree.copy_global_to(guild=guild)
        guild_synced = await bot.tree.sync(guild=guild)

        await ctx.send("`Step 4/4` Verifying...")

        # Step 4: Summary
        all_cmds = bot.tree.get_commands()
        global_cmds = [c for c in all_cmds if c.name in bot.GLOBAL_COMMANDS]
        guild_only = [c for c in all_cmds if c.name not in bot.GLOBAL_COMMANDS]

        summary = (
            f"✅ **Full Sync Complete!**\n\n"
            f"**🌐 Global** ({len(global_cmds)} commands — work in any server + DMs):\n"
        )
        for cmd in sorted(global_cmds, key=lambda x: x.name):
            summary += f"  `/{cmd.name}`\n"

        summary += f"\n**🏠 Guild Only** ({len(guild_only)} commands — this server only):\n"
        for cmd in sorted(guild_only, key=lambda x: x.name):
            summary += f"  `/{cmd.name}`\n"

        summary += (
            f"\n**📊 Totals:**\n"
            f"  Global synced: {len(global_synced)}\n"
            f"  Guild synced: {len(guild_synced)}\n\n"
            f"⚠️ Global commands may take up to **1 hour** to appear in other servers."
        )

        bot._synced = True
        await ctx.send(summary)

    except Exception as e:
        await ctx.send(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


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
    """List all registered slash commands with their scope"""
    bot = ctx.bot
    cmds = bot.tree.get_commands()

    if not cmds:
        await ctx.send("❌ No commands registered!")
        return

    global_cmds = []
    guild_cmds = []

    for cmd in sorted(cmds, key=lambda c: c.name):
        if cmd.name in bot.GLOBAL_COMMANDS:
            global_cmds.append(cmd)
        else:
            guild_cmds.append(cmd)

    msg = f"📋 **{len(cmds)} Registered Commands:**\n\n"

    if global_cmds:
        msg += "**🌐 Global (everywhere + DMs):**\n```\n"
        for cmd in global_cmds:
            msg += f"  /{cmd.name}\n"
        msg += "```\n"

    if guild_cmds:
        msg += "**🏠 Guild Only (this server):**\n```\n"
        for cmd in guild_cmds:
            msg += f"  /{cmd.name}\n"
        msg += "```"

    await ctx.send(msg)


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
    bot.add_command(sync_full)  # NEW command
    bot.add_command(reload_cog)
    bot.add_command(list_commands)
    bot.add_command(list_cogs)

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()