import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, AI_MODEL, AI_PERSONALITY, AI_NAME
import asyncio
import random
import os
from google import genai

from ai_tools import ai_handler

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

genai_client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL
    }
)


async def call_ai(prompt):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: genai_client.models.generate_content(
                model=AI_MODEL,
                contents=prompt
            )
        )
        return response.text or "No response."
    except Exception as e:
        return f"❌ AI Error: {str(e)[:200]}"


SNIPPET_BOXES = {
    "common": {
        "chance": 60,
        "color": 0x95A5A6,
        "emoji": "⬜",
        "snippets": [
            {"name": "Hello World", "code": 'print("Hello, World!")', "desc": "The classic first script"},
            {"name": "Part Color Changer", "code": 'workspace.Part.BrickColor = BrickColor.new("Really red")', "desc": "Changes a part color"},
            {"name": "Simple Kill Brick", "code": 'script.Parent.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then hum.Health = 0 end\nend)', "desc": "A basic kill brick"},
            {"name": "Anchored Toggle", "code": 'local part = script.Parent\npart.Anchored = not part.Anchored', "desc": "Toggle part anchored state"},
            {"name": "Print Player Name", "code": 'game.Players.PlayerAdded:Connect(function(player)\n    print(player.Name .. " joined!")\nend)', "desc": "Prints when someone joins"},
        ]
    },
    "uncommon": {
        "chance": 25,
        "color": 0x2ECC71,
        "emoji": "🟩",
        "snippets": [
            {"name": "Part Spinner", "code": 'local part = script.Parent\nlocal RS = game:GetService("RunService")\nRS.Heartbeat:Connect(function(dt)\n    part.CFrame = part.CFrame * CFrame.Angles(0, math.rad(90) * dt, 0)\nend)', "desc": "Smoothly spinning part"},
            {"name": "Click Counter", "code": 'local cd = Instance.new("ClickDetector", script.Parent)\nlocal count = 0\ncd.MouseClick:Connect(function(player)\n    count = count + 1\n    print(player.Name .. " clicked! Total: " .. count)\nend)', "desc": "Counts clicks on a part"},
            {"name": "Rainbow Part", "code": 'local part = script.Parent\nwhile true do\n    for i = 0, 1, 0.01 do\n        part.Color = Color3.fromHSV(i, 1, 1)\n        task.wait(0.03)\n    end\nend', "desc": "Rainbow color cycling part"},
            {"name": "Speed Boost Pad", "code": 'script.Parent.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then\n        hum.WalkSpeed = 50\n        task.wait(5)\n        hum.WalkSpeed = 16\n    end\nend)', "desc": "Temporary speed boost"},
        ]
    },
    "rare": {
        "chance": 10,
        "color": 0x3498DB,
        "emoji": "🟦",
        "snippets": [
            {"name": "Music Color Sync", "code": 'local sound = workspace.Sound\nlocal part = script.Parent\nlocal RS = game:GetService("RunService")\nRS.Heartbeat:Connect(function()\n    local loud = sound.PlaybackLoudness / 500\n    part.Color = Color3.fromHSV(loud, 1, 1)\n    part.Size = Vector3.new(4 + loud * 3, 4 + loud * 3, 4 + loud * 3)\nend)', "desc": "Part reacts to music beat"},
            {"name": "Teleport Pad", "code": 'local padA = workspace.PadA\nlocal padB = workspace.PadB\nlocal db = {}\npadA.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    local hrp = hit.Parent:FindFirstChild("HumanoidRootPart")\n    if hum and hrp and not db[hum] then\n        db[hum] = true\n        hrp.CFrame = padB.CFrame + Vector3.new(0, 5, 0)\n        task.wait(2)\n        db[hum] = nil\n    end\nend)', "desc": "Two-way teleport pads"},
            {"name": "NPC Dialog", "code": 'local pp = Instance.new("ProximityPrompt")\npp.Parent = script.Parent\npp.ActionText = "Talk"\nlocal msgs = {"Hello!", "Nice day!", "Watch out!"}\nlocal i = 1\npp.Triggered:Connect(function()\n    game:GetService("Chat"):Chat(script.Parent, msgs[i])\n    i = i % #msgs + 1\nend)', "desc": "NPC with rotating dialog"},
        ]
    },
    "epic": {
        "chance": 4,
        "color": 0x9B59B6,
        "emoji": "🟪",
        "snippets": [
            {"name": "Trail System", "code": 'game.Players.PlayerAdded:Connect(function(p)\n    p.CharacterAdded:Connect(function(c)\n        local t = Instance.new("Trail")\n        local a0 = Instance.new("Attachment", c.Head)\n        local a1 = Instance.new("Attachment", c.HumanoidRootPart)\n        t.Attachment0 = a0\n        t.Attachment1 = a1\n        t.Lifetime = 0.5\n        t.Color = ColorSequence.new(Color3.fromRGB(255,0,255), Color3.fromRGB(0,255,255))\n        t.Transparency = NumberSequence.new(0, 1)\n        t.Parent = c\n    end)\nend)', "desc": "Auto trail for all players"},
            {"name": "Day/Night Cycle", "code": 'local L = game:GetService("Lighting")\nwhile true do\n    L.ClockTime = L.ClockTime + 0.01\n    if L.ClockTime >= 24 then L.ClockTime = 0 end\n    L.Brightness = (L.ClockTime > 6 and L.ClockTime < 18) and 2 or 0.5\n    task.wait(0.1)\nend', "desc": "Smooth day/night cycle"},
        ]
    },
    "legendary": {
        "chance": 1,
        "color": 0xF1C40F,
        "emoji": "🌟",
        "snippets": [
            {"name": "Horror Camera Shake", "code": 'local cam = workspace.CurrentCamera\nlocal RS = game:GetService("RunService")\nlocal shaking, intensity = false, 0\nlocal function shake(power, dur)\n    shaking = true; intensity = power\n    task.delay(dur, function() shaking = false; intensity = 0 end)\nend\nRS.RenderStepped:Connect(function()\n    if shaking then\n        cam.CFrame = cam.CFrame * CFrame.new(\n            math.random()*intensity - intensity/2,\n            math.random()*intensity - intensity/2,\n            math.random()*intensity - intensity/2\n        )\n    end\nend)\n-- shake(2, 3) to use', "desc": "Professional horror camera shake"},
            {"name": "Grid Placement System", "code": 'local UIS = game:GetService("UserInputService")\nlocal RS = game:GetService("RunService")\nlocal player = game.Players.LocalPlayer\nlocal mouse = player:GetMouse()\nlocal GRID = 2\nlocal placing, preview = false, nil\nlocal function snap(p)\n    return Vector3.new(math.round(p.X/GRID)*GRID, p.Y, math.round(p.Z/GRID)*GRID)\nend\nRS.RenderStepped:Connect(function()\n    if placing and preview then\n        preview:SetPrimaryPartCFrame(CFrame.new(snap(mouse.Hit.Position)))\n    end\nend)\nUIS.InputBegan:Connect(function(i)\n    if i.UserInputType == Enum.UserInputType.MouseButton1 and placing then\n        local f = preview:Clone()\n        for _,p in ipairs(f:GetDescendants()) do\n            if p:IsA("BasePart") then p.Transparency = 0; p.CanCollide = true end\n        end\n        f.Parent = workspace\n        preview:Destroy(); placing = false\n    end\nend)', "desc": "Grid placement system like Bloxburg"},
        ]
    }
}


