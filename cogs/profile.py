import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, ROLES
from datetime import datetime
import random


# ============================================================
# RANK CONFIGURATION
# ============================================================

RANK_CONFIG = {
    "Beginner": {"emoji": "🥚", "color": 0x95A5A6, "min_level": 0, "next": "Learner"},
    "Learner": {"emoji": "🌱", "color": 0x2ECC71, "min_level": 5, "next": "Expert"},
    "Expert": {"emoji": "🔥", "color": 0xE67E22, "min_level": 15, "next": "Master"},
    "Master": {"emoji": "👑", "color": 0xF1C40F, "min_level": 30, "next": None},
}

LEVEL_THRESHOLDS = [0, 100, 250, 500, 800, 1200, 1700, 2300, 3000, 3800, 4700,
                    5700, 6800, 8000, 9300, 10700, 12200, 13800, 15500, 17300,
                    19200, 21200, 23300, 25500, 27800, 30200, 32700, 35300, 38000,
                    40800, 43700, 46700, 49800, 53000, 56300, 59700, 63200, 66800,
                    70500, 74300, 78200, 82200, 86300, 90500, 94800, 99200, 103700,
                    108300, 113000, 117800]


def get_xp_for_next_level(level: int) -> int:
    """Get XP needed for next level"""
    if level < len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[level]
    return int(LEVEL_THRESHOLDS[-1] * (1.1 ** (level - len(LEVEL_THRESHOLDS) + 1)))


def get_level_progress(xp: int, level: int) -> tuple:
    """Returns (current_xp_in_level, xp_needed_for_next, percentage)"""
    current_threshold = get_xp_for_next_level(level - 1) if level > 1 else 0
    next_threshold = get_xp_for_next_level(level)

    xp_in_level = xp - current_threshold
    xp_needed = next_threshold - current_threshold

    if xp_needed <= 0:
        return xp_in_level, 1, 100.0

    percentage = min((xp_in_level / xp_needed) * 100, 100.0)
    return xp_in_level, xp_needed, percentage


def build_progress_bar(percentage: float, length: int = 20, style: str = "main") -> str:
    """Build a visual progress bar"""
    styles = {
        "main": {"filled": "█", "partial": "▓", "empty": "░"},
        "slim": {"filled": "━", "partial": "╍", "empty": "┄"},
        "dots": {"filled": "●", "partial": "◐", "empty": "○"},
    }
    s = styles.get(style, styles["main"])
    filled = int((percentage / 100) * length)
    has_partial = percentage > 0 and filled < length

    bar = s["filled"] * filled
    if has_partial:
        bar += s["partial"]
        bar += s["empty"] * (length - filled - 1)
    else:
        bar += s["empty"] * (length - filled)

    return bar


def get_rank_emoji(rank: str) -> str:
    return RANK_CONFIG.get(rank, {}).get("emoji", "❓")


def get_rank_color(rank: str) -> int:
    return RANK_CONFIG.get(rank, {}).get("color", BOT_COLOR)


