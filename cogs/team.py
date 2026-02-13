import discord
from discord.ext import commands
from discord import app_commands
from database import TeamData, UserProfile, MarketplaceData, _memory_teams
from config import BOT_COLOR
import uuid
from datetime import datetime
import time


# ============================================================
# TEAM STATS TRACKER
# ============================================================

class TeamStatsTracker:
    """Tracks voice time and message count per member per team"""

    def __init__(self):
        self._stats = {}

    def _ensure(self, team_id, user_id):
        if team_id not in self._stats:
            self._stats[team_id] = {}
        if user_id not in self._stats[team_id]:
            self._stats[team_id][user_id] = {
                "voice_seconds": 0,
                "messages": 0,
                "last_voice_join": None
            }

    def add_message(self, team_id, user_id):
        self._ensure(team_id, user_id)
        self._stats[team_id][user_id]["messages"] += 1

    def voice_join(self, team_id, user_id):
        self._ensure(team_id, user_id)
        self._stats[team_id][user_id]["last_voice_join"] = time.time()

    def voice_leave(self, team_id, user_id):
        self._ensure(team_id, user_id)
        entry = self._stats[team_id][user_id]
        if entry["last_voice_join"]:
            elapsed = time.time() - entry["last_voice_join"]
            entry["voice_seconds"] += elapsed
            entry["last_voice_join"] = None

    def get_team_stats(self, team_id):
        if team_id not in self._stats:
            return {}
        result = {}
        for user_id, data in self._stats[team_id].items():
            voice = data["voice_seconds"]
            if data["last_voice_join"]:
                voice += time.time() - data["last_voice_join"]
            result[user_id] = {
                "voice_seconds": round(voice),
                "messages": data["messages"]
            }
        return result

    def get_member_stats(self, team_id, user_id):
        self._ensure(team_id, user_id)
        data = self._stats[team_id][user_id]
        voice = data["voice_seconds"]
        if data["last_voice_join"]:
            voice += time.time() - data["last_voice_join"]
        return {"voice_seconds": round(voice), "messages": data["messages"]}

    def format_time(self, seconds):
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"


# Global tracker instance
team_stats = TeamStatsTracker()


