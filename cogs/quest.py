import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR
from datetime import datetime

# ==================== QUEST DEFINITIONS ====================
QUEST_LIST = [
    {
        "quest_id": "Q001",
        "title": "First Steps",
        "description": "Send 10 messages in any channel",
        "emoji": "💬",
        "type": "message_count",
        "requirement": 10,
        "reward_xp": 50,
        "reward_credits": 100,
        "difficulty": "Easy"
    },
    {
        "quest_id": "Q002",
        "title": "Social Butterfly",
        "description": "Send 50 messages in any channel",
        "emoji": "🦋",
        "type": "message_count",
        "requirement": 50,
        "reward_xp": 150,
        "reward_credits": 300,
        "difficulty": "Medium"
    },
    {
        "quest_id": "Q003",
        "title": "Chatterbox",
        "description": "Send 200 messages in any channel",
        "emoji": "📢",
        "type": "message_count",
        "requirement": 200,
        "reward_xp": 500,
        "reward_credits": 750,
        "difficulty": "Hard"
    },
    {
        "quest_id": "Q004",
        "title": "Voice Rookie",
        "description": "Spend 10 minutes in voice channels",
        "emoji": "🎤",
        "type": "voice_minutes",
        "requirement": 10,
        "reward_xp": 75,
        "reward_credits": 150,
        "difficulty": "Easy"
    },
    {
        "quest_id": "Q005",
        "title": "Voice Veteran",
        "description": "Spend 60 minutes in voice channels",
        "emoji": "🎧",
        "type": "voice_minutes",
        "requirement": 60,
        "reward_xp": 300,
        "reward_credits": 500,
        "difficulty": "Medium"
    },
    {
        "quest_id": "Q006",
        "title": "Voice Legend",
        "description": "Spend 300 minutes in voice channels",
        "emoji": "🏆",
        "type": "voice_minutes",
        "requirement": 300,
        "reward_xp": 800,
        "reward_credits": 1200,
        "difficulty": "Hard"
    },
    {
        "quest_id": "Q007",
        "title": "First Sale",
        "description": "List 1 item on the marketplace",
        "emoji": "💰",
        "type": "sales_count",
        "requirement": 1,
        "reward_xp": 100,
        "reward_credits": 200,
        "difficulty": "Easy"
    },
    {
        "quest_id": "Q008",
        "title": "Merchant",
        "description": "List 5 items on the marketplace",
        "emoji": "🏪",
        "type": "sales_count",
        "requirement": 5,
        "reward_xp": 400,
        "reward_credits": 600,
        "difficulty": "Medium"
    },
    {
        "quest_id": "Q009",
        "title": "Tycoon",
        "description": "List 20 items on the marketplace",
        "emoji": "👑",
        "type": "sales_count",
        "requirement": 20,
        "reward_xp": 1000,
        "reward_credits": 2000,
        "difficulty": "Hard"
    },
    {
        "quest_id": "Q010",
        "title": "Helpful Hand",
        "description": "Give 3 reviews to other sellers",
        "emoji": "⭐",
        "type": "reviews_given",
        "requirement": 3,
        "reward_xp": 100,
        "reward_credits": 200,
        "difficulty": "Easy"
    },
    {
        "quest_id": "Q011",
        "title": "Level Up!",
        "description": "Reach level 5",
        "emoji": "🎯",
        "type": "level",
        "requirement": 5,
        "reward_xp": 200,
        "reward_credits": 400,
        "difficulty": "Medium"
    },
    {
        "quest_id": "Q012",
        "title": "Master Developer",
        "description": "Reach level 15",
        "emoji": "🔥",
        "type": "level",
        "requirement": 15,
        "reward_xp": 1000,
        "reward_credits": 2500,
        "difficulty": "Hard"
    },
    {
        "quest_id": "Q013",
        "title": "Reputation Builder",
        "description": "Earn 10 reputation points",
        "emoji": "🌟",
        "type": "reputation",
        "requirement": 10,
        "reward_xp": 150,
        "reward_credits": 300,
        "difficulty": "Medium"
    },
    {
        "quest_id": "Q014",
        "title": "Daily Grinder",
        "description": "Claim your daily reward 7 times",
        "emoji": "📅",
        "type": "daily_claims",
        "requirement": 7,
        "reward_xp": 200,
        "reward_credits": 350,
        "difficulty": "Easy"
    },
    {
        "quest_id": "Q015",
        "title": "Big Spender",
        "description": "Buy 3 items from the marketplace",
        "emoji": "🛒",
        "type": "purchases_count",
        "requirement": 3,
        "reward_xp": 150,
        "reward_credits": 250,
        "difficulty": "Medium"
    },
]

