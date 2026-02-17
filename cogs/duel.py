# cogs/duel.py - PART 2 (REPLACE EVERYTHING IN duel.py)

import asyncio
import random
import time
import string
import discord
from discord import app_commands, ui
from discord.ext import commands
from database import UserProfile, DuelData, ActiveDuelData

from cogs.fun import (
    FALLBACK_QUESTIONS,
    generate_ai_duel_question,
    TRIVIA_CATEGORIES,
    TRIVIA_DIFFICULTIES,
)


# ===== CONSTANTS =====
DUEL_MODES = {
    "classic": {"name": "Classic", "emoji": "📝", "desc": "Answer trivia questions", "time": 15},
    "speed": {"name": "Speed Round", "emoji": "⚡", "desc": "5 seconds per question!", "time": 5},
    "expert": {"name": "Expert Only", "emoji": "🧠", "desc": "Only expert questions", "time": 20},
}

TRASH_TALKS = [
    {"emoji": "😏", "text": "Too easy!"},
    {"emoji": "😨", "text": "I'm nervous..."},
    {"emoji": "🤔", "text": "Hmm..."},
    {"emoji": "😎", "text": "I got this!"},
    {"emoji": "🥶", "text": "Cold blooded!"},
    {"emoji": "💀", "text": "You're done!"},
]

POWERUP_INFO = {
    "shield": {"emoji": "🛡️", "name": "Shield", "desc": "Lose only half bet if wrong", "price": 200},
    "extra_time": {"emoji": "⏱️", "name": "Extra Time", "desc": "+5 seconds to answer", "price": 150},
    "peek": {"emoji": "👀", "name": "Peek", "desc": "Remove 1 wrong answer", "price": 250},
    "sabotage": {"emoji": "💣", "name": "Sabotage", "desc": "Opponent loses 5 seconds", "price": 300},
    "reroll": {"emoji": "🔄", "name": "Reroll", "desc": "Get a different question", "price": 350},
}

ARENA_FRAMES = [
    "\n\n\n         ⚔️\n\n\n",
    "\n\n      ⚔️ ⚔️ ⚔️\n\n\n\n",
    "\n   ⚔️ ⚔️ ⚔️ ⚔️ ⚔️\n\n\n\n\n",
    "\n⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️\n\n      CODE DUEL\n\n\n",
    "\n⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️\n\n      CODE DUEL.\n\n\n",
    "\n⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️\n\n      CODE DUEL..\n\n\n",
    "\n⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️ ⚔️\n\n      CODE DUEL...\n\n\n",
]
ARENA_SPEEDS = [0.4, 0.3, 0.3, 0.4, 0.4, 0.4, 0.5]

ROUND_FRAMES = [
    "\n\n      ━━━━━━━━━━━━\n\n       ROUND {n}.\n\n      ━━━━━━━━━━━━\n",
    "\n\n      ━━━━━━━━━━━━\n\n       ROUND {n}..\n\n      ━━━━━━━━━━━━\n",
    "\n\n      ━━━━━━━━━━━━\n\n       ROUND {n}...\n\n      ━━━━━━━━━━━━\n",
    "\n\n      ━━━━━━━━━━━━\n\n        FIGHT!\n\n      ━━━━━━━━━━━━\n",
]
ROUND_SPEEDS = [0.5, 0.4, 0.4, 0.6]


def generate_duel_id():
    return "DUEL-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


def get_question(mode, used_questions=None):
    if used_questions is None:
        used_questions = []
    available = []
    for q in FALLBACK_QUESTIONS:
        if q["q"] in used_questions:
            continue
        if mode == "speed" and q.get("difficulty") in ["easy", "medium"]:
            available.append(q)
        elif mode == "expert" and q.get("difficulty") in ["hard", "expert"]:
            available.append(q)
        elif mode == "classic":
            available.append(q)
    if not available:
        available = [q for q in FALLBACK_QUESTIONS if q["q"] not in used_questions]
    if not available:
        available = list(FALLBACK_QUESTIONS)
    return random.choice(available)


def build_score_bar(p1_score, p2_score, p1_name, p2_name):
    p1_dots = "🔴" * p1_score + "⚫" * (2 - p1_score)
    p2_dots = "🔵" * p2_score + "⚫" * (2 - p2_score)
    return f"**{p1_name}** {p1_dots} vs {p2_dots} **{p2_name}**\nScore: **{p1_score}** - **{p2_score}** (Best of 3)"


async def apply_powerup(powerup, question, p1_id, p2_id, user_id):
    result = {"time_bonus": 0, "time_penalty_opponent": 0, "peek_removes": None, "shield_active": False, "reroll": False, "announcement": None}
    if not powerup:
        return result
    user_name = f"<@{user_id}>"
    if powerup == "shield":
        result["shield_active"] = True
        result["announcement"] = f"🛡️ {user_name} activated **Shield**!"
    elif powerup == "extra_time":
        result["time_bonus"] = 5
        result["announcement"] = f"⏱️ {user_name} activated **Extra Time**! +5s!"
    elif powerup == "peek":
        correct = question["correct"]
        wrong = [i for i in range(len(question["options"])) if i != correct]
        result["peek_removes"] = [random.choice(wrong)]
        result["announcement"] = f"👀 {user_name} activated **Peek**!"
    elif powerup == "sabotage":
        result["time_penalty_opponent"] = 5
        result["announcement"] = f"💣 {user_name} activated **Sabotage**! -5s opponent!"
    elif powerup == "reroll":
        result["reroll"] = True
        result["announcement"] = f"🔄 {user_name} activated **Reroll**!"
    return result