def format_number(n: int) -> str:
    """Format large numbers with K/M suffixes"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def get_activity_grade(messages: int, voice: int, reviews: int) -> tuple:
    """Calculate activity grade based on engagement"""
    score = messages + (voice * 2) + (reviews * 5)

    if score >= 5000:
        return "S+", "🌟", "Legendary contributor"
    elif score >= 2000:
        return "S", "⭐", "Outstanding activity"
    elif score >= 1000:
        return "A", "🔥", "Very active"
    elif score >= 500:
        return "B", "✅", "Active member"
    elif score >= 200:
        return "C", "📊", "Regular"
    elif score >= 50:
        return "D", "📉", "Casual"
    else:
        return "F", "💤", "Inactive"


# ============================================================
# PROFILE VIEW WITH TABS
# ============================================================

class ProfileView(discord.ui.View):
    """Profile viewing with tabbed navigation"""

    def __init__(self, user_id: int, target_user_id: int, target_user: discord.User):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.target_user_id = target_user_id
        self.target_user = target_user
        self.current_tab = "overview"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can navigate.", ephemeral=True)
            return False
        return True

    async def _get_user_data(self):
        return await UserProfile.get_user(self.target_user_id)

    @discord.ui.button(label="Overview", emoji="👤", style=discord.ButtonStyle.primary, row=0)
    async def overview_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self._get_user_data()
        if not user:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return

        embed = self._build_overview(user)
        self._update_active_button("overview")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stats", emoji="📊", style=discord.ButtonStyle.secondary, row=0)
    async def stats_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self._get_user_data()
        if not user:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return

        embed = self._build_stats(user)
        self._update_active_button("stats")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Economy", emoji="💰", style=discord.ButtonStyle.secondary, row=0)
    async def economy_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self._get_user_data()
        if not user:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return

        embed = self._build_economy(user)
        self._update_active_button("economy")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Rank", emoji="👑", style=discord.ButtonStyle.secondary, row=0)
    async def rank_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self._get_user_data()
        if not user:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return

        embed = self._build_rank(user)
        self._update_active_button("rank")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Portfolio", emoji="🎮", style=discord.ButtonStyle.secondary, row=0)
    async def portfolio_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self._get_user_data()
        if not user:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return

        embed = self._build_portfolio(user)
        self._update_active_button("portfolio")
        await interaction.response.edit_message(embed=embed, view=self)

    def _update_active_button(self, active_tab: str):
        """Highlight the active tab button"""
        tab_map = {
            "overview": 0,
            "stats": 1,
            "economy": 2,
            "rank": 3,
            "portfolio": 4,
        }
        for i, child in enumerate(self.children):
            if i < 5:  # Only first row buttons
                if i == tab_map.get(active_tab, 0):
                    child.style = discord.ButtonStyle.primary
                else:
                    child.style = discord.ButtonStyle.secondary
        self.current_tab = active_tab

    def _build_overview(self, user: dict) -> discord.Embed:
        """Main overview tab"""
        rank = user.get('rank', 'Beginner')
        level = user.get('level', 1)
        xp = user.get('xp', 0)
        reputation = user.get('reputation', 0)

        roles = user.get('roles', [])
        if isinstance(roles, list) and roles:
            role_display = " ".join(f"{ROLES.get(r, '❓')} {r}" for r in roles)
        else:
            role_display = str(user.get('role', 'None'))

        rank_emoji = get_rank_emoji(rank)

        # Level progress
        xp_in_level, xp_needed, progress_pct = get_level_progress(xp, level)
        progress_bar = build_progress_bar(progress_pct, 16)

        embed = discord.Embed(
            title=f"{rank_emoji} {user.get('username', 'Unknown')} — {rank}",
            color=get_rank_color(rank)
        )
        embed.set_thumbnail(url=self.target_user.display_avatar.url)

        # Level progress section
        embed.add_field(
            name=f"📊 Level {level}",
            value=f"```\n[{progress_bar}] {progress_pct:.1f}%\n XP: {format_number(xp_in_level)}/{format_number(xp_needed)}\n```",
            inline=False
        )

        # Quick stats row
        embed.add_field(name="⭐ Reputation", value=f"**{reputation}**", inline=True)
        embed.add_field(name="✨ Total XP", value=f"**{format_number(xp)}**", inline=True)
        embed.add_field(name="💬 Messages", value=f"**{format_number(user.get('message_count', 0))}**", inline=True)

        # Roles
        embed.add_field(name="🏷️ Roles", value=role_display or "None set", inline=False)

        # Activity grade
        grade, grade_emoji, grade_desc = get_activity_grade(
            user.get('message_count', 0),
            user.get('voice_minutes', 0),
            user.get('reviews_given', 0)
        )
        embed.add_field(
            name="📈 Activity Grade",
            value=f"{grade_emoji} **{grade}** — {grade_desc}",
            inline=False
        )

        # Member since
        created_at = user.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.utcnow()
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        days_active = (datetime.utcnow() - created_at).days
        embed.set_footer(text=f"Member since {created_at.strftime('%B %d, %Y')} · {days_active} days active")

        return embed

    def _build_stats(self, user: dict) -> discord.Embed:
        """Detailed stats tab"""
        rank = user.get('rank', 'Beginner')

        embed = discord.Embed(
            title=f"📊 Detailed Stats — {user.get('username', 'Unknown')}",
            color=get_rank_color(rank)
        )
        embed.set_thumbnail(url=self.target_user.display_avatar.url)

        level = user.get('level', 1)
        xp = user.get('xp', 0)
        messages = user.get('message_count', 0)
        voice = user.get('voice_minutes', 0)
        reputation = user.get('reputation', 0)
        reviews = user.get('reviews_given', 0)

        # XP Breakdown
        xp_in_level, xp_needed, progress_pct = get_level_progress(xp, level)
        bar = build_progress_bar(progress_pct, 20)

        embed.add_field(
            name="🎯 Level Progress",
            value=(
                f"```\nLevel {level} → Level {level + 1}\n"
                f"[{bar}] {progress_pct:.1f}%\n"
                f"XP: {format_number(xp_in_level)} / {format_number(xp_needed)}\n"
                f"Total XP: {format_number(xp)}\n```"
            ),
            inline=False
        )

        # Engagement stats
        embed.add_field(name="💬 Messages", value=f"**{messages:,}**", inline=True)
        embed.add_field(name="🎤 Voice", value=f"**{voice:,}** min", inline=True)
        embed.add_field(name="⭐ Reputation", value=f"**{reputation:,}**", inline=True)

        embed.add_field(name="📝 Reviews", value=f"**{reviews:,}**", inline=True)
        embed.add_field(name="📅 Experience", value=f"**{user.get('experience_months', 0)}** months", inline=True)
        embed.add_field(name="🏆 Rank", value=f"**{rank}**", inline=True)

        # Averages
        created_at = user.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.utcnow()
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        days = max((datetime.utcnow() - created_at).days, 1)

        embed.add_field(
            name="📈 Daily Averages",
            value=(
                f"💬 {messages / days:.1f} msgs/day\n"
                f"🎤 {voice / days:.1f} min/day\n"
                f"✨ {xp / days:.1f} XP/day"
            ),
            inline=False
        )

        # Activity grade
        grade, grade_emoji, grade_desc = get_activity_grade(messages, voice, reviews)
        embed.set_footer(text=f"Activity Grade: {grade_emoji} {grade} — {grade_desc}")

        return embed

    def _build_economy(self, user: dict) -> discord.Embed:
        """Economy/wealth tab"""
        rank = user.get('rank', 'Beginner')

        embed = discord.Embed(
            title=f"💰 Economy — {user.get('username', 'Unknown')}",
            color=get_rank_color(rank)
        )
        embed.set_thumbnail(url=self.target_user.display_avatar.url)

        credits = user.get('studio_credits', 0)
        pcredits = user.get('pcredits', 0)
        ai_credits = user.get('ai_credits', 0)
        total_value = (pcredits * 1000) + credits

        # Wealth display
        embed.add_field(
            name="💰 Studio Credits",
            value=f"```\n{credits:,}\n```",
            inline=True
        )
        embed.add_field(
            name="💎 pCredits",
            value=f"```\n{pcredits:,}\n```",
            inline=True
        )
        embed.add_field(
            name="🤖 AI Credits",
            value=f"```\n{ai_credits:,}\n```",
            inline=True
        )

        # Total value
        embed.add_field(
            name="📊 Total Value",
            value=f"**{total_value:,}** Credits equivalent\n*(pCredits × 1000 + Credits)*",
            inline=False
        )

        # Wealth tier
        if total_value >= 100_000:
            tier = "💎 Diamond"
        elif total_value >= 50_000:
            tier = "🥇 Gold"
        elif total_value >= 20_000:
            tier = "🥈 Silver"
        elif total_value >= 5_000:
            tier = "🥉 Bronze"
        else:
            tier = "🪨 Stone"

        embed.add_field(name="🏅 Wealth Tier", value=tier, inline=True)

        # Slots info
        max_teams = user.get('max_teams', 1)
        max_projects = user.get('max_projects', 2)
        embed.add_field(name="👥 Team Slots", value=f"**{max_teams}**", inline=True)
        embed.add_field(name="📁 Project Slots", value=f"**{max_projects}**", inline=True)

        embed.set_footer(text="Use /convert, /convert_ai, /pshop to manage your economy")

        return embed

    def _build_rank(self, user: dict) -> discord.Embed:
        """Rank progression tab"""
        rank = user.get('rank', 'Beginner')
        level = user.get('level', 1)

        embed = discord.Embed(
            title=f"👑 Rank Progression — {user.get('username', 'Unknown')}",
            color=get_rank_color(rank)
        )
        embed.set_thumbnail(url=self.target_user.display_avatar.url)

        # Current rank display
        rank_info = RANK_CONFIG.get(rank, RANK_CONFIG["Beginner"])
        embed.add_field(
            name="Current Rank",
            value=f"{rank_info['emoji']} **{rank}**",
            inline=True
        )
        embed.add_field(
            name="Level",
            value=f"**{level}**",
            inline=True
        )
        embed.add_field(
            name="Experience",
            value=f"**{user.get('experience_months', 0)}** months",
            inline=True
        )

        # Rank progression visual
        progression_lines = []
        for r_name, r_info in RANK_CONFIG.items():
            is_current = r_name == rank
            is_achieved = level >= r_info["min_level"]

            if is_current:
                marker = "▸"
                status = "◄ YOU ARE HERE"
            elif is_achieved:
                marker = "✓"
                status = "Achieved"
            else:
                marker = "○"
                status = f"Level {r_info['min_level']} required"

            progression_lines.append(
                f"{'**' if is_current else ''}"
                f"{marker} {r_info['emoji']} {r_name} (Lv.{r_info['min_level']}+) — {status}"
                f"{'**' if is_current else ''}"
            )

        embed.add_field(
            name="📈 Rank Ladder",
            value="\n".join(progression_lines),
            inline=False
        )

        # Next rank info
        next_rank = rank_info.get("next")
        if next_rank:
            next_info = RANK_CONFIG.get(next_rank, {})
            levels_needed = max(next_info.get("min_level", 0) - level, 0)

            if levels_needed > 0:
                next_bar = build_progress_bar(
                    (level / next_info["min_level"]) * 100, 15
                )
                embed.add_field(
                    name=f"🎯 Next: {next_info.get('emoji', '')} {next_rank}",
                    value=(
                        f"```\n[{next_bar}] {level}/{next_info['min_level']}\n"
                        f"{levels_needed} more levels needed\n```"
                    ),
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"🎯 Next Rank",
                    value=f"✅ You qualify for **{next_rank}**! Keep going!",
                    inline=False
                )
        else:
            embed.add_field(
                name="🏆 MAX RANK",
                value="You've reached the highest rank! 👑",
                inline=False
            )

        # Roles
        roles = user.get('roles', [])
        if isinstance(roles, list) and roles:
            role_display = " ".join(f"{ROLES.get(r, '❓')} {r}" for r in roles)
        else:
            role_display = str(user.get('role', 'None'))
        embed.add_field(name="🏷️ Roles", value=role_display, inline=False)

        return embed

    def _build_portfolio(self, user: dict) -> discord.Embed:
        """Portfolio tab"""
        rank = user.get('rank', 'Beginner')

        embed = discord.Embed(
            title=f"🎮 Portfolio — {user.get('username', 'Unknown')}",
            color=get_rank_color(rank)
        )
        embed.set_thumbnail(url=self.target_user.display_avatar.url)

        games = user.get('portfolio_games', [])

        if games:
            for i, game in enumerate(games):
                if isinstance(game, dict):
                    name = game.get('name', f'Game {i + 1}')
                    desc = game.get('description', 'No description')
                    link = game.get('link', '')
                    value = f"{desc}"
                    if link:
                        value += f"\n🔗 [Play]({link})"
                    embed.add_field(name=f"🎮 {name}", value=value, inline=False)
                else:
                    embed.add_field(name=f"🎮 {game}", value="Featured Game", inline=False)
        else:
            embed.description = (
                "📭 **No games in portfolio yet**\n\n"
                "Add games to showcase your work!\n"
                "Your portfolio is visible to everyone who views your profile."
            )

        embed.add_field(
            name="📊 Developer Stats",
            value=(
                f"📝 Reviews Given: **{user.get('reviews_given', 0)}**\n"
                f"📅 Experience: **{user.get('experience_months', 0)}** months\n"
                f"🏆 Rank: **{rank}**"
            ),
            inline=False
        )

        embed.set_footer(text=f"Portfolio of {user.get('username', 'Unknown')}")

        return embed


# ============================================================
# LEADERBOARD VIEWS
# ============================================================

class LeaderboardView(discord.ui.View):
    """Multi-tab leaderboard with pagination"""

    def __init__(self, user_id: int, bot):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.bot = bot
        self.current_tab = "xp"
        self.current_page = 0
        self.per_page = 10
        self.cached_data = {}

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can navigate.", ephemeral=True)
            return False
        return True

    async def _get_all_users(self):
        """Get all users sorted for different categories"""
        from database import _memory_users

        users = list(_memory_users.values()) if _memory_users else []
        return users

    def _sort_users(self, users: list, category: str) -> list:
        """Sort users by different criteria"""
        sort_keys = {
            "xp": lambda u: u.get('xp', 0),
            "level": lambda u: (u.get('level', 1), u.get('xp', 0)),
            "reputation": lambda u: u.get('reputation', 0),
            "credits": lambda u: u.get('studio_credits', 0),
            "wealth": lambda u: (u.get('pcredits', 0) * 1000) + u.get('studio_credits', 0),
            "messages": lambda u: u.get('message_count', 0),
            "voice": lambda u: u.get('voice_minutes', 0),
            "ai": lambda u: u.get('ai_credits', 0),
        }

        key = sort_keys.get(category, sort_keys["xp"])
        return sorted(users, key=key, reverse=True)

    async def _build_leaderboard_embed(self, category: str, page: int) -> discord.Embed:
        users = await self._get_all_users()
        sorted_users = self._sort_users(users, category)

        total_pages = max((len(sorted_users) - 1) // self.per_page + 1, 1)
        page = min(page, total_pages - 1)
        self.current_page = page

        start = page * self.per_page
        end = start + self.per_page
        page_users = sorted_users[start:end]

        # Category config
        cat_config = {
            "xp": {"title": "✨ XP Leaderboard", "emoji": "✨", "color": 0x5865F2},
            "level": {"title": "🎯 Level Leaderboard", "emoji": "🎯", "color": 0x57F287},
            "reputation": {"title": "⭐ Reputation Leaderboard", "emoji": "⭐", "color": 0xFEE75C},
            "credits": {"title": "💰 Credits Leaderboard", "emoji": "💰", "color": 0x2ECC71},
            "wealth": {"title": "💎 Total Wealth Leaderboard", "emoji": "💎", "color": 0xF1C40F},
            "messages": {"title": "💬 Messages Leaderboard", "emoji": "💬", "color": 0x3498DB},
            "voice": {"title": "🎤 Voice Activity Leaderboard", "emoji": "🎤", "color": 0x9B59B6},
            "ai": {"title": "🤖 AI Credits Leaderboard", "emoji": "🤖", "color": 0xE67E22},
        }

        config = cat_config.get(category, cat_config["xp"])

        embed = discord.Embed(
            title=config["title"],
            color=config["color"]
        )

        if not page_users:
            embed.description = "No users found!"
            embed.set_footer(text=f"Page {page + 1}/{total_pages}")
            return embed

        # Medals for top 3
        medals = ["👑", "💎", "🥇", "🥈", "🥉"]

        lines = []
        for i, user in enumerate(page_users):
            global_rank = start + i + 1

            if global_rank <= 3:
                medal = medals[global_rank - 1]
            elif global_rank <= 5:
                medal = medals[global_rank - 1]
            else:
                medal = f"`{global_rank}.`"

            name = user.get('username', 'Unknown')
            rank = user.get('rank', 'Beginner')
            rank_emoji = get_rank_emoji(rank)

            # Value based on category
            if category == "xp":
                value = f"✨ **{format_number(user.get('xp', 0))}** XP · Lv.{user.get('level', 1)}"
            elif category == "level":
                xp_in, xp_need, pct = get_level_progress(user.get('xp', 0), user.get('level', 1))
                mini_bar = build_progress_bar(pct, 8, "slim")
                value = f"🎯 **Lv.{user.get('level', 1)}** [{mini_bar}] {pct:.0f}%"
            elif category == "reputation":
                value = f"⭐ **{user.get('reputation', 0):,}** rep"
            elif category == "credits":
                value = f"💰 **{user.get('studio_credits', 0):,}** credits"
            elif category == "wealth":
                total = (user.get('pcredits', 0) * 1000) + user.get('studio_credits', 0)
                value = f"💎 **{format_number(total)}** · 💰{format_number(user.get('studio_credits', 0))} · 💎{user.get('pcredits', 0)}"
            elif category == "messages":
                value = f"💬 **{user.get('message_count', 0):,}** messages"
            elif category == "voice":
                mins = user.get('voice_minutes', 0)
                hours = mins // 60
                remaining_mins = mins % 60
                value = f"🎤 **{hours}h {remaining_mins}m** ({mins:,} min)"
            elif category == "ai":
                value = f"🤖 **{user.get('ai_credits', 0):,}** AI credits"
            else:
                value = f"✨ {format_number(user.get('xp', 0))} XP"

            lines.append(f"{medal} {rank_emoji} **{name}**\n　{value}")

        embed.description = "\n\n".join(lines)

        # Find requesting user's position
        requesting_user_rank = None
        for i, u in enumerate(sorted_users):
            if u.get('_id') == self.user_id:
                requesting_user_rank = i + 1
                break

        footer_parts = [f"Page {page + 1}/{total_pages}", f"{len(sorted_users)} developers"]
        if requesting_user_rank:
            footer_parts.append(f"Your rank: #{requesting_user_rank}")

        embed.set_footer(text=" · ".join(footer_parts))

        return embed

    # ---- Category buttons (row 0) ----
    @discord.ui.button(label="XP", emoji="✨", style=discord.ButtonStyle.primary, row=0)
    async def xp_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "xp"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("xp", 0)
        self._highlight_tab("xp")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Level", emoji="🎯", style=discord.ButtonStyle.secondary, row=0)
    async def level_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "level"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("level", 0)
        self._highlight_tab("level")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Rep", emoji="⭐", style=discord.ButtonStyle.secondary, row=0)
    async def rep_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "reputation"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("reputation", 0)
        self._highlight_tab("reputation")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Wealth", emoji="💎", style=discord.ButtonStyle.secondary, row=0)
    async def wealth_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "wealth"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("wealth", 0)
        self._highlight_tab("wealth")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Messages", emoji="💬", style=discord.ButtonStyle.secondary, row=0)
    async def messages_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "messages"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("messages", 0)
        self._highlight_tab("messages")
        await interaction.response.edit_message(embed=embed, view=self)

    # ---- Extra categories (row 1) ----
    @discord.ui.button(label="Voice", emoji="🎤", style=discord.ButtonStyle.secondary, row=1)
    async def voice_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "voice"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("voice", 0)
        self._highlight_tab("voice")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="AI", emoji="🤖", style=discord.ButtonStyle.secondary, row=1)
    async def ai_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "ai"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("ai", 0)
        self._highlight_tab("ai")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Credits", emoji="💰", style=discord.ButtonStyle.secondary, row=1)
    async def credits_tab(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_tab = "credits"
        self.current_page = 0
        embed = await self._build_leaderboard_embed("credits", 0)
        self._highlight_tab("credits")
        await interaction.response.edit_message(embed=embed, view=self)

    # ---- Pagination (row 2) ----
    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, row=2)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        embed = await self._build_leaderboard_embed(self.current_tab, self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, row=2)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        embed = await self._build_leaderboard_embed(self.current_tab, self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

    def _highlight_tab(self, active: str):
        """Highlight the active leaderboard tab"""
        tab_map = {
            "xp": (0, 0), "level": (0, 1), "reputation": (0, 2),
            "wealth": (0, 3), "messages": (0, 4),
            "voice": (1, 0), "ai": (1, 1), "credits": (1, 2),
        }

        for child in self.children:
            if hasattr(child, 'row') and child.row in (0, 1):
                child.style = discord.ButtonStyle.secondary

        target = tab_map.get(active)
        if target:
            row, idx = target
            count = 0
            for child in self.children:
                if hasattr(child, 'row') and child.row == row:
                    if count == idx:
                        child.style = discord.ButtonStyle.primary
                        break
                    count += 1


# ============================================================
# PROFILE COG
# ============================================================

class ProfileCog(commands.Cog):
    """Profile and Stats Commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your or someone's profile")
    @app_commands.describe(user="The user to view (leave empty for yourself)")
    async def profile_cmd(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        target_user = await UserProfile.get_user(target.id)

        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)

        view = ProfileView(interaction.user.id, target.id, target)
        embed = view._build_overview(target_user)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="leaderboard", description="View the studio leaderboard")
    async def leaderboard_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()

        view = LeaderboardView(interaction.user.id, self.bot)
        embed = await view._build_leaderboard_embed("xp", 0)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="myrank", description="Check your current rank and progression")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def rank_cmd(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        target_user = await UserProfile.get_user(target.id)

        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)

        view = ProfileView(interaction.user.id, target.id, target)
        embed = view._build_rank(target_user)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="mystats", description="View detailed stats")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def stats_cmd(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        target_user = await UserProfile.get_user(target.id)

        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)

        view = ProfileView(interaction.user.id, target.id, target)
        embed = view._build_stats(target_user)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="wallet", description="View your economy and wealth")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def economy_cmd(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        target_user = await UserProfile.get_user(target.id)

        if not target_user:
            await UserProfile.create_user(target.id, target.name)
            target_user = await UserProfile.get_user(target.id)

        view = ProfileView(interaction.user.id, target.id, target)
        embed = view._build_economy(target_user)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="compare", description="Compare your profile with another user")
    @app_commands.describe(user="User to compare with")
    async def compare_cmd(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()

        if user.id == interaction.user.id:
            await interaction.followup.send("❌ Can't compare with yourself!")
            return

        if user.bot:
            await interaction.followup.send("❌ Can't compare with a bot!")
            return

        user1 = await UserProfile.get_user(interaction.user.id)
        if not user1:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user1 = await UserProfile.get_user(interaction.user.id)

        user2 = await UserProfile.get_user(user.id)
        if not user2:
            await interaction.followup.send(f"❌ **{user.display_name}** doesn't have a profile yet!")
            return

        embed = discord.Embed(
            title=f"⚔️ Profile Comparison",
            description=f"**{interaction.user.display_name}** vs **{user.display_name}**",
            color=BOT_COLOR
        )

        # Stats to compare
        comparisons = [
            ("🎯 Level", "level", 1),
            ("✨ XP", "xp", 0),
            ("⭐ Reputation", "reputation", 0),
            ("💬 Messages", "message_count", 0),
            ("🎤 Voice (min)", "voice_minutes", 0),
            ("💰 Credits", "studio_credits", 0),
            ("💎 pCredits", "pcredits", 0),
            ("🤖 AI Credits", "ai_credits", 0),
            ("📝 Reviews", "reviews_given", 0),
        ]

        u1_wins = 0
        u2_wins = 0

        for label, key, default in comparisons:
            v1 = user1.get(key, default)
            v2 = user2.get(key, default)

            if v1 > v2:
                arrow = "◄ 🟢"
                u1_wins += 1
            elif v2 > v1:
                arrow = "🟢 ►"
                u2_wins += 1
            else:
                arrow = "🟰"

            bar_total = max(v1 + v2, 1)
            v1_pct = (v1 / bar_total) * 100
            v1_bar = build_progress_bar(v1_pct, 10, "slim")

            embed.add_field(
                name=label,
                value=f"**{format_number(v1)}** [{v1_bar}] **{format_number(v2)}** {arrow}",
                inline=False
            )

        # Winner
        if u1_wins > u2_wins:
            winner = f"🏆 **{interaction.user.display_name}** leads {u1_wins}-{u2_wins}!"
        elif u2_wins > u1_wins:
            winner = f"🏆 **{user.display_name}** leads {u2_wins}-{u1_wins}!"
        else:
            winner = f"🤝 **It's a tie!** {u1_wins}-{u2_wins}"

        embed.add_field(name="─────────────────────", value=winner, inline=False)

        # Rank comparison
        r1 = user1.get('rank', 'Beginner')
        r2 = user2.get('rank', 'Beginner')
        embed.set_footer(
            text=f"{interaction.user.display_name}: {get_rank_emoji(r1)} {r1} | {user.display_name}: {get_rank_emoji(r2)} {r2}"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))