def roll_snippet():
    roll = random.randint(1, 100)
    cumulative = 0
    for rarity, data in SNIPPET_BOXES.items():
        cumulative += data["chance"]
        if roll <= cumulative:
            snippet = random.choice(data["snippets"])
            return rarity, data, snippet
    return "common", SNIPPET_BOXES["common"], random.choice(SNIPPET_BOXES["common"]["snippets"])


DUEL_QUESTIONS = [
    {"q": "What function creates a new Instance in Roblox?", "options": ["Instance.new()", "Create()", "Spawn()", "Make()"], "correct": 0},
    {"q": "What service handles player data saving?", "options": ["DataStoreService", "SaveService", "PlayerData", "StorageService"], "correct": 0},
    {"q": "What property controls how fast a Humanoid walks?", "options": ["Speed", "WalkSpeed", "MoveSpeed", "RunSpeed"], "correct": 1},
    {"q": "What event fires when a player joins the game?", "options": ["PlayerJoined", "PlayerAdded", "OnJoin", "NewPlayer"], "correct": 1},
    {"q": "What is the max value of Transparency?", "options": ["100", "255", "1", "10"], "correct": 2},
    {"q": "Which service handles physics simulation?", "options": ["PhysicsService", "RunService", "SimService", "GameService"], "correct": 1},
    {"q": "What does task.wait() replace?", "options": ["delay()", "wait()", "sleep()", "pause()"], "correct": 1},
    {"q": "What property makes a Part not fall?", "options": ["Locked", "Fixed", "Anchored", "Static"], "correct": 2},
    {"q": "What is the Roblox scripting language called?", "options": ["Lua", "Luau", "RScript", "RobloxScript"], "correct": 1},
    {"q": "What service handles tweening?", "options": ["AnimService", "TweenService", "MoveService", "TransitionService"], "correct": 1},
    {"q": "What does pcall() do?", "options": ["Print call", "Protected call", "Player call", "Pause call"], "correct": 1},
    {"q": "How do you get the LocalPlayer?", "options": ["game.LocalPlayer", "Players.LocalPlayer", "GetPlayer()", "LocalPlayer()"], "correct": 1},
    {"q": "What RemoteEvent method does CLIENT use to send to server?", "options": ["FireClient", "FireServer", "SendServer", "Invoke"], "correct": 1},
    {"q": "What is the default WalkSpeed?", "options": ["10", "16", "20", "25"], "correct": 1},
    {"q": "Which folder is only visible to the server?", "options": ["ReplicatedStorage", "ServerStorage", "Workspace", "StarterPack"], "correct": 1},
]


