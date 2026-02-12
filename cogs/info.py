import discord
from discord.ext import commands
from discord import app_commands
from config import BOT_COLOR, GUILD_ID
from database import UserProfile
from datetime import datetime


# ==================== SETUP ROLE SELECT ====================
class SetupRoleSelect(discord.ui.Select):
    """Multi-role select for setup command"""

    def __init__(self, user_id: int, guild_id: int):
        self.user_id = user_id
        self.guild_id = guild_id

        options = [
            discord.SelectOption(label="Builder", emoji="🏗️", description="Build structures and environments"),
            discord.SelectOption(label="Scripter", emoji="📝", description="Write Lua/Luau scripts"),
            discord.SelectOption(label="Designer", emoji="🎨", description="Design user interfaces"),
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
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your setup!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        roles = self.values
        roles_str = ", ".join(roles)

        user = await UserProfile.get_user(self.user_id)
        if not user:
            await UserProfile.create_user(self.user_id, interaction.user.name)

        await UserProfile.update_user(self.user_id, {
            "roles": roles,
            "rank": "Beginner",
            "experience_months": 0
        })

        # Assign Discord roles
        assigned = []
        failed = []
        try:
            guild = interaction.client.get_guild(self.guild_id) or await interaction.client.fetch_guild(self.guild_id)
            member = guild.get_member(self.user_id) or await guild.fetch_member(self.user_id)

            for role in roles:
                role_obj = discord.utils.get(guild.roles, name=role)
                if role_obj:
                    try:
                        await member.add_roles(role_obj)
                        assigned.append(role)
                    except Exception:
                        failed.append(role)
                else:
                    failed.append(role)
        except Exception as e:
            print(f"✗ Could not assign roles: {e}")

        embed = discord.Embed(
            title="✅ Profile Setup Complete!",
            description=f"Your roles: **{roles_str}**",
            color=discord.Color.green()
        )

        if assigned:
            embed.add_field(
                name="✅ Roles Assigned",
                value=", ".join(assigned),
                inline=False
            )
        if failed:
            embed.add_field(
                name="⚠️ Could Not Assign",
                value=", ".join(failed) + "\n*(Ask an admin to create these roles)*",
                inline=False
            )

        embed.add_field(
            name="📋 Set Your Experience",
            value=(
                "Type your experience in this channel:\n"
                "• `1 day` / `10 days`\n"
                "• `1 month` / `6 months`\n"
                "• `1 year` / `3 years`\n"
                "• `skip` — Start as Beginner"
            ),
            inline=False
        )

        embed.add_field(
            name="🚀 What's Next?",
            value=(
                "`/quest` — Start earning rewards\n"
                "`/daily` — Claim daily credits\n"
                "`/shop` — Browse the marketplace\n"
                "`/learn` — Learn Lua/Luau\n"
                "`/help` — See all commands"
            ),
            inline=False
        )

        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send(embed=embed, ephemeral=True)


class SetupRoleView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.add_item(SetupRoleSelect(user_id, guild_id))


# ==================== HELP CATEGORY SELECT ====================
class HelpCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Getting Started",
                value="getting_started",
                emoji="🚀",
                description="New here? Start with this!"
            ),
            discord.SelectOption(
                label="Profile & Stats",
                value="profile",
                emoji="👤",
                description="Profile, card, leaderboard, ID"
            ),
            discord.SelectOption(
                label="Economy & Quests",
                value="economy",
                emoji="💰",
                description="Credits, quests, daily rewards"
            ),
            discord.SelectOption(
                label="Marketplace",
                value="marketplace",
                emoji="🛍️",
                description="Buy, sell, browse assets"
            ),
            discord.SelectOption(
                label="AI Features",
                value="ai",
                emoji="🤖",
                description="AI chat, code review, predictions"
            ),
            discord.SelectOption(
                label="Fun & Games",
                value="fun",
                emoji="🎮",
                description="Duels, roasts, unboxing, trivia"
            ),
            discord.SelectOption(
                label="Teams & Collaboration",
                value="teams",
                emoji="👥",
                description="Create teams, find developers"
            ),
            discord.SelectOption(
                label="Learning",
                value="learning",
                emoji="📚",
                description="50 Lua/Luau lessons"
            ),
            discord.SelectOption(
                label="Premium & Conversion",
                value="premium",
                emoji="💎",
                description="pCredits, AI credits, premium shop"
            ),
            discord.SelectOption(
                label="Ranks & Progression",
                value="ranks",
                emoji="👑",
                description="Rank system and benefits"
            ),
            discord.SelectOption(
                label="All Commands",
                value="all_commands",
                emoji="📋",
                description="Complete command list"
            ),
        ]

        super().__init__(
            placeholder="📖 Select a help category...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]

        if choice == "getting_started":
            embed = discord.Embed(
                title="🚀 Getting Started",
                description="Welcome to Ashtrails' Studio! Here's how to get going:",
                color=BOT_COLOR
            )
            embed.add_field(
                name="Step 1 — Create Your Profile",
                value=(
                    "`/start` or `/setup` — Choose your roles\n"
                    "Pick from Builder, Scripter, Designer, Animator, etc."
                ),
                inline=False
            )
            embed.add_field(
                name="Step 2 — Earn Credits",
                value=(
                    "`/daily` — Claim daily reward (streak bonuses!)\n"
                    "`/quest` — Complete quests for XP & credits\n"
                    "`/trivia` — Free trivia for quick credits"
                ),
                inline=False
            )
            embed.add_field(
                name="Step 3 — Level Up",
                value=(
                    "Chat in channels to earn XP\n"
                    "Join voice channels for voice XP\n"
                    "Complete quests and lessons"
                ),
                inline=False
            )
            embed.add_field(
                name="Step 4 — Explore Features",
                value=(
                    "`/shop` — Browse & buy assets\n"
                    "`/sell` — Sell your code, builds, UIs\n"
                    "`/learn` — Learn Lua/Luau (50 lessons!)\n"
                    "`/team` — Create or join a team\n"
                    "`/temp_chat_ai` — Chat with AI assistant"
                ),
                inline=False
            )
            embed.add_field(
                name="Step 5 — Have Fun!",
                value=(
                    "`/code-duel` — Challenge others to trivia\n"
                    "`/unbox-snippet` — Open code boxes\n"
                    "`/ai-roast` — Get roasted by AI\n"
                    "`/coinflip` — Gamble your credits"
                ),
                inline=False
            )
            embed.set_footer(text="Use /help anytime to come back here!")

        elif choice == "profile":
            embed = discord.Embed(
                title="👤 Profile & Stats Commands",
                description="View and manage your developer profile.",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/profile [user]`",
                value="View your or someone's profile with stats, rank, XP, and reputation. Buttons for detailed stats, portfolio, and rank info.",
                inline=False
            )
            embed.add_field(
                name="`/card`",
                value="Generate your developer portfolio card showing roles, level, reputation, and featured games.",
                inline=False
            )
            embed.add_field(
                name="`/leaderboard`",
                value="View the top 10 developers ranked by level.",
                inline=False
            )
            embed.add_field(
                name="`/myid`",
                value="View your unique Player ID (auto-generated).",
                inline=False
            )
            embed.add_field(
                name="`/stats`",
                value="View server-wide statistics: total users, teams, and marketplace listings.",
                inline=False
            )

        elif choice == "economy":
            embed = discord.Embed(
                title="💰 Economy & Quests",
                description="Earn and spend Studio Credits!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/daily`",
                value="Claim daily reward. Streak bonuses up to 7 days!\n• Base: 100 Credits + 25 XP\n• Max streak: +175 Credits + +70 XP",
                inline=False
            )
            embed.add_field(
                name="`/quest`",
                value="View 15 quests with progress tracking.\n• Filter by Easy/Medium/Hard\n• Click **Claim Quest** → type Quest ID\n• Earn XP + Credits per quest",
                inline=False
            )
            embed.add_field(
                name="`/credits`",
                value="Check your Studio Credits, pCredits, and AI Credits balance.",
                inline=False
            )
            embed.add_field(
                name="`/credit`",
                value="Alias for `/credits`.",
                inline=False
            )
            embed.add_field(
                name="💡 Ways to Earn",
                value=(
                    "• `/daily` — Daily rewards\n"
                    "• `/quest` — Complete quests\n"
                    "• `/trivia` — Free trivia (+25 credits)\n"
                    "• `/sell` — Sell assets\n"
                    "• Chat & voice — Passive XP\n"
                    "• `/learn` — Complete lessons (+75 credits)"
                ),
                inline=False
            )

        elif choice == "marketplace":
            embed = discord.Embed(
                title="🛍️ Marketplace Commands",
                description="Buy and sell Roblox assets!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/shop`",
                value="Browse the marketplace with filters:\n• Filter by category (Code, Builds, UIs)\n• Search by keyword\n• Sort by price, rating, newest, best selling\n• Pagination support",
                inline=False
            )
            embed.add_field(
                name="`/sell`",
                value="List your assets for sale:\n• **Code** — Paste Lua/Luau directly\n• **Builds** — Upload .rbxm/.rbxmx files\n• **UIs** — Upload .rbxm/.rbxmx files\n• View your current listings",
                inline=False
            )
            embed.add_field(
                name="`/buy <listing_id>`",
                value="Purchase a listing by ID. Code is shown instantly. Files are sent via DM. You can rate the seller after purchase.",
                inline=False
            )

        elif choice == "ai":
            embed = discord.Embed(
                title="🤖 AI Features",
                description="Powered by Gemini AI. Some features cost AI Credits.",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/temp_chat_ai`",
                value="Create a private AI chat channel (expires in 1 hour).\n• Normal chat: 1 AI Credit/msg\n• Agent mode: 3 AI Credits/msg\n• Super Agent: 5 AI Credits/msg\n• Admins: free",
                inline=False
            )
            embed.add_field(
                name="`/setup_ai <channel>` *(Admin)*",
                value="Set a permanent AI chat channel.",
                inline=False
            )
            embed.add_field(
                name="`/ai-fix <code>`",
                value="AI rewrites your code optimized and bug-free. (1 AI Credit)",
                inline=False
            )
            embed.add_field(
                name="`/ai-predict-game <idea>`",
                value="AI analyzes your game idea and predicts success. (1 AI Credit)",
                inline=False
            )
            embed.add_field(
                name="`/ideas [keyword]`",
                value="AI generates 3 trending game ideas. (1 AI Credit)",
                inline=False
            )
            embed.add_field(
                name="`/review`",
                value="Quick AI code review with score and tips. (Free)",
                inline=False
            )
            embed.add_field(
                name="🔑 AI Chat Modes",
                value=(
                    "In AI channels, type:\n"
                    "• `change to agent mode` — Task planning + code gen\n"
                    "• `change to super agent` — Full pipeline\n"
                    "• `exit agent mode` — Back to normal"
                ),
                inline=False
            )

        elif choice == "fun":
            embed = discord.Embed(
                title="🎮 Fun & Games",
                description="Have fun and win credits!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/code-duel <opponent> [bet]`",
                value="Challenge someone to a Luau knowledge duel!\n• Opponent must accept\n• Bet 50-10,000 credits\n• 15 seconds to answer",
                inline=False
            )
            embed.add_field(
                name="`/trivia`",
                value="Free solo trivia question. +15 XP & +25 Credits if correct!",
                inline=False
            )
            embed.add_field(
                name="`/coinflip <choice> [bet]`",
                value="Flip a coin! Bet up to 5,000 credits on heads or tails.",
                inline=False
            )
            embed.add_field(
                name="`/unbox-snippet`",
                value="Open a random code snippet box (500 Credits).\nRarities: Common → Uncommon → Rare → Epic → Legendary (1%)",
                inline=False
            )
            embed.add_field(
                name="`/ai-roast <user>`",
                value="AI roasts a user based on their profile stats. (1 AI Credit)",
                inline=False
            )
            embed.add_field(
                name="`/dev-bounty <task> <reward>`",
                value="Post a bounty (100-50,000 credits). Others can claim it. Auto-refunds after 24h.",
                inline=False
            )
            embed.add_field(
                name="`/dev-confession <text>`",
                value="Submit an anonymous dev confession with AI commentary.",
                inline=False
            )
            embed.add_field(
                name="`/flex-wealth`",
                value="Show the top 10 richest developers in the server.",
                inline=False
            )

        elif choice == "teams":
            embed = discord.Embed(
                title="👥 Teams & Collaboration",
                description="Build projects together!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/team <name> <project>`",
                value="Create a new team for a project. You become the team leader.",
                inline=False
            )
            embed.add_field(
                name="`/team_join <team_id>`",
                value="Join an existing team by its ID.",
                inline=False
            )
            embed.add_field(
                name="`/find <role>`",
                value="Find developers by role (Builder, Scripter, etc.) and experience level.",
                inline=False
            )

        elif choice == "learning":
            embed = discord.Embed(
                title="📚 Learning System",
                description="50 comprehensive Lua/Luau lessons!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="`/learn`",
                value="Creates your private learning channel with:\n• 50 AI-powered lessons\n• Interactive quizzes\n• Progress tracking\n• Weakness analysis\n• Bookmarks & cheat sheets",
                inline=False
            )
            embed.add_field(
                name="📚 5 Phases",
                value=(
                    "1️⃣ **Fundamentals** (Lessons 1-12)\n"
                    "2️⃣ **Intermediate** (Lessons 13-24)\n"
                    "3️⃣ **Advanced** (Lessons 25-36)\n"
                    "4️⃣ **Expert** (Lessons 37-45)\n"
                    "5️⃣ **Mastery Projects** (Lessons 46-50)"
                ),
                inline=False
            )
            embed.add_field(
                name="📝 In-Channel Commands",
                value=(
                    "`start lesson` / `next lesson` / `repeat lesson`\n"
                    "`hint` / `skip` / `cheat sheet` / `practice`\n"
                    "`my progress` / `my weaknesses` / `bookmarks`\n"
                    "`review <number>` / `final test`\n"
                    "`switch to coder` / `switch to explain`"
                ),
                inline=False
            )
            embed.add_field(
                name="🎁 Rewards",
                value="• +50 XP & +75 Credits per lesson\n• +500 XP & +1000 Credits for graduation",
                inline=False
            )

        elif choice == "premium":
            embed = discord.Embed(
                title="💎 Premium & Currency",
                description="Three currency types and conversion system.",
                color=BOT_COLOR
            )
            embed.add_field(
                name="💰 Studio Credits",
                value="Main currency. Earned from quests, daily, selling, lessons.",
                inline=False
            )
            embed.add_field(
                name="💎 pCredits",
                value="Premium currency for special items.",
                inline=False
            )
            embed.add_field(
                name="🤖 AI Credits",
                value="Used for AI features (chat, code fix, predictions).",
                inline=False
            )
            embed.add_field(
                name="`/convert [amount]`",
                value="Convert Studio Credits → pCredits.\n*(Rate configured by admin)*",
                inline=False
            )
            embed.add_field(
                name="`/convert_ai [amount]`",
                value="Convert pCredits → AI Credits.\n*(Rate configured by admin)*",
                inline=False
            )
            embed.add_field(
                name="`/pshop`",
                value="Premium shop — buy team slots, project slots, and more with pCredits.",
                inline=False
            )
            embed.add_field(
                name="Admin: `!give <user> <type> <amount>`",
                value="Give credits/pcredits/ai_credits to a user. (Admin only, prefix command)",
                inline=False
            )

        elif choice == "ranks":
            embed = discord.Embed(
                title="👑 Ranks & Progression",
                description="Level up and unlock benefits!",
                color=BOT_COLOR
            )
            embed.add_field(
                name="🥚 Beginner (Level 1-4)",
                value="Starting rank. Complete quests and lessons to level up!",
                inline=False
            )
            embed.add_field(
                name="🌱 Learner (Level 5-9)",
                value="You're getting the hang of it! More quest rewards unlocked.",
                inline=False
            )
            embed.add_field(
                name="🔥 Expert (Level 10-14)",
                value="Experienced developer. Access to advanced features.",
                inline=False
            )
            embed.add_field(
                name="👑 Master (Level 15+)",
                value="Top-tier developer. Maximum prestige!",
                inline=False
            )
            embed.add_field(
                name="📈 How to Level Up",
                value=(
                    "• Send messages — passive XP\n"
                    "• Voice channels — voice XP\n"
                    "• `/daily` — daily XP\n"
                    "• `/quest` — quest XP rewards\n"
                    "• `/learn` — lesson completion XP\n"
                    "• `/trivia` — correct answers give XP"
                ),
                inline=False
            )
            embed.add_field(
                name="⭐ Reputation",
                value="Earn reputation from other users recognizing your help and contributions.",
                inline=False
            )

        elif choice == "all_commands":
            embed = discord.Embed(
                title="📋 All Commands (36)",
                description="Complete list of every command available.",
                color=BOT_COLOR
            )
            embed.add_field(
                name="🚀 Setup & Profile",
                value=(
                    "`/start` — Setup your profile\n"
                    "`/setup` — Choose roles\n"
                    "`/profile [user]` — View profile\n"
                    "`/card` — Developer card\n"
                    "`/myid` — Your Player ID\n"
                    "`/leaderboard` — Top developers"
                ),
                inline=False
            )
            embed.add_field(
                name="💰 Economy",
                value=(
                    "`/daily` — Daily reward\n"
                    "`/quest` — Quests & rewards\n"
                    "`/credits` — Check balance\n"
                    "`/credit` — Balance alias\n"
                    "`/convert` — Credits → pCredits\n"
                    "`/convert_ai` — pCredits → AI Credits\n"
                    "`/pshop` — Premium shop"
                ),
                inline=False
            )
            embed.add_field(
                name="🛍️ Marketplace",
                value=(
                    "`/shop` — Browse listings\n"
                    "`/sell` — Sell assets\n"
                    "`/buy <id>` — Buy listing"
                ),
                inline=False
            )
            embed.add_field(
                name="🤖 AI Features",
                value=(
                    "`/temp_chat_ai` — Private AI chat\n"
                    "`/setup_ai` — Set AI channel *(Admin)*\n"
                    "`/ai-fix <code>` — Optimize code\n"
                    "`/ai-predict-game <idea>` — Predict success\n"
                    "`/ideas [keyword]` — Game ideas\n"
                    "`/review` — Code review\n"
                    "`/ai-roast <user>` — AI roast"
                ),
                inline=False
            )
            embed.add_field(
                name="🎮 Fun & Games",
                value=(
                    "`/code-duel <user> [bet]` — Knowledge duel\n"
                    "`/trivia` — Free trivia\n"
                    "`/coinflip <choice> [bet]` — Coin flip\n"
                    "`/unbox-snippet` — Code box\n"
                    "`/dev-bounty <task> <reward>` — Post bounty\n"
                    "`/dev-confession <text>` — Anonymous confession\n"
                    "`/flex-wealth` — Wealth leaderboard"
                ),
                inline=False
            )
            embed.add_field(
                name="👥 Teams",
                value=(
                    "`/team <name> <project>` — Create team\n"
                    "`/team_join <id>` — Join team\n"
                    "`/find <role>` — Find developers"
                ),
                inline=False
            )
            embed.add_field(
                name="📚 Learning",
                value="`/learn` — Start Lua/Luau lessons (50 lessons)",
                inline=False
            )
            embed.add_field(
                name="ℹ️ Info",
                value=(
                    "`/help` — This menu\n"
                    "`/stats` — Server statistics"
                ),
                inline=False
            )
            embed.add_field(
                name="🔧 Admin",
                value="`!give <user> <type> <amount>` — Give credits *(prefix cmd, admin only)*",
                inline=False
            )

        else:
            embed = discord.Embed(
                title="❌ Unknown Category",
                description="Please select a valid category.",
                color=discord.Color.red()
            )

        embed.set_footer(text="Use the dropdown above to browse other categories!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpView(discord.ui.View):
    """Main help menu with category dropdown and quick buttons"""

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpCategorySelect())

    @discord.ui.button(label="Quick Start", emoji="⚡", style=discord.ButtonStyle.success, row=1)
    async def quick_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚡ Quick Start Guide",
            description="Get up and running in 60 seconds!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="1️⃣ → `/start`",
            value="Set up your profile and choose roles",
            inline=False
        )
        embed.add_field(
            name="2️⃣ → `/daily`",
            value="Claim your first 100+ credits",
            inline=False
        )
        embed.add_field(
            name="3️⃣ → `/quest`",
            value="See what quests you can complete",
            inline=False
        )
        embed.add_field(
            name="4️⃣ → `/trivia`",
            value="Quick free credits from trivia",
            inline=False
        )
        embed.add_field(
            name="5️⃣ → `/learn`",
            value="Start learning Lua/Luau!",
            inline=False
        )
        embed.set_footer(text="You're all set! Use /help for more details.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="My Stats", emoji="📊", style=discord.ButtonStyle.secondary, row=1)
    async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        roles = user.get('roles', [])
        roles_str = ", ".join(roles) if isinstance(roles, list) and roles else user.get('role', 'None')
        level = user.get('level', 1)
        xp = user.get('xp', 0)
        xp_needed = level * 250
        xp_pct = min(100, int(xp / xp_needed * 100)) if xp_needed > 0 else 0
        bar_filled = int(xp_pct / 10)
        xp_bar = "█" * bar_filled + "░" * (10 - bar_filled)

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Quick Stats",
            color=BOT_COLOR
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🎭 Roles", value=roles_str, inline=True)
        embed.add_field(name="👑 Rank", value=user.get('rank', 'Beginner'), inline=True)
        embed.add_field(name="🎯 Level", value=str(level), inline=True)
        embed.add_field(
            name="✨ XP",
            value=f"`[{xp_bar}]` {xp}/{xp_needed} ({xp_pct}%)",
            inline=False
        )
        embed.add_field(name="💰 Credits", value=str(user.get('studio_credits', 0)), inline=True)
        embed.add_field(name="💎 pCredits", value=str(user.get('pcredits', 0)), inline=True)
        embed.add_field(name="🤖 AI Credits", value=str(user.get('ai_credits', 0)), inline=True)
        embed.add_field(name="⭐ Reputation", value=str(user.get('reputation', 0)), inline=True)
        embed.add_field(name="💬 Messages", value=str(user.get('message_count', 0)), inline=True)
        embed.add_field(name="🎤 Voice", value=f"{user.get('voice_minutes', 0)} min", inline=True)

        # Quest progress
        claimed = user.get('claimed_quests', [])
        embed.add_field(
            name="📜 Quests Claimed",
            value=f"{len(claimed)}/15",
            inline=True
        )
        embed.add_field(
            name="🔥 Daily Streak",
            value=f"{user.get('daily_streak', 0)} days",
            inline=True
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Invite Bot", emoji="🔗", style=discord.ButtonStyle.secondary, row=1)
    async def invite_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔗 Bot Information",
            description=(
                "**Ashtrails' Studio Bot**\n\n"
                "A complete Roblox developer community bot with:\n"
                "• 36 slash commands\n"
                "• AI-powered features\n"
                "• Marketplace system\n"
                "• 50 Lua/Luau lessons\n"
                "• Economy & quests\n"
                "• Fun mini-games\n\n"
                "This bot is private to this server."
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Made with ❤️ for the Roblox dev community")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== INFO COG ====================
class InfoCog(commands.Cog):
    """Help, Info, and Settings"""

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    @bot.tree.command(name="help", description="📖 Get help and see all commands")
    async def help_cmd(interaction: discord.Interaction):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        level = user.get('level', 1) if user else 1
        credits = user.get('studio_credits', 0) if user else 0
        rank = user.get('rank', 'Beginner') if user else 'Beginner'

        view = HelpView()

        embed = discord.Embed(
            title="📖 Ashtrails' Studio — Help Center",
            description=(
                f"Welcome, **{interaction.user.display_name}**! "
                f"You're a **{rank}** (Level {level}) with **{credits}** credits.\n\n"
                "Use the **dropdown menu** below to browse help categories, "
                "or click a quick button to get started!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=BOT_COLOR
        )

        embed.add_field(
            name="📂 Categories",
            value=(
                "🚀 Getting Started\n"
                "👤 Profile & Stats\n"
                "💰 Economy & Quests\n"
                "🛍️ Marketplace\n"
                "🤖 AI Features\n"
                "🎮 Fun & Games"
            ),
            inline=True
        )
        embed.add_field(
            name="📂 More",
            value=(
                "👥 Teams\n"
                "📚 Learning\n"
                "💎 Premium\n"
                "👑 Ranks\n"
                "📋 All Commands\n"
                "_ _"
            ),
            inline=True
        )

        embed.add_field(
            name="⚡ Quick Tips",
            value=(
                "• Start with `/start` to set up your profile\n"
                "• Use `/daily` every day for streak bonuses\n"
                "• `/quest` has 15 quests with big rewards\n"
                "• `/learn` teaches Lua/Luau in 50 lessons"
            ),
            inline=False
        )

        embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user else None)
        embed.set_footer(text="36 commands available • Select a category below!")

        await interaction.followup.send(embed=embed, view=view)

    @bot.tree.command(name="stats", description="📊 View server and bot statistics")
    async def stats_cmd(interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            from database import _memory_users, _memory_teams, _memory_marketplace
            user_count = len(_memory_users)
            team_count = len(_memory_teams)
            listing_count = len(_memory_marketplace)

            # Calculate extra stats
            total_credits = sum(u.get('studio_credits', 0) for u in _memory_users.values())
            total_pcredits = sum(u.get('pcredits', 0) for u in _memory_users.values())
            avg_level = round(
                sum(u.get('level', 1) for u in _memory_users.values()) / max(user_count, 1), 1
            )
            total_messages = sum(u.get('message_count', 0) for u in _memory_users.values())
            total_voice = sum(u.get('voice_minutes', 0) for u in _memory_users.values())

            active_listings = sum(
                1 for l in _memory_marketplace.values()
                if l.get('status') == 'active'
            )

            # Role distribution
            role_counts = {}
            for u in _memory_users.values():
                roles = u.get('roles', [])
                if isinstance(roles, list):
                    for r in roles:
                        role_counts[r] = role_counts.get(r, 0) + 1

            # Rank distribution
            rank_counts = {}
            for u in _memory_users.values():
                rank = u.get('rank', 'Beginner')
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

        except Exception:
            user_count = team_count = listing_count = 0
            total_credits = total_pcredits = 0
            avg_level = 0
            total_messages = total_voice = active_listings = 0
            role_counts = {}
            rank_counts = {}

        embed = discord.Embed(
            title="📊 Ashtrails' Studio Statistics",
            description="Live server analytics",
            color=BOT_COLOR
        )

        embed.add_field(name="👥 Developers", value=f"**{user_count}**", inline=True)
        embed.add_field(name="👥 Teams", value=f"**{team_count}**", inline=True)
        embed.add_field(name="🛍️ Listings", value=f"**{active_listings}** active / {listing_count} total", inline=True)

        embed.add_field(name="📊 Avg Level", value=f"**{avg_level}**", inline=True)
        embed.add_field(name="💬 Total Messages", value=f"**{total_messages:,}**", inline=True)
        embed.add_field(name="🎤 Voice Minutes", value=f"**{total_voice:,}**", inline=True)

        embed.add_field(
            name="💰 Economy",
            value=(
                f"💰 Total Credits: **{total_credits:,}**\n"
                f"💎 Total pCredits: **{total_pcredits:,}**"
            ),
            inline=False
        )

        if role_counts:
            role_lines = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
            role_text = " | ".join([f"**{r}**: {c}" for r, c in role_lines[:6]])
            embed.add_field(name="🎭 Role Distribution", value=role_text, inline=False)

        if rank_counts:
            rank_emojis = {"Beginner": "🥚", "Learner": "🌱", "Expert": "🔥", "Master": "👑"}
            rank_lines = []
            for rank_name in ["Master", "Expert", "Learner", "Beginner"]:
                if rank_name in rank_counts:
                    emoji = rank_emojis.get(rank_name, "")
                    rank_lines.append(f"{emoji} **{rank_name}**: {rank_counts[rank_name]}")
            if rank_lines:
                embed.add_field(name="👑 Rank Distribution", value=" | ".join(rank_lines), inline=False)

        embed.set_footer(text=f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        if interaction.guild:
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="setup", description="⚙️ Setup your profile and choose your role")
    async def setup_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)

        dm_embed = discord.Embed(
            title="⚙️ Ashtrails' Studio — Profile Setup",
            description=(
                "Welcome! Let's set up your developer profile.\n\n"
                "**Select your role(s) from the dropdown below.**\n"
                "You can choose multiple!"
            ),
            color=BOT_COLOR
        )
        dm_embed.add_field(
            name="🎭 Available Roles",
            value=(
                "🏗️ **Builder** — Structures & environments\n"
                "📝 **Scripter** — Lua/Luau code\n"
                "🎨 **Designer** — User interfaces\n"
                "⚙️ **Mesh Creator** — 3D meshes\n"
                "🎬 **Animator** — Characters & objects\n"
                "🟦 **Modeler** — 3D assets"
            ),
            inline=False
        )
        dm_embed.set_footer(text="You can change your roles anytime with /setup")

        view = SetupRoleView(interaction.user.id, GUILD_ID)

        try:
            await interaction.user.send(embed=dm_embed, view=view)
            await interaction.followup.send(
                "📩 Check your DMs! I've sent you the setup form.",
                ephemeral=True
            )
        except discord.Forbidden:
            fallback_embed = discord.Embed(
                title="⚙️ Ashtrails' Studio — Profile Setup",
                description=(
                    "⚠️ I couldn't DM you! Please enable DMs from server members.\n\n"
                    "**Select your role(s) below:**"
                ),
                color=BOT_COLOR
            )
            fallback_embed.add_field(
                name="🎭 Available Roles",
                value=(
                    "🏗️ Builder | 📝 Scripter | 🎨 Designer\n"
                    "⚙️ Mesh Creator | 🎬 Animator | 🟦 Modeler"
                ),
                inline=False
            )
            await interaction.followup.send(
                embed=fallback_embed, view=view, ephemeral=True
            )

    @bot.tree.command(name="start", description="🎯 START HERE — Setup your profile and get started!")
    async def start_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        # Check if already set up
        existing_roles = user.get('roles', [])
        if existing_roles and isinstance(existing_roles, list) and len(existing_roles) > 0:
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=(
                    f"You already have a profile set up!\n\n"
                    f"**Your Roles:** {', '.join(existing_roles)}\n"
                    f"**Rank:** {user.get('rank', 'Beginner')}\n"
                    f"**Level:** {user.get('level', 1)}\n"
                    f"**Credits:** 💰 {user.get('studio_credits', 0)}\n\n"
                    "Want to change your roles? Use `/setup` instead."
                ),
                color=BOT_COLOR
            )
            embed.add_field(
                name="📋 Quick Actions",
                value=(
                    "`/daily` — Claim daily reward\n"
                    "`/quest` — View quests\n"
                    "`/shop` — Browse marketplace\n"
                    "`/learn` — Start learning\n"
                    "`/help` — Full command list"
                ),
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        dm_embed = discord.Embed(
            title="🎯 Welcome to Ashtrails' Studio!",
            description=(
                "Let's get you started! 🚀\n\n"
                "**Step 1:** Select your developer role(s) below\n"
                "**Step 2:** Set your experience level\n"
                "**Step 3:** Start earning credits and XP!\n\n"
                "You'll receive **500 starting credits** to explore the marketplace!"
            ),
            color=discord.Color.green()
        )
        dm_embed.add_field(
            name="🎭 Choose Your Roles",
            value=(
                "🏗️ **Builder** — Build structures & environments\n"
                "📝 **Scripter** — Write Lua/Luau scripts\n"
                "🎨 **Designer** — Design user interfaces\n"
                "⚙️ **Mesh Creator** — Create 3D meshes\n"
                "🎬 **Animator** — Animate characters & objects\n"
                "🟦 **Modeler** — Model 3D assets"
            ),
            inline=False
        )
        dm_embed.set_footer(text="Select one or more roles from the dropdown below!")

        view = SetupRoleView(interaction.user.id, GUILD_ID)

        try:
            await interaction.user.send(embed=dm_embed, view=view)
            await interaction.followup.send(
                "📩 Check your DMs! I've sent you the setup form.\n"
                "*(If you don't see it, enable DMs from server members)*",
                ephemeral=True
            )
        except discord.Forbidden:
            fallback_embed = discord.Embed(
                title="🎯 Welcome to Ashtrails' Studio!",
                description=(
                    "⚠️ I couldn't DM you! Please enable DMs, or set up here:\n\n"
                    "**Select your role(s) from the dropdown below!**"
                ),
                color=BOT_COLOR
            )
            fallback_embed.add_field(
                name="🎭 Available Roles",
                value=(
                    "🏗️ Builder | 📝 Scripter | 🎨 Designer\n"
                    "⚙️ Mesh Creator | 🎬 Animator | 🟦 Modeler"
                ),
                inline=False
            )
            await interaction.followup.send(
                embed=fallback_embed, view=view, ephemeral=True
            )

    await bot.add_cog(InfoCog(bot))