DIFFICULTY_EMOJIS = {
    "Easy": "🟢",
    "Medium": "🟡",
    "Hard": "🔴"
}


def get_quest_by_id(quest_id: str):
    """Find a quest by its ID"""
    quest_id = quest_id.strip().upper()
    for q in QUEST_LIST:
        if q["quest_id"] == quest_id:
            return q
    return None


def get_user_progress(user_data: dict, quest: dict) -> int:
    """Get user current progress toward a quest"""
    return user_data.get(quest["type"], 0)


def is_quest_complete(user_data: dict, quest: dict) -> bool:
    """Check if user meets the quest requirement"""
    return get_user_progress(user_data, quest) >= quest["requirement"]


# ==================== QUEST LIST VIEW ====================
class QuestListView(discord.ui.View):
    def __init__(self, user_id: int, bot):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.bot = bot
        self.page = 1
        self.per_page = 5
        self.filter_difficulty = None

    def get_filtered_quests(self):
        if self.filter_difficulty:
            return [q for q in QUEST_LIST if q["difficulty"] == self.filter_difficulty]
        return list(QUEST_LIST)

    @discord.ui.button(label="All", emoji="📋", style=discord.ButtonStyle.blurple, row=0)
    async def all_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        self.filter_difficulty = None
        self.page = 1
        await self.show_quests(interaction)

    @discord.ui.button(label="Easy", emoji="🟢", style=discord.ButtonStyle.success, row=0)
    async def easy_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        self.filter_difficulty = "Easy"
        self.page = 1
        await self.show_quests(interaction)

    @discord.ui.button(label="Medium", emoji="🟡", style=discord.ButtonStyle.secondary, row=0)
    async def medium_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        self.filter_difficulty = "Medium"
        self.page = 1
        await self.show_quests(interaction)

    @discord.ui.button(label="Hard", emoji="🔴", style=discord.ButtonStyle.danger, row=0)
    async def hard_quests(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        self.filter_difficulty = "Hard"
        self.page = 1
        await self.show_quests(interaction)

    @discord.ui.button(label="Claim Quest", emoji="🎁", style=discord.ButtonStyle.success, row=1)
    async def claim_quest_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return

        # Show claimable quests and ask for ID
        user_data = await UserProfile.get_user(self.user_id)
        if not user_data:
            user_data = await UserProfile.create_user(self.user_id, interaction.user.name)

        claimed = user_data.get('claimed_quests', [])
        ready = []
        for q in QUEST_LIST:
            if q["quest_id"] not in claimed and is_quest_complete(user_data, q):
                ready.append(q)

        if not ready:
            embed = discord.Embed(
                title="❌ No Quests Ready",
                description="You don't have any completed quests to claim.\n"
                            "Keep working on your progress!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        ready_text = ""
        for q in ready:
            ready_text += f"`{q['quest_id']}` - {q['emoji']} **{q['title']}** (💰 {q['reward_credits']} + ✨ {q['reward_xp']})\n"

        embed = discord.Embed(
            title="🎁 Claim a Quest Reward",
            description=f"**These quests are ready to claim:**\n\n{ready_text}\n"
                        f"**Send the Quest ID below** (e.g. `Q001`)\n"
                        f"⏱️ You have 30 seconds.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        def check(m):
            return m.author.id == self.user_id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            quest_id_input = msg.content.strip().upper()

            try:
                await msg.delete()
            except Exception:
                pass

            quest = get_quest_by_id(quest_id_input)
            if not quest:
                err = discord.Embed(
                    title="❌ Invalid Quest ID",
                    description=f"No quest found with ID `{quest_id_input}`.\nCheck your quest list and try again.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=err, ephemeral=True)
                return

            # Refresh user data
            user_data = await UserProfile.get_user(self.user_id)
            claimed = user_data.get('claimed_quests', [])

            if quest_id_input in claimed:
                err = discord.Embed(
                    title="⚠️ Already Claimed",
                    description=f"You already claimed **{quest['title']}**!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=err, ephemeral=True)
                return

            if not is_quest_complete(user_data, quest):
                progress = get_user_progress(user_data, quest)
                req = quest["requirement"]
                pct = int(progress / req * 100) if req > 0 else 0
                err = discord.Embed(
                    title="❌ Quest Not Complete",
                    description=f"**{quest['emoji']} {quest['title']}**\n\n"
                                f"Progress: **{progress}/{req}** ({pct}%)\n"
                                f"Keep going!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=err, ephemeral=True)
                return

            # Give rewards
            current_xp = user_data.get('xp', 0)
            current_credits = user_data.get('studio_credits', 0)
            current_level = user_data.get('level', 1)

            new_xp = current_xp + quest['reward_xp']
            new_credits = current_credits + quest['reward_credits']

            # Level up check
            new_level = current_level
            xp_needed = new_level * 250
            while new_xp >= xp_needed and new_level < 100:
                new_xp -= xp_needed
                new_level += 1
                xp_needed = new_level * 250

            # Rank
            if new_level >= 15:
                new_rank = "Master"
            elif new_level >= 10:
                new_rank = "Expert"
            elif new_level >= 5:
                new_rank = "Learner"
            else:
                new_rank = "Beginner"

            claimed.append(quest_id_input)

            await UserProfile.update_user(self.user_id, {
                "xp": new_xp,
                "studio_credits": new_credits,
                "level": new_level,
                "rank": new_rank,
                "claimed_quests": claimed
            })

            success = discord.Embed(
                title="🎉 Quest Reward Claimed!",
                description=f"**{quest['emoji']} {quest['title']}**",
                color=discord.Color.green()
            )
            success.add_field(name="XP Earned", value=f"✨ +{quest['reward_xp']}", inline=True)
            success.add_field(name="Credits Earned", value=f"💰 +{quest['reward_credits']}", inline=True)
            success.add_field(name="Balance", value=f"💰 {new_credits}", inline=True)

            if new_level > current_level:
                success.add_field(
                    name="🎯 LEVEL UP!",
                    value=f"Level {current_level} → **Level {new_level}**",
                    inline=False
                )
            if new_rank != user_data.get('rank', 'Beginner'):
                success.add_field(
                    name="👑 RANK UP!",
                    value=f"New Rank: **{new_rank}**",
                    inline=False
                )

            await interaction.followup.send(embed=success, ephemeral=True)

        except Exception:
            timeout = discord.Embed(
                title="⏱️ Timeout",
                description="You didn't send a Quest ID in time. Use `/quest` again.",
                color=discord.Color.red()
            )
            try:
                await interaction.followup.send(embed=timeout, ephemeral=True)
            except Exception:
                pass

    @discord.ui.button(label="My Progress", emoji="📊", style=discord.ButtonStyle.secondary, row=1)
    async def my_progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        user_data = await UserProfile.get_user(self.user_id)
        if not user_data:
            user_data = await UserProfile.create_user(self.user_id, interaction.user.name)

        claimed = user_data.get('claimed_quests', [])
        total = len(QUEST_LIST)
        completed_count = sum(1 for q in QUEST_LIST if is_quest_complete(user_data, q))
        claimed_count = len(claimed)
        unclaimed_count = sum(
            1 for q in QUEST_LIST
            if is_quest_complete(user_data, q) and q["quest_id"] not in claimed
        )

        embed = discord.Embed(
            title="📊 Your Quest Progress",
            description=f"**Completed:** {completed_count}/{total}\n"
                        f"**Claimed:** {claimed_count}/{total}\n"
                        f"**Unclaimed Rewards:** {unclaimed_count}",
            color=BOT_COLOR
        )

        # Unclaimed completed
        unclaimed_list = [
            q for q in QUEST_LIST
            if is_quest_complete(user_data, q) and q["quest_id"] not in claimed
        ]
        if unclaimed_list:
            val = ""
            for q in unclaimed_list[:5]:
                val += f"{q['emoji']} **{q['title']}** (`{q['quest_id']}`) - 💰 {q['reward_credits']} + ✨ {q['reward_xp']}\n"
            embed.add_field(name="🎁 Ready to Claim!", value=val, inline=False)

        # In progress
        in_progress = []
        for q in QUEST_LIST:
            if not is_quest_complete(user_data, q):
                prog = get_user_progress(user_data, q)
                req = q["requirement"]
                pct = int(prog / req * 100) if req > 0 else 0
                in_progress.append((q, prog, pct))

        if in_progress:
            in_progress.sort(key=lambda x: x[2], reverse=True)
            val = ""
            for q, prog, pct in in_progress[:5]:
                bar_f = int(pct / 10)
                bar_e = 10 - bar_f
                bar = "█" * bar_f + "░" * bar_e
                val += f"{q['emoji']} **{q['title']}** - {prog}/{q['requirement']} [{bar}] {pct}%\n"
            embed.add_field(name="🔄 In Progress (Top 5)", value=val, inline=False)

        # Stats summary
        embed.add_field(
            name="📈 Your Stats",
            value=f"💬 Messages: {user_data.get('message_count', 0)}\n"
                  f"🎤 Voice: {user_data.get('voice_minutes', 0)} min\n"
                  f"💰 Sales: {user_data.get('sales_count', 0)}\n"
                  f"🛒 Purchases: {user_data.get('purchases_count', 0)}\n"
                  f"⭐ Reviews: {user_data.get('reviews_given', 0)}\n"
                  f"📅 Dailies: {user_data.get('daily_claims', 0)}",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=2)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        if self.page > 1:
            self.page -= 1
            await self.show_quests(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, row=2)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return
        quests = self.get_filtered_quests()
        max_pages = max(1, (len(quests) + self.per_page - 1) // self.per_page)
        if self.page < max_pages:
            self.page += 1
            await self.show_quests(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Daily Reward", emoji="🎁", style=discord.ButtonStyle.blurple, row=2)
    async def daily_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your quest board!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(self.user_id)
        if not user:
            user = await UserProfile.create_user(self.user_id, interaction.user.name)

        last_daily = user.get('last_daily')
        now = datetime.utcnow()

        if last_daily:
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.fromisoformat(last_daily)
                except Exception:
                    last_daily = None

            if last_daily and (now - last_daily).total_seconds() < 86400:
                remaining = 86400 - (now - last_daily).total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"Come back in **{hours}h {minutes}m**!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        # Streak calc
        streak = user.get('daily_streak', 0)
        if last_daily:
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.fromisoformat(last_daily)
                except Exception:
                    last_daily = None
            if last_daily and (now - last_daily).total_seconds() < 172800:
                streak += 1
            else:
                streak = 1
        else:
            streak = 1

        bonus = min(streak, 7)
        credits_reward = 100 + (bonus * 25)
        xp_reward = 25 + (bonus * 10)

        current_credits = user.get('studio_credits', 0)
        current_xp = user.get('xp', 0)
        daily_claims = user.get('daily_claims', 0)
        current_level = user.get('level', 1)

        new_xp = current_xp + xp_reward
        new_level = current_level
        xp_needed = new_level * 250
        while new_xp >= xp_needed and new_level < 100:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = new_level * 250

        if new_level >= 15:
            new_rank = "Master"
        elif new_level >= 10:
            new_rank = "Expert"
        elif new_level >= 5:
            new_rank = "Learner"
        else:
            new_rank = "Beginner"

        await UserProfile.update_user(self.user_id, {
            "studio_credits": current_credits + credits_reward,
            "xp": new_xp,
            "level": new_level,
            "rank": new_rank,
            "last_daily": now.isoformat(),
            "daily_streak": streak,
            "daily_claims": daily_claims + 1
        })

        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            color=discord.Color.green()
        )
        embed.add_field(name="Credits", value=f"💰 +{credits_reward}", inline=True)
        embed.add_field(name="XP", value=f"✨ +{xp_reward}", inline=True)
        embed.add_field(name="Streak", value=f"🔥 {streak} day{'s' if streak != 1 else ''}", inline=True)
        embed.add_field(name="Balance", value=f"💰 {current_credits + credits_reward}", inline=True)

        if new_level > current_level:
            embed.add_field(
                name="🎯 LEVEL UP!",
                value=f"Level {current_level} → **Level {new_level}**",
                inline=False
            )

        if bonus < 7:
            embed.set_footer(text=f"Streak bonus: {bonus}x | Max at 7 days!")
        else:
            embed.set_footer(text="🔥 MAX STREAK BONUS!")

        await interaction.followup.send(embed=embed, ephemeral=True)

    async def show_quests(self, interaction: discord.Interaction):
        """Display the quest list page"""
        if not interaction.response.is_done():
            await interaction.response.defer()

        user_data = await UserProfile.get_user(self.user_id)
        if not user_data:
            await UserProfile.create_user(self.user_id, interaction.user.name)
            user_data = await UserProfile.get_user(self.user_id)

        claimed = user_data.get('claimed_quests', [])
        quests = self.get_filtered_quests()
        total = len(quests)
        max_pages = max(1, (total + self.per_page - 1) // self.per_page)

        if self.page > max_pages:
            self.page = max_pages
        if self.page < 1:
            self.page = 1

        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        page_quests = quests[start:end]

        filter_text = f" - {self.filter_difficulty}" if self.filter_difficulty else ""

        embed = discord.Embed(
            title=f"📜 Quests{filter_text}",
            description=f"**{total}** quests | Page **{self.page}/{max_pages}**\n"
                        f"Complete quests → Click **Claim Quest** → Type the ID\n",
            color=BOT_COLOR
        )

        if not page_quests:
            embed.add_field(name="No quests found", value="Try a different filter!", inline=False)
        else:
            for quest in page_quests:
                diff_emoji = DIFFICULTY_EMOJIS.get(quest["difficulty"], "⚪")
                progress = get_user_progress(user_data, quest)
                req = quest["requirement"]
                pct = min(100, int(progress / req * 100)) if req > 0 else 0

                if quest["quest_id"] in claimed:
                    status = "✅ CLAIMED"
                    bar = "█" * 10
                elif is_quest_complete(user_data, quest):
                    status = "🎁 READY TO CLAIM"
                    bar = "█" * 10
                else:
                    status = f"{progress}/{req} ({pct}%)"
                    bar_f = int(pct / 10)
                    bar_e = 10 - bar_f
                    bar = "█" * bar_f + "░" * bar_e

                embed.add_field(
                    name=f"{quest['emoji']} {quest['title']} | `{quest['quest_id']}` {diff_emoji}",
                    value=f"{quest['description']}\n"
                          f"[{bar}] {status}\n"
                          f"Rewards: ✨ {quest['reward_xp']} XP | 💰 {quest['reward_credits']} Credits",
                    inline=False
                )

        embed.set_footer(text="Click 'Claim Quest' → type Quest ID (e.g. Q001)")
        await interaction.edit_original_response(embed=embed, view=self)


# ==================== COG ====================
class QuestCog(commands.Cog):
    """Quest System"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="quest", description="View and claim quests")
    async def quest_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        view = QuestListView(interaction.user.id, self.bot)
        claimed = user.get('claimed_quests', [])
        completed = sum(1 for q in QUEST_LIST if is_quest_complete(user, q))
        unclaimed = sum(
            1 for q in QUEST_LIST
            if is_quest_complete(user, q) and q["quest_id"] not in claimed
        )

        embed = discord.Embed(
            title="📜 Quest Board",
            description=f"Complete quests to earn XP and Credits!\n\n"
                        f"✅ Completed: **{completed}/{len(QUEST_LIST)}**\n"
                        f"🎁 Unclaimed Rewards: **{unclaimed}**\n\n"
                        f"Use the buttons to browse, filter, and claim.",
            color=BOT_COLOR
        )

        if unclaimed > 0:
            embed.add_field(
                name="🎁 You have unclaimed rewards!",
                value="Click **Claim Quest** to collect them!",
                inline=False
            )

        embed.add_field(
            name="💡 How to Claim",
            value="1. Click **Claim Quest**\n"
                  "2. See which quests are ready\n"
                  "3. Type the Quest ID (e.g. `Q001`)\n"
                  "4. Get your rewards!",
            inline=False
        )

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        last_daily = user.get('last_daily')
        now = datetime.utcnow()

        if last_daily:
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.fromisoformat(last_daily)
                except Exception:
                    last_daily = None

            if last_daily and (now - last_daily).total_seconds() < 86400:
                remaining = 86400 - (now - last_daily).total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"Come back in **{hours}h {minutes}m**!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        streak = user.get('daily_streak', 0)
        if last_daily:
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.fromisoformat(last_daily)
                except Exception:
                    last_daily = None
            if last_daily and (now - last_daily).total_seconds() < 172800:
                streak += 1
            else:
                streak = 1
        else:
            streak = 1

        bonus = min(streak, 7)
        credits_reward = 100 + (bonus * 25)
        xp_reward = 25 + (bonus * 10)

        current_credits = user.get('studio_credits', 0)
        current_xp = user.get('xp', 0)
        daily_claims = user.get('daily_claims', 0)
        current_level = user.get('level', 1)

        new_xp = current_xp + xp_reward
        new_level = current_level
        xp_needed = new_level * 250
        while new_xp >= xp_needed and new_level < 100:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = new_level * 250

        if new_level >= 15:
            new_rank = "Master"
        elif new_level >= 10:
            new_rank = "Expert"
        elif new_level >= 5:
            new_rank = "Learner"
        else:
            new_rank = "Beginner"

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": current_credits + credits_reward,
            "xp": new_xp,
            "level": new_level,
            "rank": new_rank,
            "last_daily": now.isoformat(),
            "daily_streak": streak,
            "daily_claims": daily_claims + 1
        })

        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            color=discord.Color.green()
        )
        embed.add_field(name="Credits", value=f"💰 +{credits_reward}", inline=True)
        embed.add_field(name="XP", value=f"✨ +{xp_reward}", inline=True)
        embed.add_field(name="Streak", value=f"🔥 {streak} day{'s' if streak != 1 else ''}", inline=True)
        embed.add_field(name="Balance", value=f"💰 {current_credits + credits_reward}", inline=True)

        if new_level > current_level:
            embed.add_field(
                name="🎯 LEVEL UP!",
                value=f"Level {current_level} → **Level {new_level}**",
                inline=False
            )

        if bonus < 7:
            embed.set_footer(text=f"Streak bonus: {bonus}x | Max at 7 days!")
        else:
            embed.set_footer(text="🔥 MAX STREAK BONUS!")

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(QuestCog(bot))