async def announce_streak(bot, guild, winner_id, streak):
    channel_id = await DuelData.get_streak_channel(guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if not channel:
        return
    streak_emojis = {10: "🔥", 30: "⚡", 50: "🌟", 100: "👑", 500: "💎"}
    emoji = streak_emojis.get(streak, "🔥")
    user = await UserProfile.get_user(winner_id)
    rank = user.get("duel_rank", "Unknown") if user else "Unknown"
    embed = discord.Embed(
        title=f"{emoji} STREAK MILESTONE!",
        description=f"<@{winner_id}> reached a **{streak}x** duel win streak!\nRank: **{rank}**",
        color=0xF1C40F
    )
    if streak >= 100:
        embed.color = 0xFF0000
        embed.description += "\n\n🏆 **ABSOLUTE LEGEND!**"
    elif streak >= 50:
        embed.color = 0xE67E22
        embed.description += "\n\n👑 **UNSTOPPABLE FORCE!**"
    embed.timestamp = discord.utils.utcnow()
    try:
        await channel.send(embed=embed)
    except Exception:
        pass


async def play_arena_animation(msg, p1_name, p2_name, p1_stats, p2_stats, bet):
    for i, frame in enumerate(ARENA_FRAMES):
        embed = discord.Embed(title="⚔️ CODE DUEL", description=frame, color=0xE74C3C)
        try:
            await msg.edit(embed=embed)
        except Exception:
            pass
        await asyncio.sleep(ARENA_SPEEDS[i])
    stats_embed = discord.Embed(title="⚔️ CODE DUEL — VS", color=0xE74C3C)
    p1_text = f"```\nRank : {p1_stats['rank_emoji']} {p1_stats['rank']}\nWins : {p1_stats['wins']}\nRate : {p1_stats['win_rate']:.0f}%\n🔥   : {p1_stats['streak']}x\n```"
    p2_text = f"```\nRank : {p2_stats['rank_emoji']} {p2_stats['rank']}\nWins : {p2_stats['wins']}\nRate : {p2_stats['win_rate']:.0f}%\n🔥   : {p2_stats['streak']}x\n```"
    stats_embed.add_field(name=f"🔴 {p1_name}", value=p1_text, inline=True)
    stats_embed.add_field(name="⚔️", value="\n\n**VS**", inline=True)
    stats_embed.add_field(name=f"🔵 {p2_name}", value=p2_text, inline=True)
    stats_embed.add_field(name="💰 Bet", value=f"**{bet:,}** credits", inline=True)
    stats_embed.set_footer(text="Best of 3 • Choose mode below!")
    await msg.edit(embed=stats_embed)
    await asyncio.sleep(2)


async def play_round_animation(msg, round_num):
    for i, frame in enumerate(ROUND_FRAMES):
        formatted = frame.replace("{n}", str(round_num))
        embed = discord.Embed(title=f"⚔️ ROUND {round_num}", description=formatted, color=0xE74C3C)
        try:
            await msg.edit(embed=embed)
        except Exception:
            pass
        await asyncio.sleep(ROUND_SPEEDS[i])


# ===== VIEWS =====

class DuelAcceptView(ui.View):
    def __init__(self, challenger_id, opponent_id, bet):
        super().__init__(timeout=60)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.bet = bet
        self.accepted = None

    @ui.button(label="Accept ⚔️", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
            return
        self.accepted = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Decline ❌", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
            return
        self.accepted = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


class ModeSelectView(ui.View):
    def __init__(self, challenger_id, opponent_id):
        super().__init__(timeout=30)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.mode = None
        self.votes = {}

    @ui.button(label="📝 Classic", style=discord.ButtonStyle.blurple)
    async def classic(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, "classic")

    @ui.button(label="⚡ Speed", style=discord.ButtonStyle.red)
    async def speed(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, "speed")

    @ui.button(label="🧠 Expert", style=discord.ButtonStyle.green)
    async def expert(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, "expert")

    async def handle_vote(self, interaction, mode):
        uid = interaction.user.id
        if uid != self.challenger_id and uid != self.opponent_id:
            await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
            return
        self.votes[uid] = mode
        if len(self.votes) >= 2:
            modes = list(self.votes.values())
            self.mode = modes[0] if modes[0] == modes[1] else random.choice(modes)
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()
        else:
            await interaction.response.send_message(f"✅ Voted **{DUEL_MODES[mode]['emoji']} {DUEL_MODES[mode]['name']}**! Waiting...", ephemeral=True)


class TrashTalkView(ui.View):
    def __init__(self, challenger_id, opponent_id, channel):
        super().__init__(timeout=10)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.channel = channel
        self.talks = {}
        for i, talk in enumerate(TRASH_TALKS):
            btn = ui.Button(label=talk["text"], emoji=talk["emoji"], style=discord.ButtonStyle.secondary, custom_id=f"trash_{i}", row=i // 3)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid != self.challenger_id and uid != self.opponent_id:
                await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
                return
            if uid in self.talks:
                await interaction.response.send_message("❌ Already sent one!", ephemeral=True)
                return
            self.talks[uid] = index
            talk = TRASH_TALKS[index]
            await self.channel.send(f"💬 **{interaction.user.display_name}:** {talk['emoji']} *\"{talk['text']}\"*")
            await interaction.response.defer()
        return callback


class DuelAnswerView(ui.View):
    def __init__(self, question, p1_id, p2_id, time_limit, peek_removes=None):
        super().__init__(timeout=time_limit + 2)
        self.question = question
        self.p1_id = p1_id
        self.p2_id = p2_id
        self.answers = {}
        self.start_time = time.time()
        labels = ["A", "B", "C", "D"]
        colors = [discord.ButtonStyle.blurple, discord.ButtonStyle.green, discord.ButtonStyle.red, discord.ButtonStyle.secondary]
        for i, option in enumerate(question["options"]):
            if peek_removes and i in peek_removes:
                btn = ui.Button(label=f"{labels[i]}: ❌", style=discord.ButtonStyle.secondary, disabled=True, custom_id=f"ans_{i}")
            else:
                btn = ui.Button(label=f"{labels[i]}: {option[:40]}", style=colors[i], custom_id=f"ans_{i}")
            btn.callback = self.make_answer_callback(i)
            self.add_item(btn)

    def make_answer_callback(self, index):
        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid != self.p1_id and uid != self.p2_id:
                await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
                return
            if uid in self.answers:
                await interaction.response.send_message("❌ Already answered!", ephemeral=True)
                return
            elapsed = time.time() - self.start_time
            self.answers[uid] = {"choice": index, "correct": index == self.question["correct"], "time": round(elapsed, 2)}
            await interaction.response.send_message(f"✅ Answered in **{elapsed:.1f}s**!", ephemeral=True)
            if len(self.answers) >= 2:
                for item in self.children:
                    item.disabled = True
                try:
                    await interaction.message.edit(view=self)
                except Exception:
                    pass
                self.stop()
        return callback


class PowerupSelectView(ui.View):
    def __init__(self, user_id, user_powerups):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.selected = None
        for name, info in POWERUP_INFO.items():
            count = user_powerups.get(name, 0)
            btn = ui.Button(label=f"{info['name']} ({count})", emoji=info["emoji"], style=discord.ButtonStyle.green if count > 0 else discord.ButtonStyle.secondary, disabled=count <= 0, custom_id=f"pw_{name}")
            btn.callback = self.make_callback(name)
            self.add_item(btn)
        skip_btn = ui.Button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.red, custom_id="pw_skip")
        skip_btn.callback = self.skip_callback
        self.add_item(skip_btn)

    def make_callback(self, powerup_name):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not yours!", ephemeral=True)
                return
            used = await DuelData.use_powerup(self.user_id, powerup_name)
            if not used:
                await interaction.response.send_message("❌ No uses left!", ephemeral=True)
                return
            self.selected = powerup_name
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()
        return callback

    async def skip_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not yours!", ephemeral=True)
            return
        self.selected = None
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


class SpectatorView(ui.View):
    def __init__(self, p1_id, p2_id):
        super().__init__(timeout=120)
        self.p1_id = p1_id
        self.p2_id = p2_id
        self.bets = {}

    @ui.button(label="Bet Player 1", emoji="1️⃣", style=discord.ButtonStyle.blurple)
    async def bet_p1(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_bet(interaction, self.p1_id)

    @ui.button(label="Bet Player 2", emoji="2️⃣", style=discord.ButtonStyle.red)
    async def bet_p2(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_bet(interaction, self.p2_id)

    async def handle_bet(self, interaction, pick_id):
        uid = interaction.user.id
        if uid == self.p1_id or uid == self.p2_id:
            await interaction.response.send_message("❌ Players can't spectate bet!", ephemeral=True)
            return
        if uid in self.bets:
            await interaction.response.send_message("❌ Already picked!", ephemeral=True)
            return
        self.bets[uid] = pick_id
        await interaction.response.send_message(f"✅ Betting on <@{pick_id}>!", ephemeral=True)

    def get_results(self, winner_id):
        correct = [uid for uid, pick in self.bets.items() if pick == winner_id]
        wrong = [uid for uid, pick in self.bets.items() if pick != winner_id]
        return correct, wrong
# cogs/duel.py - PART 3

class DuelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}

    async def create_duel_channel(self, guild, p1, p2, duel_id):
        """Create a private channel for the duel"""
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
            p1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            p2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        # Find or create duel category
        category = discord.utils.get(guild.categories, name="⚔️ Duels")
        if not category:
            try:
                category = await guild.create_category(
                    "⚔️ Duels",
                    overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False)}
                )
            except Exception:
                category = None

        channel_name = f"duel-{p1.display_name}-vs-{p2.display_name}".lower().replace(" ", "-")[:50]

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"⚔️ Duel {duel_id} | {p1.display_name} vs {p2.display_name}"
            )
            return channel
        except Exception as e:
            print(f"Failed to create duel channel: {e}")
            return None

    async def delete_duel_channel(self, channel, delay=30):
        """Delete duel channel after delay"""
        if not channel:
            return
        try:
            await channel.send(f"🗑️ This channel will be deleted in **{delay}** seconds...")
            await asyncio.sleep(delay)
            await channel.delete(reason="Duel ended")
        except Exception:
            pass

    async def add_spectator_to_channel(self, channel, user):
        """Give a spectator view access to duel channel"""
        if not channel:
            return False
        try:
            await channel.set_permissions(
                user,
                view_channel=True,
                send_messages=False
            )
            return True
        except Exception:
            return False

    @app_commands.command(name="code-duel", description="⚔️ Challenge someone to a Best of 3 duel!")
    @app_commands.describe(opponent="Who to challenge", bet="Credits to bet (50-10000)")
    async def code_duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int = 100):
        await interaction.response.defer()

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.followup.send("❌ Can't duel bots or yourself!")
            return

        if bet < 50 or bet > 10000:
            await interaction.followup.send("❌ Bet must be **50 - 10,000** credits!")
            return

        duel_key = tuple(sorted([interaction.user.id, opponent.id]))
        if duel_key in self.active_duels:
            await interaction.followup.send("❌ Already in a duel!")
            return

        p1 = await UserProfile.get_user(interaction.user.id)
        if not p1:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            p1 = await UserProfile.get_user(interaction.user.id)

        p2 = await UserProfile.get_user(opponent.id)
        if not p2:
            await UserProfile.create_user(opponent.id, opponent.name)
            p2 = await UserProfile.get_user(opponent.id)

        if p1.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ You only have **{p1.get('studio_credits', 0):,}** credits!")
            return

        if p2.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ {opponent.display_name} only has **{p2.get('studio_credits', 0):,}** credits!")
            return

        # Challenge accept
        accept_embed = discord.Embed(
            title="⚔️ DUEL CHALLENGE!",
            description=(
                f"**{interaction.user.display_name}** challenges **{opponent.display_name}**!\n\n"
                f"💰 **Bet:** {bet:,} credits\n"
                f"🎮 **Format:** Best of 3\n"
                f"⚡ **Powerups:** Enabled\n"
                f"📺 **Spectating:** Enabled\n\n"
                f"{opponent.mention}, do you accept?"
            ),
            color=0xE74C3C
        )
        accept_view = DuelAcceptView(interaction.user.id, opponent.id, bet)
        await interaction.followup.send(embed=accept_embed, view=accept_view)
        await accept_view.wait()

        if not accept_view.accepted:
            expire_embed = discord.Embed(title="⚔️ Duel Cancelled", description="Challenge was declined or expired.", color=0x95A5A6)
            try:
                await interaction.edit_original_response(embed=expire_embed, view=None)
            except Exception:
                pass
            return

        # Re-verify credits
        p1 = await UserProfile.get_user(interaction.user.id)
        p2 = await UserProfile.get_user(opponent.id)
        if p1.get("studio_credits", 0) < bet or p2.get("studio_credits", 0) < bet:
            await interaction.channel.send("❌ Not enough credits! Duel cancelled.")
            return

        # Generate duel ID
        duel_id = generate_duel_id()

        # Create private duel channel
        duel_channel = await self.create_duel_channel(interaction.guild, interaction.user, opponent, duel_id)
        if not duel_channel:
            await interaction.channel.send("❌ Failed to create duel channel!")
            return

        # Register active duel
        await ActiveDuelData.create_active_duel(
            duel_id, interaction.user.id, opponent.id,
            bet, duel_channel.id, interaction.guild.id
        )
        await ActiveDuelData.update_active_duel(duel_id, {
            "p1_name": interaction.user.display_name,
            "p2_name": opponent.display_name
        })

        self.active_duels[duel_key] = duel_id

        # Announce in original channel
        announce_embed = discord.Embed(
            title="⚔️ DUEL STARTED!",
            description=(
                f"**{interaction.user.display_name}** vs **{opponent.display_name}**\n"
                f"💰 Bet: **{bet:,}** credits\n"
                f"🆔 Duel ID: **{duel_id}**\n"
                f"📺 Channel: {duel_channel.mention}\n\n"
                f"*Use `/spectate {duel_id}` to watch!*"
            ),
            color=0xE74C3C
        )
        await interaction.channel.send(embed=announce_embed)

        # Run duel in private channel
        try:
            await self.run_duel(
                duel_channel, interaction.user, opponent,
                bet, p1, p2, duel_key, duel_id
            )
        except Exception as e:
            print(f"Duel error: {e}")
            await duel_channel.send("❌ Duel error occurred!")
        finally:
            self.active_duels.pop(duel_key, None)
            await ActiveDuelData.delete_active_duel(duel_id)
            await self.delete_duel_channel(duel_channel, delay=30)

    async def run_duel(self, channel, p1_member, p2_member, bet, p1, p2, duel_key, duel_id):
        """Main duel game loop in private channel"""
        p1_id = p1_member.id
        p2_id = p2_member.id
        p1_name = p1_member.display_name
        p2_name = p2_member.display_name

        # Welcome message
        welcome_embed = discord.Embed(
            title=f"⚔️ DUEL ARENA — {duel_id}",
            description=(
                f"Welcome to the arena!\n\n"
                f"🔴 **{p1_name}** vs 🔵 **{p2_name}**\n"
                f"💰 **{bet:,}** credits on the line!\n\n"
                f"*Spectators can use `/spectate {duel_id}` to watch!*"
            ),
            color=0xE74C3C
        )
        await channel.send(embed=welcome_embed)
        await asyncio.sleep(2)

        # Get stats
        p1_stats = await DuelData.get_duel_stats(p1_id) or {
            "wins": 0, "losses": 0, "win_rate": 0,
            "streak": 0, "rank": "Novice Duelist",
            "rank_emoji": "🥉", "powerups": {}
        }
        p2_stats = await DuelData.get_duel_stats(p2_id) or {
            "wins": 0, "losses": 0, "win_rate": 0,
            "streak": 0, "rank": "Novice Duelist",
            "rank_emoji": "🥉", "powerups": {}
        }

        # Arena animation
        arena_msg = await channel.send(embed=discord.Embed(title="⚔️", description="Loading arena...", color=0xE74C3C))
        await play_arena_animation(arena_msg, p1_name, p2_name, p1_stats, p2_stats, bet)

        # Head to head
        h2h = await DuelData.get_head_to_head(p1_id, p2_id)
        if h2h["total_duels"] > 0:
            await channel.send(f"📊 **Head to Head:** {p1_name} **{h2h['user1_wins']}** - **{h2h['user2_wins']}** {p2_name}")

        # Spectator betting
        spec_view = SpectatorView(p1_id, p2_id)
        spec_embed = discord.Embed(
            title="👀 SPECTATORS — Place your bets!",
            description=f"Who will win?\n\n1️⃣ **{p1_name}**\n2️⃣ **{p2_name}**\n\n*15 seconds to pick!*",
            color=0xF1C40F
        )
        spec_msg = await channel.send(embed=spec_embed, view=spec_view)

        # Mode selection
        mode_embed = discord.Embed(
            title="🎮 Choose Game Mode!",
            description=(
                f"**Both players vote!**\n\n"
                f"📝 **Classic** — 15s per question\n"
                f"⚡ **Speed** — 5s per question!\n"
                f"🧠 **Expert** — Hard questions, 20s\n\n"
                f"*If different votes, random pick!*"
            ),
            color=0x3498DB
        )
        mode_view = ModeSelectView(p1_id, p2_id)
        mode_msg = await channel.send(embed=mode_embed, view=mode_view)
        await mode_view.wait()

        if not mode_view.mode:
            mode_view.mode = "classic"

        mode = mode_view.mode
        mode_info = DUEL_MODES[mode]
        base_time = mode_info["time"]

        await ActiveDuelData.update_active_duel(duel_id, {"mode": mode})
        await channel.send(f"🎮 Mode: **{mode_info['emoji']} {mode_info['name']}** — {mode_info['desc']}")

        # Trash talk
        trash_embed = discord.Embed(title="💬 TRASH TALK!", description="*Send a message to your opponent!*", color=0xE67E22)
        trash_view = TrashTalkView(p1_id, p2_id, channel)
        trash_msg = await channel.send(embed=trash_embed, view=trash_view)
        await asyncio.sleep(8)

        for v in [spec_view, trash_view]:
            for item in v.children:
                item.disabled = True
        try:
            await spec_msg.edit(view=spec_view)
            await trash_msg.edit(view=trash_view)
        except Exception:
            pass

        # ===== BEST OF 3 ROUNDS =====
        p1_score = 0
        p2_score = 0
        used_questions = []
        rounds_data = []
        round_num = 0

        while p1_score < 2 and p2_score < 2:
            round_num += 1

            await ActiveDuelData.update_active_duel(duel_id, {
                "round": round_num, "p1_score": p1_score, "p2_score": p2_score
            })

            # Round animation
            round_msg = await channel.send(embed=discord.Embed(title="⚔️", description="...", color=0xE74C3C))
            await play_round_animation(round_msg, round_num)

            score_text = build_score_bar(p1_score, p2_score, p1_name, p2_name)
            await channel.send(score_text)

            # Run round
            result = await self.run_round(channel, p1_id, p2_id, p1_name, p2_name, mode, base_time, used_questions, round_num)
            rounds_data.append(result)

            if result["winner"] == p1_id:
                p1_score += 1
            elif result["winner"] == p2_id:
                p2_score += 1

            score_text = build_score_bar(p1_score, p2_score, p1_name, p2_name)
            await channel.send(score_text)

            if p1_score < 2 and p2_score < 2:
                await channel.send("*Next round in 3 seconds...*")
                await asyncio.sleep(3)

        # Final results
        await self.finish_duel(channel, p1_id, p2_id, p1_name, p2_name, p1_score, p2_score, bet, rounds_data, mode, spec_view, duel_id)

    async def run_round(self, channel, p1_id, p2_id, p1_name, p2_name, mode, base_time, used_questions, round_num):
        """Run a single round"""
        question = get_question(mode, used_questions)
        used_questions.append(question["q"])

        # Powerup phase
        p1_user = await UserProfile.get_user(p1_id)
        p2_user = await UserProfile.get_user(p2_id)
        p1_powerups = p1_user.get("duel_powerups", {}) if p1_user else {}
        p2_powerups = p2_user.get("duel_powerups", {}) if p2_user else {}
        has_any_p1 = any(v > 0 for v in p1_powerups.values())
        has_any_p2 = any(v > 0 for v in p2_powerups.values())

        p1_powerup = None
        p2_powerup = None

        if has_any_p1 or has_any_p2:
            if has_any_p1:
                p1_pw_view = PowerupSelectView(p1_id, p1_powerups)
                p1_pw_msg = await channel.send(f"🎒 {p1_name} — Choose powerup:", view=p1_pw_view)
            if has_any_p2:
                p2_pw_view = PowerupSelectView(p2_id, p2_powerups)
                p2_pw_msg = await channel.send(f"🎒 {p2_name} — Choose powerup:", view=p2_pw_view)

            await asyncio.sleep(12)

            if has_any_p1:
                p1_powerup = p1_pw_view.selected
                for item in p1_pw_view.children:
                    item.disabled = True
                try:
                    await p1_pw_msg.edit(view=p1_pw_view)
                except Exception:
                    pass
            if has_any_p2:
                p2_powerup = p2_pw_view.selected
                for item in p2_pw_view.children:
                    item.disabled = True
                try:
                    await p2_pw_msg.edit(view=p2_pw_view)
                except Exception:
                    pass

        # Apply powerups
        p1_effects = await apply_powerup(p1_powerup, question, p1_id, p2_id, p1_id)
        p2_effects = await apply_powerup(p2_powerup, question, p1_id, p2_id, p2_id)

        if p1_effects["announcement"]:
            await channel.send(p1_effects["announcement"])
        if p2_effects["announcement"]:
            await channel.send(p2_effects["announcement"])

        if p1_effects["reroll"] or p2_effects["reroll"]:
            question = get_question(mode, used_questions)
            used_questions.append(question["q"])
            await channel.send("🔄 **New question incoming!**")
            await asyncio.sleep(1)

        time_limit = max(3, base_time + p1_effects["time_bonus"] + p2_effects["time_bonus"] - p1_effects["time_penalty_opponent"] - p2_effects["time_penalty_opponent"])

        peek_removes = None
        if p1_effects["peek_removes"]:
            peek_removes = p1_effects["peek_removes"]
        if p2_effects["peek_removes"]:
            peek_removes = (peek_removes or []) + p2_effects["peek_removes"]

        # Question embed
        cat = question.get("category", "general")
        diff = question.get("difficulty", "medium")
        cat_info = TRIVIA_CATEGORIES.get(cat, TRIVIA_CATEGORIES["general"])
        diff_info = TRIVIA_DIFFICULTIES.get(diff, TRIVIA_DIFFICULTIES["medium"])

        q_embed = discord.Embed(
            title=f"⚔️ Round {round_num} — FIGHT!",
            description=(
                f"{cat_info['emoji']} {cat_info['name']} | {diff_info['emoji']} {diff}\n\n"
                f"**{question['q']}**\n\n⏱️ **{time_limit} seconds!**"
            ),
            color=0xE74C3C
        )

        answer_view = DuelAnswerView(question, p1_id, p2_id, time_limit, peek_removes)
        q_msg = await channel.send(embed=q_embed, view=answer_view)
        await answer_view.wait()

        for item in answer_view.children:
            item.disabled = True
        try:
            await q_msg.edit(view=answer_view)
        except Exception:
            pass

        # Process result
        p1_ans = answer_view.answers.get(p1_id)
        p2_ans = answer_view.answers.get(p2_id)
        correct_text = question["options"][question["correct"]]
        round_winner = None
        result_text = ""

        if not p1_ans and not p2_ans:
            result_text = "💀 Neither answered! No point."
        elif not p1_ans:
            round_winner = p2_id
            result_text = f"✅ **{p2_name}** wins! {p1_name} didn't answer!"
        elif not p2_ans:
            round_winner = p1_id
            result_text = f"✅ **{p1_name}** wins! {p2_name} didn't answer!"
        elif p1_ans["correct"] and not p2_ans["correct"]:
            round_winner = p1_id
            result_text = f"✅ **{p1_name}** correct! ({p1_ans['time']:.1f}s)"
        elif not p1_ans["correct"] and p2_ans["correct"]:
            round_winner = p2_id
            result_text = f"✅ **{p2_name}** correct! ({p2_ans['time']:.1f}s)"
        elif p1_ans["correct"] and p2_ans["correct"]:
            if p1_ans["time"] < p2_ans["time"]:
                round_winner = p1_id
                result_text = f"⚡ Both correct! **{p1_name}** faster! ({p1_ans['time']:.1f}s vs {p2_ans['time']:.1f}s)"
            elif p2_ans["time"] < p1_ans["time"]:
                round_winner = p2_id
                result_text = f"⚡ Both correct! **{p2_name}** faster! ({p2_ans['time']:.1f}s vs {p1_ans['time']:.1f}s)"
            else:
                result_text = "🤝 Both correct, same time! No point."
        else:
            result_text = "💀 Both wrong! No point."

        r_embed = discord.Embed(
            title=f"📊 Round {round_num} Result",
            description=result_text,
            color=0x2ECC71 if round_winner else 0x95A5A6
        )
        r_embed.add_field(name="✅ Answer", value=f"**{correct_text}**", inline=False)
        if question.get("explanation"):
            r_embed.add_field(name="📖 Why?", value=question["explanation"][:300], inline=False)

        await channel.send(embed=r_embed)

        return {
            "round": round_num, "winner": round_winner,
            "question": question["q"], "correct": correct_text,
            "p1_answer": p1_ans, "p2_answer": p2_ans,
            "p1_powerup": p1_powerup, "p2_powerup": p2_powerup,
        }