class DuelAnswerView(discord.ui.View):
    def __init__(self, question, challenger_id, opponent_id, bet):
        super().__init__(timeout=15)
        self.question = question
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.bet = bet
        self.answers = {}
        self.correct = question["correct"]

        for i, option in enumerate(question["options"]):
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.blurple, custom_id=f"duel_{i}_{random.randint(1000,9999)}")
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid != self.challenger_id and uid != self.opponent_id:
                await interaction.response.send_message("❌ Not your duel!", ephemeral=True)
                return
            if uid in self.answers:
                await interaction.response.send_message("❌ Already answered!", ephemeral=True)
                return
            self.answers[uid] = {"choice": index, "correct": index == self.correct, "time": interaction.created_at.timestamp()}
            await interaction.response.send_message("✅ Answer locked!", ephemeral=True)
            if len(self.answers) == 2:
                self.stop()
        return callback


class BountyClaimView(discord.ui.View):
    def __init__(self, bounty_id, creator_id, reward):
        super().__init__(timeout=None)
        self.bounty_id = bounty_id
        self.creator_id = creator_id
        self.reward = reward
        self.claimed_by = None

    @discord.ui.button(label="🎯 Claim Bounty", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.creator_id:
            await interaction.response.send_message("❌ Can't claim your own bounty!", ephemeral=True)
            return
        if self.claimed_by:
            await interaction.response.send_message("❌ Already claimed!", ephemeral=True)
            return
        self.claimed_by = interaction.user.id
        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.grey
        embed = discord.Embed(title="🎯 Bounty Claimed!", description=f"**{interaction.user.display_name}** claimed this bounty!", color=0x2ECC71)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("❌ Only creator can cancel!", ephemeral=True)
            return
        await UserProfile.add_credits(self.creator_id, self.reward)
        embed = discord.Embed(title="❌ Bounty Cancelled", description=f"**{self.reward} Credits** refunded.", color=0xE74C3C)
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)