# ============================================================
# CONFIRM DELETE VIEW
# ============================================================

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, team_id, user_id):
        super().__init__(timeout=30)
        self.team_id = team_id
        self.user_id = user_id

    @discord.ui.button(label="Yes, Delete", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your team.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        guild = interaction.guild
        if guild and team.get("category_id"):
            try:
                category = guild.get_channel(team["category_id"])
                if isinstance(category, discord.CategoryChannel):
                    for channel in category.channels:
                        await channel.delete(reason="Team deleted")
                    await category.delete(reason="Team deleted")
            except Exception as e:
                print(f"Error deleting team channels: {e}")

        team_name = team["name"]
        await TeamData.delete_team(self.team_id)

        await interaction.followup.send(embed=discord.Embed(
            title="🗑️ Team Deleted",
            description=f"**{team_name}** has been deleted.",
            color=discord.Color.red()),
            ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.stop()


# ============================================================
# SETTINGS MODALS
# ============================================================

class SetProgressModal(discord.ui.Modal):
    def __init__(self, team_id):
        super().__init__(title="Set Progress")
        self.team_id = team_id
        self.percent = discord.ui.TextInput(
            label="Progress Percentage (0-100)",
            placeholder="e.g., 50",
            required=True,
            max_length=3)
        self.add_item(self.percent)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            percent = max(0, min(100, int(self.percent.value)))
            await TeamData.update_team(self.team_id, {"progress": percent})
            filled = percent // 5
            bar = "█" * filled + "░" * (20 - filled)
            await interaction.followup.send(embed=discord.Embed(
                title="📈 Progress Updated",
                description=f"\n[{bar}] {percent}%\n",
                color=discord.Color.green()),
                ephemeral=True)
        except ValueError:
            await interaction.followup.send("Enter a number between 0 and 100.", ephemeral=True)


class AddMilestoneModal(discord.ui.Modal):
    def __init__(self, team_id):
        super().__init__(title="Add Milestone")
        self.team_id = team_id
        self.name = discord.ui.TextInput(
            label="Milestone Name",
            placeholder="e.g., Core combat system complete",
            required=True,
            max_length=100)
        self.description = discord.ui.TextInput(
            label="Description (optional)",
            placeholder="What does this milestone include?",
            required=False,
            max_length=200)
        self.add_item(self.name)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        milestones = team.get("milestones", [])
        milestones.append({
            "name": self.name.value,
            "description": self.description.value or "",
            "completed": False,
            "added_at": datetime.utcnow().isoformat()
        })
        await TeamData.update_team(self.team_id, {"milestones": milestones})
        await interaction.followup.send(embed=discord.Embed(
            title="🎯 Milestone Added",
            description=f"{self.name.value}",
            color=discord.Color.green()),
            ephemeral=True)


class KickMemberModal(discord.ui.Modal):
    def __init__(self, team_id):
        super().__init__(title="Kick Member")
        self.team_id = team_id
        self.member_id = discord.ui.TextInput(
            label="Member User ID",
            placeholder="Right-click user > Copy User ID",
            required=True,
            max_length=20)
        self.add_item(self.member_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            member_id = int(self.member_id.value.strip())
        except ValueError:
            await interaction.followup.send("Invalid user ID.", ephemeral=True)
            return

        if member_id == interaction.user.id:
            await interaction.followup.send("You can't kick yourself.", ephemeral=True)
            return

        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        success = await TeamData.remove_member(self.team_id, member_id)
        if success:
            guild = interaction.guild
            if guild and team.get("category_id"):
                try:
                    member = guild.get_member(member_id)
                    category = guild.get_channel(team["category_id"])
                    if category and member:
                        await category.set_permissions(member, overwrite=None)
                except Exception:
                    pass
            await interaction.followup.send(embed=discord.Embed(
                title="👢 Member Kicked",
                description=f"<@{member_id}> removed from the team.",
                color=discord.Color.orange()),
                ephemeral=True)
        else:
            await interaction.followup.send("That user isn't in this team.", ephemeral=True)


class AddProjectModal(discord.ui.Modal):
    """Add a project to a team — separate from team creation"""
    def __init__(self, team_id):
        super().__init__(title="Add Project")
        self.team_id = team_id
        self.project_name = discord.ui.TextInput(
            label="Project Name",
            placeholder="e.g., Sword Combat System",
            required=True,
            max_length=50)
        self.project_desc = discord.ui.TextInput(
            label="Description (optional)",
            placeholder="What is this project about?",
            required=False,
            max_length=200,
            style=discord.TextStyle.long)
        self.add_item(self.project_name)
        self.add_item(self.project_desc)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        # Check project limit
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
             await interaction.followup.send("Profile not found.", ephemeral=True)
             return
             
        max_projects = user.get("max_projects", 2)
        current_projects = team.get("projects", [])
        active_projects = [p for p in current_projects if p.get("status") == "active"]

        if len(active_projects) >= max_projects:
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Project Limit Reached",
                description=f"Max **{max_projects}** active projects per team.\nBuy more slots in `/pshop`.",
                color=discord.Color.red()),
                ephemeral=True)
            return

        await TeamData.add_project(self.team_id, self.project_name.value, self.project_desc.value or "")

        # Also update the main project field if it's the default
        if team.get("project") == "No project yet":
            await TeamData.update_team(self.team_id, {"project": self.project_name.value})

        await interaction.followup.send(embed=discord.Embed(
            title="📁 Project Added",
            description=f"**{self.project_name.value}** added to the team!",
            color=discord.Color.green()),
            ephemeral=True)


class SetBannerModal(discord.ui.Modal):
    """Set custom team banner (requires purchase)"""
    def __init__(self, team_id):
        super().__init__(title="Set Team Banner")
        self.team_id = team_id
        self.banner_desc = discord.ui.TextInput(
            label="Team Description",
            placeholder="Describe your team...",
            required=True,
            max_length=200,
            style=discord.TextStyle.long)
        self.banner_color = discord.ui.TextInput(
            label="Color Hex (e.g., #FF5733)",
            placeholder="#FF5733",
            required=False,
            max_length=7)
        self.add_item(self.banner_desc)
        self.add_item(self.banner_color)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        updates = {"banner_description": self.banner_desc.value}
        if self.banner_color.value:
            color_str = self.banner_color.value.strip().lstrip("#")
            try:
                int(color_str, 16)
                updates["banner_color"] = int(color_str, 16)
            except ValueError:
                pass

        await TeamData.update_team(self.team_id, updates)
        await interaction.followup.send(embed=discord.Embed(
            title="🎨 Banner Updated",
            description="Team banner has been customized!",
            color=discord.Color.green()),
            ephemeral=True)


# ============================================================
# TEAM SETTINGS VIEW
# ============================================================

class TeamSettingsView(discord.ui.View):
    def __init__(self, team_id, user_id):
        super().__init__(timeout=120)
        self.team_id = team_id
        self.user_id = user_id

    @discord.ui.button(label="Toggle Privacy", emoji="🔒", style=discord.ButtonStyle.blurple)
    async def toggle_privacy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        new_privacy = not team.get("private", True)
        await TeamData.update_team(self.team_id, {"private": new_privacy})
        status = "🔒 Private" if new_privacy else "🌐 Public"
        await interaction.followup.send(embed=discord.Embed(
            title="Privacy Updated",
            description=f"Team is now {status}",
            color=BOT_COLOR),
            ephemeral=True)

    @discord.ui.button(label="Set Progress", emoji="📈", style=discord.ButtonStyle.success)
    async def set_progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        modal = SetProgressModal(self.team_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Milestone", emoji="🎯", style=discord.ButtonStyle.secondary)
    async def add_milestone(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        modal = AddMilestoneModal(self.team_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Project", emoji="📁", style=discord.ButtonStyle.success, row=1)
    async def add_project(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        modal = AddProjectModal(self.team_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Set Banner", emoji="🎨", style=discord.ButtonStyle.secondary, row=1)
    async def set_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        team = await TeamData.get_team(self.team_id)
        if not team or not team.get("has_banner"):
            await interaction.response.send_message(
                "🎨 You need the **Custom Team Banner** from `/pshop` first!", ephemeral=True)
            return
        modal = SetBannerModal(self.team_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Kick Member", emoji="👢", style=discord.ButtonStyle.danger, row=2)
    async def kick_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        modal = KickMemberModal(self.team_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete Team", emoji="🗑️", style=discord.ButtonStyle.danger, row=2)
    async def delete_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the owner can do this.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return
        view = ConfirmDeleteView(self.team_id, self.user_id)
        await interaction.followup.send(embed=discord.Embed(
            title="⚠️ Delete Team?",
            description=(
                f"Are you sure you want to delete **{team['name']}**?\n\n"
                f"This will:\n"
                f"- Remove all members\n"
                f"- Delete team channels\n"
                f"- This cannot be undone"),
            color=discord.Color.red()),
            view=view,
            ephemeral=True)


# ============================================================
# TEAM ACTION VIEW (manage a specific team)
# ============================================================

class TeamActionView(discord.ui.View):
    def __init__(self, team_id, user_id):
        super().__init__(timeout=120)
        self.team_id = team_id
        self.user_id = user_id

    @discord.ui.button(label="Members", emoji="👥", style=discord.ButtonStyle.blurple)
    async def members(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        embed = discord.Embed(title=f"👥 {team['name']} — Members", color=BOT_COLOR)
        members = team.get("members", [])
        creator_id = team.get("creator_id")
        member_list = []
        for member_id in members:
            role = "👑 Owner" if member_id == creator_id else "👤 Member"
            member_list.append(f"{role} — <@{member_id}>")
        embed.description = "\n".join(member_list) if member_list else "No members"
        embed.set_footer(text=f"{len(members)}/{team.get('max_members', 5)} members")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Projects", emoji="📁", style=discord.ButtonStyle.success)
    async def projects(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        projects = team.get("projects", [])
        embed = discord.Embed(title=f"📁 {team['name']} — Projects", color=BOT_COLOR)

        if projects:
            for i, proj in enumerate(projects):
                status_icon = "🟢" if proj.get("status") == "active" else "⚪"
                desc = proj.get("description", "No description") or "No description"
                embed.add_field(
                    name=f"{status_icon} {proj.get('name', f'Project {i+1}')}",
                    value=desc[:100],
                    inline=False)
            embed.set_footer(text="Owner can add projects in ⚙️ Settings")
        else:
            embed.description = "No projects yet.\nOwner can add them in ⚙️ Settings."

        # Add buttons to the message
        class ProjectView(discord.ui.View):
            def __init__(self, team_id, owner_id):
                super().__init__(timeout=60)
                self.team_id = team_id
                self.owner_id = owner_id

            @discord.ui.button(label="Add Project", style=discord.ButtonStyle.green)
            async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.owner_id:
                    await interaction.response.send_message("Only the owner can add projects.", ephemeral=True)
                    return
                await interaction.response.send_modal(AddProjectModal(self.team_id))

        await interaction.followup.send(embed=embed, view=ProjectView(self.team_id, team.get("creator_id")), ephemeral=True)

    @discord.ui.button(label="Stats", emoji="📊", style=discord.ButtonStyle.secondary)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        members = team.get("members", [])
        all_stats = team_stats.get_team_stats(self.team_id)

        total_messages = 0
        total_voice = 0
        member_data = []

        for member_id in members:
            stats = all_stats.get(member_id, {"voice_seconds": 0, "messages": 0})
            total_messages += stats["messages"]
            total_voice += stats["voice_seconds"]
            member_data.append({
                "id": member_id,
                "messages": stats["messages"],
                "voice": stats["voice_seconds"]
            })

        member_data.sort(key=lambda x: x["messages"] + (x["voice"] // 60), reverse=True)

        embed = discord.Embed(title=f"📊 {team['name']} — Team Stats", color=BOT_COLOR)

        progress = team.get("progress", 0)
        filled = progress // 5
        bar = "█" * filled + "░" * (20 - filled)

        overview = (
            f"```\n[{bar}] {progress}%\n```\n"
            f"👥 **Members:** {len(members)}/{team.get('max_members', 5)}\n"
            f"💬 **Total Messages:** {total_messages}\n"
            f"🔊 **Total Voice Time:** {team_stats.format_time(total_voice)}\n"
            f"💰 **Shared Wallet:** {team.get('shared_wallet', 0)} Credits\n"
            f"📁 **Projects:** {len(team.get('projects', []))}\n"
            f"🎯 **Milestones:** {len(team.get('milestones', []))}")
        embed.description = overview

        if member_data:
            member_lines = []
            for i, md in enumerate(member_data[:10]):
                rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"`{i + 1}.`"
                voice_str = team_stats.format_time(md["voice"])
                member_lines.append(
                    f"{rank_icon} <@{md['id']}>\n"
                    f"    💬 {md['messages']} msgs · 🔊 {voice_str}")
            embed.add_field(name="Member Activity",
                            value="\n".join(member_lines),
                            inline=False)

        created = team.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(created)
                age_days = (datetime.utcnow() - created_dt).days
                embed.set_footer(text=f"Team created {age_days} days ago · ID: {self.team_id}")
            except Exception:
                embed.set_footer(text=f"ID: {self.team_id}")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Milestones", emoji="🎯", style=discord.ButtonStyle.secondary)
    async def milestone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        embed = discord.Embed(title=f"🎯 {team['name']} — Milestones", color=BOT_COLOR)
        milestones = team.get("milestones", [])
        if milestones and isinstance(milestones, list):
            completed = sum(1 for ms in milestones if isinstance(ms, dict) and ms.get("completed"))
            total = len(milestones)
            if total > 0:
                pct = int((completed / total) * 100)
                filled = pct // 5
                bar = "█" * filled + "░" * (20 - filled)
                embed.description = f"```\n[{bar}] {completed}/{total} completed\n```"

            for i, ms in enumerate(milestones):
                if isinstance(ms, dict):
                    name = ms.get("name", f"Milestone {i + 1}")
                    done = ms.get("completed", False)
                    icon = "✅" if done else "⬜"
                    desc = ms.get("description", "") or "—"
                    embed.add_field(name=f"{icon} {name}", value=desc, inline=False)
                else:
                    embed.add_field(name=f"🎯 {ms}", value="—", inline=False)
        else:
            embed.description = "No milestones yet.\nOwner can add them in ⚙️ Settings."
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Invite", emoji="📨", style=discord.ButtonStyle.secondary, row=1)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        if interaction.user.id != team.get("creator_id"):
            await interaction.followup.send("Only the owner can view the invite code.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📨 {team['name']} — Invite",
            description=(
                f"**Invite Code:** `{team.get('invite_code', 'N/A')}`\n\n"
                f"Others join with `/team_join {team.get('invite_code', '')}`\n\n"
                f"**Privacy:** {'🔒 Private' if team.get('private', True) else '🌐 Public'}\n"
                f"**Slots:** {len(team.get('members', []))}/{team.get('max_members', 5)}"),
            color=BOT_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Settings", emoji="⚙️", style=discord.ButtonStyle.danger, row=1)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        team = await TeamData.get_team(self.team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        if interaction.user.id != team.get("creator_id"):
            await interaction.followup.send("Only the owner can access settings.", ephemeral=True)
            return

        view = TeamSettingsView(self.team_id, self.user_id)
        embed = discord.Embed(
            title=f"⚙️ {team['name']} — Settings",
            description=(
                f"**Team ID:** `{self.team_id}`\n"
                f"**Privacy:** {'🔒 Private' if team.get('private', True) else '🌐 Public'}\n"
                f"**Max Members:** {team.get('max_members', 5)}\n"
                f"**Projects:** {len(team.get('projects', []))}\n"
                f"**Storage:** {'☁️ Enabled' if team.get('has_storage') else '❌ Not unlocked'}\n"
                f"**Banner:** {'🎨 Custom' if team.get('has_banner') else '❌ Not unlocked'}"),
            color=discord.Color.orange())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# ============================================================
# TEAM SELECT VIEW (multiple teams dropdown)
# ============================================================

class TeamSelectView(discord.ui.View):
    def __init__(self, teams, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

        options = []
        for team in teams[:25]:
            is_owner = team.get("creator_id") == user_id
            role = "Owner" if is_owner else "Member"
            proj = team.get('project', 'No project')[:50]
            options.append(
                discord.SelectOption(
                    label=team["name"][:100],
                    value=team["_id"],
                    description=f"{role} · {proj}"))

        select = discord.ui.Select(placeholder="Select a team to manage", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        team_id = interaction.data["values"][0]
        team = await TeamData.get_team(team_id)
        if not team:
            await interaction.followup.send("Team not found!", ephemeral=True)
            return

        progress = team.get("progress", 0)
        filled = progress // 5
        bar = "█" * filled + "░" * (20 - filled)
        members = team.get("members", [])
        is_owner = team.get("creator_id") == self.user_id
        privacy = "🔒 Private" if team.get("private", True) else "🌐 Public"

        color = team.get("banner_color", BOT_COLOR) or BOT_COLOR
        embed = discord.Embed(title=f"{privacy} {team['name']}", color=color)

        if team.get("banner_description"):
            embed.description = f"*{team['banner_description']}*\n"

        embed.add_field(name="Project", value=team.get("project", "None"), inline=True)
        embed.add_field(name="Role", value="👑 Owner" if is_owner else "👤 Member", inline=True)
        embed.add_field(name="Members", value=f"{len(members)}/{team.get('max_members', 5)}", inline=True)
        embed.add_field(name="Progress", value=f"```\n[{bar}] {progress}%\n```", inline=False)
        embed.add_field(name="💰 Wallet", value=f"{team.get('shared_wallet', 0)} Credits", inline=True)
        embed.add_field(name="📁 Projects", value=str(len(team.get('projects', []))), inline=True)

        view = TeamActionView(team_id, self.user_id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# ============================================================
# CREATE TEAM MODAL — PROJECT IS OPTIONAL
# ============================================================

class CreateTeamModal(discord.ui.Modal):
    def __init__(self, user_id):
        super().__init__(title="Create New Team")
        self.user_id = user_id
        self.team_name = discord.ui.TextInput(
            label="Team Name",
            placeholder="e.g., Swift Builders",
            required=True,
            max_length=30)
        self.project = discord.ui.TextInput(
            label="Project Name (optional)",
            placeholder="e.g., Sword Combat System — leave blank to add later",
            required=False,
            max_length=50)
        self.add_item(self.team_name)
        self.add_item(self.project)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        team_id = str(uuid.uuid4())[:8]
        team_name = self.team_name.value
        project = self.project.value or ""

        try:
            user = await UserProfile.get_user(self.user_id)
            max_teams = user.get("max_teams", 3) if user else 3
            current_teams = await TeamData.get_user_teams(self.user_id)

            if len(current_teams) >= max_teams:
                await interaction.followup.send(embed=discord.Embed(
                    title="✗ Team Limit Reached",
                    description=(
                        f"You can only have **{max_teams}** team(s).\n"
                        f"Buy more slots in `/pshop`."),
                    color=discord.Color.red()),
                    ephemeral=True)
                return

            team = await TeamData.create_team(team_id, self.user_id, team_name, project, private=True)
            invite_code = team.get("invite_code", "N/A")

            # Add project to projects list if provided
            if project:
                await TeamData.add_project(team_id, project)

            guild = interaction.guild
            channels_created = False

            if guild:
                try:
                    overwrites = {
                        guild.default_role:
                            discord.PermissionOverwrite(read_messages=False),
                        interaction.user:
                            discord.PermissionOverwrite(
                                read_messages=True,
                                send_messages=True,
                                manage_channels=True),
                        guild.me:
                            discord.PermissionOverwrite(
                                read_messages=True,
                                send_messages=True,
                                manage_channels=True)
                    }

                    category = await guild.create_category(
                        name=f"🏢 {team_name[:25]}", overwrites=overwrites)
                    await guild.create_text_channel(
                        name="team-chat",
                        category=category,
                        topic=f"Team: {team_name} · ID: {team_id}")
                    await guild.create_text_channel(
                        name="team-code",
                        category=category,
                        topic="Share code and resources")
                    await guild.create_voice_channel(
                        name="Team Voice", category=category)
                    channels_created = True
                    await TeamData.update_team(team_id, {"category_id": category.id})
                except Exception as e:
                    print(f"Error creating team channels: {e}")

            embed = discord.Embed(
                title="✓ Team Created!",
                description=f"**{team_name}** is ready!",
                color=discord.Color.green())
            embed.add_field(name="Team ID", value=f"`{team_id}`", inline=True)
            embed.add_field(name="Project", value=project or "None — add later in Settings", inline=True)
            embed.add_field(name="Privacy", value="🔒 Private", inline=True)
            embed.add_field(
                name="📨 Invite Code",
                value=f"`{invite_code}`\nOthers join with `/team_join {invite_code}`",
                inline=False)
            if channels_created:
                embed.add_field(name="Channels", value="✅ Private channels created", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in CreateTeamModal: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Error",
                description="Failed to create team.",
                color=discord.Color.red()),
                ephemeral=True)


# ============================================================
# SELL SCRIPT MODAL
# ============================================================

class SellScriptModal(discord.ui.Modal):
    def __init__(self, user_id):
        super().__init__(title="Sell Script")
        self.user_id = user_id
        self.script_name = discord.ui.TextInput(
            label="Script Name",
            placeholder="e.g., Combat System v2.0",
            required=True,
            max_length=100)
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="What does your script do?",
            required=True,
            style=discord.TextStyle.long,
            max_length=500)
        self.price = discord.ui.TextInput(
            label="Price (Studio Credits)",
            placeholder="e.g., 500",
            required=True,
            max_length=10)
        self.add_item(self.script_name)
        self.add_item(self.description)
        self.add_item(self.price)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            price = int(self.price.value)
            if price <= 0:
                await interaction.followup.send(embed=discord.Embed(
                    title="✗ Invalid Price",
                    description="Price must be greater than 0.",
                    color=discord.Color.red()),
                    ephemeral=True)
                return

            listing = {
                "_id": f"{self.user_id}-{self.script_name.value[:20].replace(' ', '_')}-{int(datetime.utcnow().timestamp())}",
                "seller_id": self.user_id,
                "seller_name": interaction.user.name,
                "title": self.script_name.value,
                "description": self.description.value,
                "price": price,
                "sold": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            await MarketplaceData.create_listing(listing)

            embed = discord.Embed(
                title="✓ Listing Created!",
                description=f"**{self.script_name.value}** is now for sale!",
                color=discord.Color.green())
            embed.add_field(name="Price", value=f"💰 {price} Credits", inline=True)
            embed.add_field(name="Status", value="🟢 Active", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Invalid Price",
                description="Price must be a number.",
                color=discord.Color.red()),
                ephemeral=True)
        except Exception as e:
            print(f"Error in SellScriptModal: {e}")
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Error",
                description="Something went wrong.",
                color=discord.Color.red()),
                ephemeral=True)


# ============================================================
# SELL VIEW
# ============================================================

class SellView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="Create Listing", emoji="📝", style=discord.ButtonStyle.success)
    async def create_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        modal = SellScriptModal(self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="My Listings", emoji="📋", style=discord.ButtonStyle.blurple)
    async def view_listings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        listings = await MarketplaceData.get_user_listings(self.user_id)
        if not listings:
            embed = discord.Embed(
                title="📋 My Listings",
                description="You don't have any listings yet.",
                color=BOT_COLOR)
        else:
            embed = discord.Embed(
                title="📋 My Listings",
                description=f"You have {len(listings)} listing(s)",
                color=BOT_COLOR)
            for listing in listings[:10]:
                embed.add_field(
                    name=f"📄 {listing.get('title', '?')}",
                    value=f"💰 {listing.get('price', 0)} Credits · Sold: {listing.get('sold', 0)}",
                    inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


# ============================================================
# TEAM SELECTION VIEW (main /team UI)
# ============================================================

class TeamSelectionView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="Create Team", emoji="➕", style=discord.ButtonStyle.success)
    async def create_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        modal = CreateTeamModal(self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="My Teams", emoji="📊", style=discord.ButtonStyle.blurple)
    async def my_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        teams = await TeamData.get_user_teams(self.user_id)

        if not teams:
            embed = discord.Embed(
                title="📊 My Teams",
                description=(
                    "You aren't in any teams yet.\n\n"
                    "➕ Click **Create Team** to start one\n"
                    "🔍 Click **Browse** to find public teams\n"
                    "📨 Use `/team_join <code>` with an invite"),
                color=BOT_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if len(teams) == 1:
            team = teams[0]
            progress = team.get("progress", 0)
            filled = progress // 5
            bar = "█" * filled + "░" * (20 - filled)
            members = team.get("members", [])
            is_owner = team.get("creator_id") == self.user_id
            privacy = "🔒 Private" if team.get("private", True) else "🌐 Public"

            all_stats = team_stats.get_team_stats(team["_id"])
            total_msgs = sum(s["messages"] for s in all_stats.values())
            total_voice = sum(s["voice_seconds"] for s in all_stats.values())

            color = team.get("banner_color", BOT_COLOR) or BOT_COLOR
            embed = discord.Embed(title=f"{privacy} {team['name']}", color=color)

            if team.get("banner_description"):
                embed.description = f"*{team['banner_description']}*"

            embed.add_field(name="Project", value=team.get("project", "None"), inline=True)
            embed.add_field(name="Role", value="👑 Owner" if is_owner else "👤 Member", inline=True)
            embed.add_field(name="Members", value=f"{len(members)}/{team.get('max_members', 5)}", inline=True)
            embed.add_field(name="Progress", value=f"```\n[{bar}] {progress}%\n```", inline=False)
            embed.add_field(name="💬 Messages", value=str(total_msgs), inline=True)
            embed.add_field(name="🔊 Voice Time", value=team_stats.format_time(total_voice), inline=True)
            embed.add_field(name="💰 Wallet", value=f"{team.get('shared_wallet', 0)} Credits", inline=True)

            view = TeamActionView(team["_id"], self.user_id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="📊 My Teams",
                description=f"You're in **{len(teams)}** team(s)\n\nSelect a team to manage:",
                color=BOT_COLOR)
            for team in teams[:10]:
                members = team.get("members", [])
                progress = team.get("progress", 0)
                is_owner = team.get("creator_id") == self.user_id
                role = "👑" if is_owner else "👤"
                privacy = "🔒" if team.get("private", True) else "🌐"
                filled = progress // 10
                bar = "█" * filled + "░" * (10 - filled)

                embed.add_field(
                    name=f"{privacy} {team['name']} {role}",
                    value=(
                        f"📁 {team.get('project', 'No project')}\n"
                        f"👥 {len(members)}/{team.get('max_members', 5)} · [{bar}] {progress}%\n"
                        f"ID: `{team['_id']}`"),
                    inline=False)

            view = TeamSelectView(teams, self.user_id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Browse", emoji="🔍", style=discord.ButtonStyle.secondary)
    async def browse_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        teams = await TeamData.get_all_teams()

        if not teams:
            embed = discord.Embed(
                title="🔍 Public Teams",
                description="No public teams available.\nTeams are private by default. Ask for an invite code!",
                color=BOT_COLOR)
        else:
            embed = discord.Embed(
                title="🔍 Public Teams",
                description=f"**{len(teams)}** public team(s) available",
                color=BOT_COLOR)
            for team in teams[:10]:
                members = team.get("members", [])
                max_m = team.get("max_members", 5)
                full = len(members) >= max_m
                status = "🔴 Full" if full else "🟢 Open"
                embed.add_field(
                    name=f"{team['name']} — {status}",
                    value=f"📁 {team.get('project', 'No project')}\n👥 {len(members)}/{max_m}",
                    inline=False)
        embed.set_footer(text="Use /team_join <invite_code> to join")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.secondary)
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        teams = await TeamData.get_user_teams(self.user_id)

        if not teams:
            await interaction.followup.send(embed=discord.Embed(
                title="🏆 Team Leaderboard",
                description="Join or create a team first!",
                color=BOT_COLOR),
                ephemeral=True)
            return

        embed = discord.Embed(title="🏆 Team Leaderboard", color=0xFFD700)

        for team in teams:
            team_id = team["_id"]
            members = team.get("members", [])
            all_stats = team_stats.get_team_stats(team_id)

            member_scores = []
            for member_id in members:
                stats = all_stats.get(member_id, {"voice_seconds": 0, "messages": 0})
                score = stats["messages"] + (stats["voice_seconds"] // 60)
                member_scores.append({
                    "id": member_id,
                    "messages": stats["messages"],
                    "voice": stats["voice_seconds"],
                    "score": score
                })

            member_scores.sort(key=lambda x: x["score"], reverse=True)

            board_lines = []
            medals = ["🥇", "🥈", "🥉"]
            for i, ms in enumerate(member_scores[:5]):
                medal = medals[i] if i < 3 else f"`{i + 1}.`"
                voice_str = team_stats.format_time(ms["voice"])
                board_lines.append(
                    f"{medal} <@{ms['id']}> — {ms['messages']} msgs · {voice_str} voice")

            if board_lines:
                total_msgs = sum(s["messages"] for s in member_scores)
                total_voice = sum(s["voice"] for s in member_scores)
                header = f"💬 {total_msgs} msgs · 🔊 {team_stats.format_time(total_voice)} total\n\n"
                embed.add_field(
                    name=f"{'🔒' if team.get('private', True) else '🌐'} {team['name']}",
                    value=header + "\n".join(board_lines),
                    inline=False)
            else:
                embed.add_field(
                    name=f"{'🔒' if team.get('private', True) else '🌐'} {team['name']}",
                    value="No activity yet. Start chatting and joining voice!",
                    inline=False)

        embed.set_footer(text="Score = messages + voice minutes")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Premium Shop", emoji="💎", style=discord.ButtonStyle.primary, row=1)
    async def open_pshop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick link to /pshop from team menu"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your menu!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(self.user_id)
        if not user:
            user = await UserProfile.create_user(self.user_id, interaction.user.name)

        from cogs.premium import PremiumShopView
        embed = discord.Embed(
            title="💎 Premium Shop",
            description=(
                f"Your pCredits: **{user.get('pcredits', 0)}**\n\n"
                "Buy team upgrades and premium features here!"),
            color=0x5865F2)
        view = PremiumShopView(self.user_id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        for key, item in PCREDIT_SHOP.items():
            cat = item.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((key, item))

        cat_names = {"team": "👥 Team Items", "ai": "🤖 AI Items", "profile": "🌟 Profile", "marketplace": "📢 Marketplace"}
        for cat, items in categories.items():
            cat_text = ""
            for key, item in items:
                emoji = item.get("emoji", "•")
                cat_text += f"{emoji} **{item['name']}** — {item['price']} pCredits\n{item['description']}\n\n"
            embed.add_field(
                name=cat_names.get(cat, cat.title()),
                value=cat_text.strip(),
                inline=False)

        await interaction.followup.send(
            embed=embed,
            view=PremiumShopView(self.user_id),
            ephemeral=True)


# ============================================================
# TEAM COG
# ============================================================

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="team_join", description="Join a team with an invite code")
    async def team_join(self, interaction: discord.Interaction, invite_code: str):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        from database import _memory_teams, db

        found_team = None
        for tid, team in _memory_teams.items():
            if team.get("invite_code", "").upper() == invite_code.strip().upper():
                found_team = team
                break

        if not found_team and db is not None:
            try:
                found_team = await db["teams"].find_one(
                    {"invite_code": invite_code.strip().upper()})
            except Exception:
                pass

        if not found_team:
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Invalid Code",
                description="No team found with that code.",
                color=discord.Color.red()),
                ephemeral=True)
            return

        team_id = found_team["_id"]
        members = found_team.get("members", [])
        max_members = found_team.get("max_members", 5)

        if interaction.user.id in members:
            await interaction.followup.send(embed=discord.Embed(
                title="Already a Member",
                description="You're already in this team!",
                color=BOT_COLOR),
                ephemeral=True)
            return

        if len(members) >= max_members:
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Team Full",
                description=f"Limit: {max_members} members.",
                color=discord.Color.red()),
                ephemeral=True)
            return

        # Check user team limit
        user_teams = await TeamData.get_user_teams(interaction.user.id)
        max_teams = user.get("max_teams", 3)
        if len(user_teams) >= max_teams:
            await interaction.followup.send(embed=discord.Embed(
                title="✗ Your Team Limit Reached",
                description=f"You can only be in **{max_teams}** team(s).\nBuy more slots in `/pshop`.",
                color=discord.Color.red()),
                ephemeral=True)
            return

        await TeamData.add_member(team_id, interaction.user.id)

        guild = interaction.guild
        if guild and found_team.get("category_id"):
            try:
                category = guild.get_channel(found_team["category_id"])
                if category:
                    await category.set_permissions(
                        interaction.user,
                        read_messages=True,
                        send_messages=True)
            except Exception as e:
                print(f"Error granting channel access: {e}")

        embed = discord.Embed(
            title="✓ Joined Team!",
            description=(
                f"Welcome to **{found_team['name']}**!\n\n"
                f"**Project:** {found_team.get('project', 'None')}\n"
                f"**Members:** {len(members) + 1}/{max_members}"),
            color=discord.Color.green())
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track messages in team channels"""
        if message.author.bot:
            return
        if not message.guild:
            return

        channel = message.channel
        if not hasattr(channel, 'category') or not channel.category:
            return

        for team_id, team in _memory_teams.items():
            if team.get("category_id") == channel.category.id:
                if message.author.id in team.get("members", []):
                    team_stats.add_message(team_id, message.author.id)
                break

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice time in team channels"""
        if member.bot:
            return

        # Left a voice channel
        if before.channel and hasattr(before.channel, 'category') and before.channel.category:
            for team_id, team in _memory_teams.items():
                if team.get("category_id") == before.channel.category.id:
                    if member.id in team.get("members", []):
                        team_stats.voice_leave(team_id, member.id)
                    break

        # Joined a voice channel
        if after.channel and hasattr(after.channel, 'category') and after.channel.category:
            for team_id, team in _memory_teams.items():
                if team.get("category_id") == after.channel.category.id:
                    if member.id in team.get("members", []):
                        team_stats.voice_join(team_id, member.id)
                    break


async def setup(bot):
    @bot.tree.command(name="team", description="Manage or create a team")
    async def team_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)

        view = TeamSelectionView(interaction.user.id)
        embed = discord.Embed(
            title="👥 Team Management",
            description=(
                "Create teams, collaborate on projects, and build together!\n\n"
                "**Teams are private by default.** Share your invite code to let others join.\n"
                "**Projects are optional** — add them whenever you're ready!"),
            color=BOT_COLOR)
        embed.add_field(
            name="Options",
            value=(
                "➕ **Create** — Start a new private team\n"
                "📊 **My Teams** — View and manage your teams\n"
                "🔍 **Browse** — Find public teams\n"
                "🏆 **Leaderboard** — Team activity rankings\n"
                "💎 **Premium Shop** — Buy team upgrades"),
            inline=False)
        embed.set_footer(text="Have an invite code? Use /team_join <code>")
        await interaction.followup.send(embed=embed, view=view)

    await bot.add_cog(TeamCog(bot))