# cogs/duel.py - PART 4 (FINAL)

    async def finish_duel(self, channel, p1_id, p2_id, p1_name, p2_name, p1_score, p2_score, bet, rounds_data, mode, spec_view, duel_id):
        """Handle duel ending and rewards"""
        if p1_score > p2_score:
            winner_id, loser_id = p1_id, p2_id
            winner_name, loser_name = p1_name, p2_name
            winner_score, loser_score = p1_score, p2_score
        else:
            winner_id, loser_id = p2_id, p1_id
            winner_name, loser_name = p2_name, p1_name
            winner_score, loser_score = p2_score, p1_score

        # Transfer credits
        winner = await UserProfile.get_user(winner_id)
        loser = await UserProfile.get_user(loser_id)
        actual_bet = 0

        if winner and loser:
            actual_bet = min(bet, loser.get("studio_credits", 0))

            shield_active = False
            for rd in rounds_data:
                if rd.get("winner") != loser_id:
                    if rd.get("p1_powerup") == "shield" and loser_id == p1_id:
                        shield_active = True
                    if rd.get("p2_powerup") == "shield" and loser_id == p2_id:
                        shield_active = True

            if shield_active:
                actual_bet = actual_bet // 2
                await channel.send(f"🛡️ Shield! {loser_name} only loses **{actual_bet:,}** credits!")

            if actual_bet > 0:
                await UserProfile.update_user(loser_id, {"studio_credits": loser.get("studio_credits", 0) - actual_bet})
                await UserProfile.update_user(winner_id, {"studio_credits": winner.get("studio_credits", 0) + actual_bet})

        # Record in database
        duel_result = await DuelData.record_duel(winner_id, loser_id, actual_bet, mode, rounds_data)
        await DuelData.record_loss(loser_id, actual_bet)

        # Check streak milestone
        if duel_result.get("milestone_hit"):
            streak = duel_result.get("winner_new_streak", 0)
            guild = channel.guild
            if guild:
                await announce_streak(self.bot, guild, winner_id, streak)

        # Victory animation
        vic_frames = [
            "\n\n        🏆\n\n",
            "\n\n     🏆 🏆 🏆\n\n",
            "\n\n  🏆 🏆 🏆 🏆 🏆\n\n",
            f"\n\n  🏆 {winner_name} WINS! 🏆\n\n",
        ]
        vic_msg = await channel.send(embed=discord.Embed(title="⚔️", description=vic_frames[0], color=0xF1C40F))
        for frame in vic_frames[1:]:
            embed = discord.Embed(title="⚔️ DUEL OVER!", description=frame, color=0xF1C40F)
            try:
                await vic_msg.edit(embed=embed)
            except Exception:
                pass
            await asyncio.sleep(0.5)

        await asyncio.sleep(1)

        # Rounds recap
        recap = ""
        for rd in rounds_data:
            rn = rd["round"]
            if rd["winner"] == p1_id:
                recap += f"Round {rn}: 🔴 **{p1_name}** ✅\n"
            elif rd["winner"] == p2_id:
                recap += f"Round {rn}: 🔵 **{p2_name}** ✅\n"
            else:
                recap += f"Round {rn}: 🤝 Draw\n"

        w_stats = await DuelData.get_duel_stats(winner_id)
        l_stats = await DuelData.get_duel_stats(loser_id)

        final_embed = discord.Embed(
            title=f"🏆 {winner_name} WINS THE DUEL!",
            description=(
                f"**{winner_name}** defeats **{loser_name}**\n"
                f"**{winner_score} - {loser_score}**\n\n"
                f"💰 **{actual_bet:,}** credits transferred!\n"
                f"🆔 Duel: **{duel_id}**"
            ),
            color=0x2ECC71
        )

        final_embed.add_field(name="📋 Rounds", value=recap, inline=False)

        if w_stats:
            w_text = f"```\nRank   : {w_stats['rank_emoji']} {w_stats['rank']}\nRecord : {w_stats['wins']}W-{w_stats['losses']}L\nRate   : {w_stats['win_rate']:.0f}%\nStreak : 🔥 {w_stats['streak']}x\n```"
            final_embed.add_field(name=f"🏆 {winner_name}", value=w_text, inline=True)

        if l_stats:
            l_text = f"```\nRank   : {l_stats['rank_emoji']} {l_stats['rank']}\nRecord : {l_stats['wins']}W-{l_stats['losses']}L\nRate   : {l_stats['win_rate']:.0f}%\nStreak : {l_stats['streak']}x\n```"
            final_embed.add_field(name=f"💀 {loser_name}", value=l_text, inline=True)

        # Rank up check
        if duel_result.get("winner_new_rank"):
            new_rank = duel_result["winner_new_rank"]
            old_wins = duel_result.get("winner_old_wins", 0)
            old_rank = DuelData.get_rank(old_wins)
            if new_rank["rank"] != old_rank["rank"]:
                final_embed.add_field(
                    name="🎉 RANK UP!",
                    value=f"{winner_name}: {old_rank['emoji']} {old_rank['rank']} → {new_rank['emoji']} {new_rank['rank']}",
                    inline=False
                )

        # Spectator results
        if spec_view.bets:
            correct_specs, wrong_specs = spec_view.get_results(winner_id)
            spec_text = ""
            if correct_specs:
                spec_text += f"✅ Correct: {' '.join(f'<@{uid}>' for uid in correct_specs)}\n"
            if wrong_specs:
                spec_text += f"❌ Wrong: {' '.join(f'<@{uid}>' for uid in wrong_specs)}\n"
            if spec_text:
                final_embed.add_field(name="👀 Spectator Results", value=spec_text, inline=False)

        final_embed.set_footer(text="⚔️ /code-duel to play again! • Channel closes in 30s")
        final_embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=final_embed)

    # ===== SPECTATE COMMAND =====
    @app_commands.command(name="spectate", description="👀 Watch a live duel!")
    @app_commands.describe(duel_id="Duel ID to spectate (leave empty to see list)")
    async def spectate(self, interaction: discord.Interaction, duel_id: str = None):
        await interaction.response.defer(ephemeral=True)

        if duel_id:
            # Join specific duel
            duel_id = duel_id.upper().strip()
            duel = await ActiveDuelData.get_active_duel(duel_id)

            if not duel:
                await interaction.followup.send("❌ Duel not found or already ended!", ephemeral=True)
                return

            if duel.get("status") != "active":
                await interaction.followup.send("❌ That duel has already ended!", ephemeral=True)
                return

            if interaction.user.id == duel.get("p1_id") or interaction.user.id == duel.get("p2_id"):
                await interaction.followup.send("❌ You're already in this duel!", ephemeral=True)
                return

            # Get duel channel
            duel_channel = interaction.guild.get_channel(duel.get("channel_id"))
            if not duel_channel:
                await interaction.followup.send("❌ Duel channel not found!", ephemeral=True)
                return

            # Add spectator to channel
            success = await self.add_spectator_to_channel(duel_channel, interaction.user)
            if not success:
                await interaction.followup.send("❌ Failed to join duel channel!", ephemeral=True)
                return

            await ActiveDuelData.add_spectator(duel_id, interaction.user.id)

            # Announce in duel channel
            try:
                await duel_channel.send(f"👀 **{interaction.user.display_name}** is now spectating!")
            except Exception:
                pass

            embed = discord.Embed(
                title="👀 Spectating!",
                description=(
                    f"You're now watching **{duel_id}**!\n\n"
                    f"🔴 **{duel.get('p1_name', 'Player 1')}** vs 🔵 **{duel.get('p2_name', 'Player 2')}**\n"
                    f"💰 Bet: **{duel.get('bet', 0):,}** credits\n"
                    f"🎮 Mode: **{duel.get('mode', 'classic')}**\n"
                    f"📊 Score: **{duel.get('p1_score', 0)}** - **{duel.get('p2_score', 0)}**\n"
                    f"🔄 Round: **{duel.get('round', 0)}**\n\n"
                    f"📺 Go to {duel_channel.mention}"
                ),
                color=0xF1C40F
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        else:
            # Show list of active duels
            active = await ActiveDuelData.get_all_active_duels(interaction.guild.id)

            if not active:
                embed = discord.Embed(
                    title="👀 No Active Duels",
                    description="No duels are happening right now!\n\n*Use `/code-duel @user bet` to start one!*",
                    color=0x95A5A6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="👀 Active Duels",
                description=f"**{len(active)}** duel(s) in progress!\nUse `/spectate DUEL-XXXX` to watch.\n",
                color=0xF1C40F
            )

            for duel in active:
                d_id = duel.get("_id", "???")
                p1n = duel.get("p1_name", "Player 1")
                p2n = duel.get("p2_name", "Player 2")
                d_bet = duel.get("bet", 0)
                d_mode = duel.get("mode", "classic")
                d_round = duel.get("round", 0)
                p1s = duel.get("p1_score", 0)
                p2s = duel.get("p2_score", 0)
                specs = len(duel.get("spectators", []))

                mode_emoji = DUEL_MODES.get(d_mode, {}).get("emoji", "📝")

                embed.add_field(
                    name=f"⚔️ {d_id}",
                    value=(
                        f"🔴 **{p1n}** vs 🔵 **{p2n}**\n"
                        f"💰 {d_bet:,} | {mode_emoji} {d_mode}\n"
                        f"📊 {p1s}-{p2s} | Round {d_round}\n"
                        f"👀 {specs} spectator(s)\n"
                        f"`/spectate {d_id}`"
                    ),
                    inline=True
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

    # ===== DUEL STATS =====
    @app_commands.command(name="duel-stats", description="⚔️ View duel statistics")
    @app_commands.describe(user="User to check")
    async def duel_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        target = user or interaction.user
        stats = await DuelData.get_duel_stats(target.id)

        if not stats:
            await interaction.followup.send("❌ No duel stats found! Play a duel first.")
            return

        embed = discord.Embed(title=f"⚔️ {target.display_name}'s Duel Stats", color=0xE74C3C)
        embed.add_field(name="🏅 Rank", value=f"{stats['rank_emoji']} **{stats['rank']}**", inline=True)
        embed.add_field(name="🔥 Streak", value=f"Current: **{stats['streak']}x**\nBest: **{stats['best_streak']}x**", inline=True)
        embed.add_field(name="📊 Record", value=f"**{stats['wins']}**W - **{stats['losses']}**L - **{stats['draws']}**D", inline=True)
        embed.add_field(name="📈 Win Rate", value=f"**{stats['win_rate']:.1f}%**", inline=True)
        embed.add_field(name="💰 Won", value=f"**{stats['credits_won']:,}**", inline=True)
        embed.add_field(name="💸 Lost", value=f"**{stats['credits_lost']:,}**", inline=True)

        pw = stats.get("powerups", {})
        pw_text = "\n".join(f"{POWERUP_INFO[n]['emoji']} {POWERUP_INFO[n]['name']}: **{pw.get(n, 0)}**" for n in POWERUP_INFO)
        embed.add_field(name="🎒 Powerups", value=pw_text, inline=False)

        history = stats.get("history", [])[-5:]
        if history:
            hist_text = ""
            for h in reversed(history):
                if h["result"] == "win":
                    hist_text += f"✅ Won **{h.get('bet', 0):,}** vs <@{h.get('opponent', 0)}>\n"
                else:
                    hist_text += f"❌ Lost **{h.get('bet', 0):,}**\n"
            embed.add_field(name="📜 Recent", value=hist_text, inline=False)

        next_rank = None
        for r in DuelData.DUEL_RANKS:
            if r["min"] > stats["wins"]:
                next_rank = r
                break
        if next_rank:
            embed.set_footer(text=f"🎯 {next_rank['min'] - stats['wins']} more wins to {next_rank['emoji']} {next_rank['rank']}")

        await interaction.followup.send(embed=embed)

    # ===== DUEL LEADERBOARD =====
    @app_commands.command(name="duel-leaderboard", description="⚔️ View top duelists")
    async def duel_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top = await DuelData.get_duel_leaderboard(10)

        if not top:
            await interaction.followup.send("❌ No duels yet!")
            return

        embed = discord.Embed(title="⚔️ Duel Leaderboard", color=0xF1C40F)
        medals = ["🥇", "🥈", "🥉"]
        desc = ""

        for i, u in enumerate(top):
            rank_info = DuelData.get_rank(u.get("duel_wins", 0))
            medal = medals[i] if i < 3 else f"**#{i+1}**"
            wins = u.get("duel_wins", 0)
            losses = u.get("duel_losses", 0)
            streak = u.get("duel_streak", 0)
            name = u.get("username", "Unknown")
            desc += f"{medal} **{name}** — {rank_info['emoji']} {rank_info['rank']}\n   {wins}W-{losses}L"
            if streak >= 3:
                desc += f" | 🔥 {streak}x"
            desc += "\n\n"

        embed.description = desc
        embed.set_footer(text="⚔️ /code-duel to climb the ranks!")
        await interaction.followup.send(embed=embed)

    # ===== BUY POWERUP =====
    @app_commands.command(name="buy-powerup", description="🎒 Buy duel powerups")
    @app_commands.describe(powerup="Which powerup", amount="How many (1-10)")
    @app_commands.choices(powerup=[
        app_commands.Choice(name="🛡️ Shield (200c)", value="shield"),
        app_commands.Choice(name="⏱️ Extra Time (150c)", value="extra_time"),
        app_commands.Choice(name="👀 Peek (250c)", value="peek"),
        app_commands.Choice(name="💣 Sabotage (300c)", value="sabotage"),
        app_commands.Choice(name="🔄 Reroll (350c)", value="reroll"),
    ])
    async def buy_powerup(self, interaction: discord.Interaction, powerup: str, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount < 1 or amount > 10:
            await interaction.followup.send("❌ Amount must be **1-10**!", ephemeral=True)
            return

        info = POWERUP_INFO.get(powerup)
        if not info:
            await interaction.followup.send("❌ Invalid powerup!", ephemeral=True)
            return

        total_cost = info["price"] * amount
        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        credits = user.get("studio_credits", 0)
        if credits < total_cost:
            await interaction.followup.send(f"❌ Need **{total_cost:,}** but have **{credits:,}**!", ephemeral=True)
            return

        await UserProfile.update_user(interaction.user.id, {"studio_credits": credits - total_cost})
        await DuelData.add_powerup(interaction.user.id, powerup, amount)

        embed = discord.Embed(
            title="✅ Powerup Purchased!",
            description=(
                f"{info['emoji']} **{info['name']}** x{amount}\n\n"
                f"💰 Cost: **{total_cost:,}** credits\n"
                f"💎 Balance: **{credits - total_cost:,}** credits\n\n"
                f"*Use in your next duel!*"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ===== STREAK CHANNEL =====
    @app_commands.command(name="streak-channel", description="⚔️ Set streak announcement channel")
    @app_commands.describe(channel="Channel for announcements")
    @app_commands.default_permissions(administrator=True)
    async def streak_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await DuelData.set_streak_channel(interaction.guild.id, channel.id)

        embed = discord.Embed(
            title="✅ Streak Channel Set!",
            description=f"Announcements in {channel.mention}\nMilestones: **10x, 30x, 50x, 100x, 500x**",
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ===== HEAD TO HEAD =====
    @app_commands.command(name="duel-h2h", description="⚔️ View head-to-head record")
    @app_commands.describe(opponent="Who to compare against")
    async def duel_h2h(self, interaction: discord.Interaction, opponent: discord.Member):
        await interaction.response.defer()

        if opponent.id == interaction.user.id:
            await interaction.followup.send("❌ Can't compare against yourself!")
            return

        h2h = await DuelData.get_head_to_head(interaction.user.id, opponent.id)

        if h2h["total_duels"] == 0:
            await interaction.followup.send(f"❌ No duels between you and {opponent.display_name} yet!")
            return

        embed = discord.Embed(
            title=f"⚔️ {interaction.user.display_name} vs {opponent.display_name}",
            description=(
                f"**{h2h['total_duels']}** total duels\n\n"
                f"🔴 **{interaction.user.display_name}:** {h2h['user1_wins']} wins\n"
                f"🔵 **{opponent.display_name}:** {h2h['user2_wins']} wins"
            ),
            color=0xE74C3C
        )

        if h2h["user1_wins"] > h2h["user2_wins"]:
            embed.set_footer(text=f"👑 {interaction.user.display_name} leads the rivalry!")
        elif h2h["user2_wins"] > h2h["user1_wins"]:
            embed.set_footer(text=f"👑 {opponent.display_name} leads the rivalry!")
        else:
            embed.set_footer(text="🤝 It's tied!")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DuelCog(bot))