class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== 1. AI ROAST ==========
    @app_commands.command(name="ai-roast", description="💀 AI roasts a user based on their profile")
    @app_commands.describe(user="The user to roast")
    async def ai_roast(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        profile = await UserProfile.get_user(user.id)
        if not profile:
            await interaction.followup.send("❌ This user doesn't have a profile yet!")
            return

        roles = profile.get("roles", ["None"])
        rank = profile.get("rank", "Beginner")
        level = profile.get("level", 1)
        xp = profile.get("xp", 0)
        credits = profile.get("studio_credits", 0)
        messages = profile.get("message_count", 0)
        reputation = profile.get("reputation", 0)

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Write a devastating but FUNNY roast about this Roblox developer. "
            f"Be savage but playful and game-dev themed. Use their stats against them. "
            f"3-4 sentences max. Be creative.\n\n"
            f"TARGET: {user.display_name}\n"
            f"Roles: {', '.join(roles) if isinstance(roles, list) else roles}\n"
            f"Rank: {rank} | Level: {level} | XP: {xp}\n"
            f"Credits: {credits} | Messages: {messages} | Rep: {reputation}"
        )
        roast = await call_ai(prompt)

        embed = discord.Embed(title=f"💀 AI ROAST — {user.display_name}", description=roast, color=0xE74C3C)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Victim's Stats", value=f"Level {level} | {rank} | {credits} Credits", inline=False)
        embed.set_footer(text=f"Roasted by {AI_NAME} | Requested by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    # ========== 2. DEV BOUNTY ==========
    @app_commands.command(name="dev-bounty", description="💰 Post a bounty for other devs to claim")
    @app_commands.describe(task="What needs to be done", reward="Credits to offer")
    async def dev_bounty(self, interaction: discord.Interaction, task: str, reward: int):
        await interaction.response.defer()
        if reward < 100 or reward > 50000:
            await interaction.followup.send("❌ Reward must be between 100 and 50,000 Credits!")
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user or user.get("studio_credits", 0) < reward:
            await interaction.followup.send(f"❌ Not enough credits! You need {reward} Credits.")
            return

        await UserProfile.update_user(interaction.user.id, {"studio_credits": user["studio_credits"] - reward})
        bounty_id = f"bounty_{interaction.user.id}_{random.randint(1000,9999)}"

        embed = discord.Embed(
            title="💰 Dev Bounty Posted!",
            description=f"**Task:** {task}\n\n**Reward:** 💰 {reward} Credits\n**Posted by:** {interaction.user.mention}",
            color=0xF1C40F
        )
        embed.add_field(name="How to claim", value="Click 🎯 below!", inline=False)
        view = BountyClaimView(bounty_id, interaction.user.id, reward)
        await interaction.followup.send(embed=embed, view=view)

    # ========== 3. UNBOX SNIPPET ==========
    @app_commands.command(name="unbox-snippet", description="📦 Open a random code snippet box (500 Credits)")
    async def unbox_snippet(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        if not user or user.get("studio_credits", 0) < 500:
            await interaction.followup.send("❌ You need 500 Credits to unbox!")
            return

        await UserProfile.update_user(interaction.user.id, {"studio_credits": user["studio_credits"] - 500})

        msg = await interaction.followup.send("📦 Opening Code Box... 🎰", wait=True)
        await asyncio.sleep(1)
        await msg.edit(content="📦 Opening Code Box... 🎰 ✨✨✨")
        await asyncio.sleep(1)

        rarity, rarity_data, snippet = roll_snippet()

        embed = discord.Embed(
            title=f"{rarity_data['emoji']} {rarity.upper()} — {snippet['name']}!",
            description=f"**{snippet['desc']}**",
            color=rarity_data["color"]
        )
        embed.add_field(name="📝 Code", value=f"```lua\n{snippet['code'][:500]}\n```", inline=False)
        embed.add_field(name="Rarity", value=f"{rarity_data['emoji']} {rarity.upper()} ({rarity_data['chance']}%)", inline=True)
        embed.set_footer(text=f"Unboxed by {interaction.user.display_name}")
        await msg.edit(content=None, embed=embed)

    # ========== 4. FLEX WEALTH ==========
    @app_commands.command(name="flex-wealth", description="💎 Show the richest devs in the server")
    async def flex_wealth(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from database import _memory_users
        users = sorted(_memory_users.values(), key=lambda x: x.get("pcredits", 0), reverse=True)[:10]

        if not users:
            await interaction.followup.send("❌ No users found!")
            return

        embed = discord.Embed(title="💎💰 WEALTH LEADERBOARD 💰💎", description="*The richest devs in Ashtrails' Studio*\n\n💸💸💸\n", color=0xF1C40F)
        medals = ["👑", "💎", "🥇", "🥈", "🥉", "💰", "💰", "💰", "💰", "💰"]
        for i, u in enumerate(users):
            embed.add_field(name=f"{medals[i]} #{i+1} — {u.get('username', 'Unknown')}", value=f"💎 {u.get('pcredits', 0)} pCredits | 💰 {u.get('studio_credits', 0)} Credits", inline=False)
        embed.set_footer(text="💸 Get rich or die coding 💸")
        await interaction.followup.send(embed=embed)

    # ========== 5. CODE DUEL ==========
    @app_commands.command(name="code-duel", description="⚔️ Challenge someone to a Luau knowledge duel")
    @app_commands.describe(opponent="Who to challenge", bet="Credits to bet")
    async def code_duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int = 100):
        await interaction.response.defer()
        if opponent.bot:
            await interaction.followup.send("❌ Can't duel a bot!")
            return
        if opponent.id == interaction.user.id:
            await interaction.followup.send("❌ Can't duel yourself!")
            return
        if bet < 50 or bet > 10000:
            await interaction.followup.send("❌ Bet must be between 50 and 10,000 Credits!")
            return

        challenger = await UserProfile.get_user(interaction.user.id)
        opp_profile = await UserProfile.get_user(opponent.id)

        if not challenger or challenger.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ You don't have {bet} Credits!")
            return
        if not opp_profile or opp_profile.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ {opponent.display_name} doesn't have {bet} Credits!")
            return

        question = random.choice(DUEL_QUESTIONS)
        embed = discord.Embed(
            title="⚔️ CODE DUEL!",
            description=f"**{interaction.user.display_name}** vs **{opponent.display_name}**\n💰 **Bet:** {bet} Credits\n\n**Question:**\n{question['q']}\n\nBoth players click your answer! (15s)",
            color=0xE74C3C
        )
        view = DuelAnswerView(question, interaction.user.id, opponent.id, bet)
        await interaction.followup.send(embed=embed, view=view)
        await view.wait()

        ca = view.answers.get(interaction.user.id)
        oa = view.answers.get(opponent.id)
        correct_text = question["options"][question["correct"]]

        if not ca and not oa:
            result = discord.Embed(title="⚔️ Draw!", description="Neither answered! No credits lost.", color=0x95A5A6)
        elif not ca:
            await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] - bet})
            await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] + bet})
            result = discord.Embed(title=f"⚔️ {opponent.display_name} WINS!", description=f"{interaction.user.display_name} didn't answer!\n💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**", color=0x2ECC71)
        elif not oa:
            await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] - bet})
            await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] + bet})
            result = discord.Embed(title=f"⚔️ {interaction.user.display_name} WINS!", description=f"{opponent.display_name} didn't answer!\n💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**", color=0x2ECC71)
        elif ca["correct"] and not oa["correct"]:
            await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] - bet})
            await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] + bet})
            result = discord.Embed(title=f"⚔️ {interaction.user.display_name} WINS!", description=f"💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**", color=0x2ECC71)
        elif not ca["correct"] and oa["correct"]:
            await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] - bet})
            await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] + bet})
            result = discord.Embed(title=f"⚔️ {opponent.display_name} WINS!", description=f"💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**", color=0x2ECC71)
        elif ca["correct"] and oa["correct"]:
            if ca["time"] < oa["time"]:
                await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] - bet})
                await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] + bet})
                result = discord.Embed(title=f"⚔️ {interaction.user.display_name} WINS!", description=f"Both correct but faster! ⚡\n💰 Wins **{bet} Credits**!", color=0x2ECC71)
            else:
                await UserProfile.update_user(interaction.user.id, {"studio_credits": challenger["studio_credits"] - bet})
                await UserProfile.update_user(opponent.id, {"studio_credits": opp_profile["studio_credits"] + bet})
                result = discord.Embed(title=f"⚔️ {opponent.display_name} WINS!", description=f"Both correct but faster! ⚡\n💰 Wins **{bet} Credits**!", color=0x2ECC71)
        else:
            result = discord.Embed(title="⚔️ Draw!", description=f"Both wrong! No credits exchanged.\n✅ Answer: **{correct_text}**", color=0x95A5A6)

        await interaction.channel.send(embed=result)

    # ========== 6. AI FIX (1 AI Credit) ==========
    @app_commands.command(name="ai-fix", description="🔧 AI rewrites your code optimized (1 AI Credit)")
    @app_commands.describe(code="Paste your code here")
    async def ai_fix(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            if not user or user.get("ai_credits", 0) < 1:
                await interaction.followup.send("❌ You need 1 AI Credit! Use `/convert_ai`.")
                return
            await UserProfile.update_user(interaction.user.id, {"ai_credits": user["ai_credits"] - 1})

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Rewrite this code optimized, clean, and bug-free.\n"
            f"Show improved version with comments.\n\n"
            f"ORIGINAL:\n```lua\n{code}\n```\n\n"
            f"1. Brief list of fixes (2-3 points)\n2. Complete improved code in lua code block"
        )
        result = await call_ai(prompt)
        msg = await interaction.followup.send("🔧 Here's your optimized code:", wait=True)
        await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)

    # ========== 7. DEV CONFESSION ==========
    @app_commands.command(name="dev-confession", description="🤫 Submit an anonymous dev confession")
    @app_commands.describe(confession="Your anonymous confession")
    async def dev_confession(self, interaction: discord.Interaction, confession: str):
        await interaction.response.defer(ephemeral=True)
        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"A dev confessed: \"{confession}\"\n\n"
            f"Write a SHORT funny reaction (1-2 sentences). Be witty and relatable."
        )
        ai_comment = await call_ai(prompt)

        embed = discord.Embed(title="🤫 Anonymous Dev Confession", description=f"*\"{confession}\"*", color=0x9B59B6)
        embed.add_field(name=f"💬 {AI_NAME}'s Take", value=ai_comment[:1024], inline=False)
        embed.set_footer(text="Someone in this server wrote this... 👀")
        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Posted anonymously!", ephemeral=True)

    # ========== 8. AI PREDICT GAME (1 AI Credit) ==========
    @app_commands.command(name="ai-predict-game", description="🔮 AI predicts if your game will hit 1M plays (1 AI Credit)")
    @app_commands.describe(idea="Describe your game idea")
    async def ai_predict_game(self, interaction: discord.Interaction, idea: str):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            if not user or user.get("ai_credits", 0) < 1:
                await interaction.followup.send("❌ You need 1 AI Credit! Use `/convert_ai`.")
                return
            await UserProfile.update_user(interaction.user.id, {"ai_credits": user["ai_credits"] - 1})

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Analyze this Roblox game idea and predict success.\n\n"
            f"IDEA: {idea}\n\n"
            f"Provide:\n1. SUCCESS CHANCE: percentage\n2. VERDICT: 🟢/🟡/🔴\n"
            f"3. STRENGTHS: 2-3\n4. WEAKNESSES: 2-3\n5. COMPETITION\n"
            f"6. MONETIZATION\n7. DEV TIME\n8. KILLER TIP"
        )
        result = await call_ai(prompt)
        embed = discord.Embed(title="🔮 Game Prediction", description=f"**Idea:** {idea[:200]}", color=0x9B59B6)
        embed.set_footer(text=f"By {AI_NAME} | {interaction.user.display_name}")
        msg = await interaction.followup.send(embed=embed, wait=True)
        await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)

    # ========== 9. IDEAS (1 AI Credit) ==========
    @app_commands.command(name="ideas", description="💡 AI generates trending game ideas (1 AI Credit)")
    @app_commands.describe(keyword="Theme or keyword (optional)")
    async def ideas(self, interaction: discord.Interaction, keyword: str = None):
        await interaction.response.defer()
        user = await UserProfile.get_user(interaction.user.id)
        is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            if not user or user.get("ai_credits", 0) < 1:
                await interaction.followup.send("❌ You need 1 AI Credit! Use `/convert_ai`.")
                return
            await UserProfile.update_user(interaction.user.id, {"ai_credits": user["ai_credits"] - 1})

        kw = f"based on '{keyword}'" if keyword else "based on current Roblox trends"
        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Generate 3 creative Roblox game ideas {kw}.\n\n"
            f"For each:\n1. 🎮 NAME\n2. 📝 DESCRIPTION (2-3 sentences)\n"
            f"3. 🎯 GENRE\n4. 📊 PREDICTED VIEWS (first month)\n"
            f"5. ⏱️ DEV TIME\n6. 💰 MONETIZATION\n7. 🔥 WHY IT WORKS"
        )
        result = await call_ai(prompt)
        embed = discord.Embed(title="💡 Game Ideas", description=f"**Theme:** {keyword or 'Trending'}", color=0xF1C40F)
        embed.set_footer(text=f"By {AI_NAME} | {interaction.user.display_name}")
        msg = await interaction.followup.send(embed=embed, wait=True)
        await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)


async def setup(bot):
    await bot.add_cog(FunCog(bot))