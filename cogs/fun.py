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
        print(f"[AI Error] {e}")
        return f"❌ AI Error: {str(e)[:200]}"


# ==================== SNIPPET BOXES ====================
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


# ==================== DUEL QUESTIONS ====================
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
    {"q": "What does :Clone() return?", "options": ["Nothing", "A copy of the instance", "The original", "An error"], "correct": 1},
    {"q": "What method destroys an instance?", "options": ["Remove()", "Delete()", "Destroy()", "Kill()"], "correct": 2},
    {"q": "What does math.clamp() do?", "options": ["Rounds a number", "Constrains a value between min and max", "Returns absolute value", "Floors a number"], "correct": 1},
    {"q": "What is HumanoidRootPart?", "options": ["The head", "The primary part of a character", "A GUI element", "A sound"], "correct": 1},
    {"q": "What does :WaitForChild() do?", "options": ["Waits forever", "Yields until child exists", "Creates a child", "Deletes a child"], "correct": 1},
]


# ==================== DUEL VIEW ====================
class DuelAcceptView(discord.ui.View):
    """View for opponent to accept or decline a duel"""

    def __init__(self, challenger_id: int, opponent_id: int, bet: int):
        super().__init__(timeout=30)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.bet = bet
        self.accepted = False

    @discord.ui.button(label="Accept Duel", emoji="⚔️", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ This duel isn't for you!", ephemeral=True)
            return

        self.accepted = True
        button.disabled = True
        self.children[1].disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Decline", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ This duel isn't for you!", ephemeral=True)
            return

        self.accepted = False
        button.disabled = True
        self.children[0].disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚔️ Duel Declined",
                description=f"{interaction.user.display_name} declined the duel.",
                color=0x95A5A6
            ),
            view=self
        )
        self.stop()


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
            button = discord.ui.Button(
                label=option,
                style=discord.ButtonStyle.blurple,
                custom_id=f"duel_{i}_{random.randint(10000, 99999)}"
            )
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

            self.answers[uid] = {
                "choice": index,
                "correct": index == self.correct,
                "time": interaction.created_at.timestamp()
            }
            await interaction.response.send_message("✅ Answer locked!", ephemeral=True)

            if len(self.answers) == 2:
                self.stop()

        return callback


# ==================== BOUNTY VIEW ====================
class BountyClaimView(discord.ui.View):
    def __init__(self, bounty_id, creator_id, reward):
        super().__init__(timeout=86400)  # 24 hour timeout instead of None
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

        # Give reward to claimer
        await UserProfile.add_credits(interaction.user.id, self.reward)

        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.grey

        # Disable cancel button too
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="🎯 Bounty Claimed!",
            description=(
                f"**{interaction.user.display_name}** claimed this bounty!\n"
                f"💰 **{self.reward} Credits** awarded!"
            ),
            color=0x2ECC71
        )
        embed.add_field(name="Claimer", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reward", value=f"💰 {self.reward}", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("❌ Only the creator can cancel!", ephemeral=True)
            return
        if self.claimed_by:
            await interaction.response.send_message("❌ Already claimed, can't cancel!", ephemeral=True)
            return

        await UserProfile.add_credits(self.creator_id, self.reward)

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="❌ Bounty Cancelled",
            description=f"**{self.reward} Credits** refunded to {interaction.user.mention}.",
            color=0xE74C3C
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        """Refund if bounty expires unclaimed"""
        if not self.claimed_by:
            await UserProfile.add_credits(self.creator_id, self.reward)


# ==================== UNBOX ANIMATION ====================
UNBOX_FRAMES = [
    "📦 Opening Code Box... 🎰",
    "📦 Opening Code Box... 🎰 ✨",
    "📦 Opening Code Box... 🎰 ✨✨",
    "📦 Opening Code Box... 🎰 ✨✨✨",
    "💥 **REVEALED!** 💥",
]


# ==================== HELPER: SAFE ADMIN CHECK ====================
def is_user_admin(interaction: discord.Interaction) -> bool:
    """Safely check if user is admin"""
    try:
        if interaction.guild and hasattr(interaction.user, 'guild_permissions'):
            return interaction.user.guild_permissions.administrator
    except Exception:
        pass
    return False


# ==================== HELPER: CHECK AND DEDUCT AI CREDITS ====================
async def check_ai_credits(interaction: discord.Interaction, cost: int = 1) -> bool:
    """Check if user has enough AI credits. Returns True if ok to proceed."""
    if is_user_admin(interaction):
        return True

    user = await UserProfile.get_user(interaction.user.id)
    if not user:
        await UserProfile.create_user(interaction.user.id, interaction.user.name)
        user = await UserProfile.get_user(interaction.user.id)

    current_ai = user.get("ai_credits", 0)
    if current_ai < cost:
        embed = discord.Embed(
            title="❌ Not Enough AI Credits",
            description=(
                f"This command costs **{cost}** AI Credit(s).\n"
                f"You have **{current_ai}** AI Credits.\n\n"
                f"**Get more:**\n"
                f"`/convert` — Studio Credits → pCredits\n"
                f"`/convert_ai` — pCredits → AI Credits"
            ),
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return False

    await UserProfile.update_user(interaction.user.id, {
        "ai_credits": current_ai - cost
    })
    return True


async def refund_ai_credits(user_id: int, cost: int = 1):
    """Refund AI credits on error"""
    user = await UserProfile.get_user(user_id)
    if user:
        current = user.get("ai_credits", 0)
        await UserProfile.update_user(user_id, {
            "ai_credits": current + cost
        })


# ==================== FUN COG ====================
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== 1. AI ROAST ==========
    @app_commands.command(name="ai-roast", description="💀 AI roasts a user based on their profile")
    @app_commands.describe(user="The user to roast")
    async def ai_roast(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()

        if user.bot:
            await interaction.followup.send("❌ Can't roast a bot... or can I? No, I can't.")
            return

        profile = await UserProfile.get_user(user.id)
        if not profile:
            await interaction.followup.send(
                f"❌ {user.display_name} doesn't have a profile yet! "
                f"Tell them to use `/start`."
            )
            return

        # Check AI credits (1 credit for roast)
        if not await check_ai_credits(interaction, 1):
            return

        roles = profile.get("roles", profile.get("role", "None"))
        if isinstance(roles, list):
            roles = ", ".join(roles) if roles else "None"
        rank = profile.get("rank", "Beginner")
        level = profile.get("level", 1)
        xp = profile.get("xp", 0)
        credits = profile.get("studio_credits", 0)
        messages = profile.get("message_count", 0)
        reputation = profile.get("reputation", 0)
        voice = profile.get("voice_minutes", 0)

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Write a devastating but FUNNY roast about this Roblox developer. "
            f"Be savage but playful and game-dev themed. Use their stats against them. "
            f"3-4 sentences max. Be creative and specific to their stats.\n\n"
            f"TARGET: {user.display_name}\n"
            f"Roles: {roles}\n"
            f"Rank: {rank} | Level: {level} | XP: {xp}\n"
            f"Credits: {credits} | Messages: {messages} | Rep: {reputation}\n"
            f"Voice Minutes: {voice}"
        )

        try:
            roast = await call_ai(prompt)

            if roast.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(roast)
                return

            embed = discord.Embed(
                title=f"💀 AI ROAST — {user.display_name}",
                description=roast[:2000],
                color=0xE74C3C
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(
                name="Victim's Stats",
                value=f"Level {level} | {rank} | 💰 {credits} Credits | 💬 {messages} msgs",
                inline=False
            )
            embed.set_footer(
                text=f"Roasted by {AI_NAME} • Requested by {interaction.user.display_name} • 1 AI Credit"
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Roast failed: {str(e)[:200]}")

    # ========== 2. DEV BOUNTY ==========
    @app_commands.command(name="dev-bounty", description="💰 Post a bounty for other devs to claim")
    @app_commands.describe(task="What needs to be done", reward="Credits to offer (100-50000)")
    async def dev_bounty(self, interaction: discord.Interaction, task: str, reward: int):
        await interaction.response.defer()

        if reward < 100 or reward > 50000:
            await interaction.followup.send("❌ Reward must be between **100** and **50,000** Credits!")
            return

        if len(task) < 10:
            await interaction.followup.send("❌ Task description must be at least 10 characters!")
            return

        if len(task) > 500:
            await interaction.followup.send("❌ Task description must be under 500 characters!")
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if current_credits < reward:
            await interaction.followup.send(
                f"❌ Not enough credits! You need **{reward}** but have **{current_credits}**."
            )
            return

        # Deduct credits (escrow)
        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": current_credits - reward
        })

        bounty_id = f"bounty_{interaction.user.id}_{random.randint(10000, 99999)}"

        embed = discord.Embed(
            title="💰 Dev Bounty Posted!",
            description=(
                f"**Task:** {task}\n\n"
                f"**Reward:** 💰 {reward} Credits\n"
                f"**Posted by:** {interaction.user.mention}\n"
                f"**Expires:** 24 hours"
            ),
            color=0xF1C40F
        )
        embed.add_field(
            name="How to claim",
            value="Click 🎯 **Claim Bounty** below!\nThe poster will verify completion.",
            inline=False
        )
        embed.set_footer(text=f"Bounty ID: {bounty_id}")

        view = BountyClaimView(bounty_id, interaction.user.id, reward)
        await interaction.followup.send(embed=embed, view=view)

    # ========== 3. UNBOX SNIPPET ==========
    @app_commands.command(name="unbox-snippet", description="📦 Open a random code snippet box (500 Credits)")
    async def unbox_snippet(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if current_credits < 500:
            await interaction.followup.send(
                f"❌ You need **500 Credits** to unbox! You have **{current_credits}**.\n"
                f"Earn more through `/daily` and `/quest`!"
            )
            return

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": current_credits - 500
        })

        # Animated unboxing
        msg = await interaction.followup.send(UNBOX_FRAMES[0], wait=True)
        for frame in UNBOX_FRAMES[1:]:
            await asyncio.sleep(0.8)
            try:
                await msg.edit(content=frame)
            except Exception:
                pass

        rarity, rarity_data, snippet = roll_snippet()

        # Bonus XP for rare+ unboxes
        xp_bonus = {"common": 5, "uncommon": 10, "rare": 25, "epic": 50, "legendary": 100}
        bonus = xp_bonus.get(rarity, 5)
        await UserProfile.add_xp(interaction.user.id, bonus)

        embed = discord.Embed(
            title=f"{rarity_data['emoji']} {rarity.upper()} — {snippet['name']}!",
            description=f"**{snippet['desc']}**",
            color=rarity_data["color"]
        )

        code_text = snippet['code']
        if len(code_text) > 900:
            code_text = code_text[:900] + "\n-- ... (truncated)"

        embed.add_field(name="📝 Code", value=f"```lua\n{code_text}\n```", inline=False)
        embed.add_field(
            name="Rarity",
            value=f"{rarity_data['emoji']} {rarity.upper()} ({rarity_data['chance']}% chance)",
            inline=True
        )
        embed.add_field(name="Bonus XP", value=f"✨ +{bonus}", inline=True)
        embed.set_footer(text=f"Unboxed by {interaction.user.display_name} | 500 Credits spent")

        await msg.edit(content=None, embed=embed)

    # ========== 4. FLEX WEALTH ==========
    @app_commands.command(name="flex-wealth", description="💎 Show the richest devs in the server")
    async def flex_wealth(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from database import _memory_users

        if not _memory_users:
            await interaction.followup.send("❌ No users found!")
            return

        # Sort by total wealth (pcredits * 1000 + studio_credits) for fair ranking
        users = sorted(
            _memory_users.values(),
            key=lambda x: (x.get("pcredits", 0) * 1000) + x.get("studio_credits", 0),
            reverse=True
        )[:10]

        if not users:
            await interaction.followup.send("❌ No users found!")
            return

        embed = discord.Embed(
            title="💎💰 WEALTH LEADERBOARD 💰💎",
            description="*The richest devs in the studio*\n",
            color=0xF1C40F
        )

        medals = ["👑", "💎", "🥇", "🥈", "🥉", "💰", "💰", "💰", "💰", "💰"]
        for i, u in enumerate(users):
            pcredits = u.get('pcredits', 0)
            credits = u.get('studio_credits', 0)
            ai_credits = u.get('ai_credits', 0)
            total = (pcredits * 1000) + credits

            embed.add_field(
                name=f"{medals[i]} #{i + 1} — {u.get('username', 'Unknown')}",
                value=(
                    f"💎 {pcredits} pCredits | 💰 {credits} Credits | 🤖 {ai_credits} AI\n"
                    f"📊 Total Value: **{total:,}** Credits"
                ),
                inline=False
            )

        embed.set_footer(text="💸 Get rich or die coding 💸 | Total = (pCredits × 1000) + Credits")
        await interaction.followup.send(embed=embed)

    # ========== 5. CODE DUEL ==========
    @app_commands.command(name="code-duel", description="⚔️ Challenge someone to a Luau knowledge duel")
    @app_commands.describe(opponent="Who to challenge", bet="Credits to bet (50-10000)")
    async def code_duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int = 100):
        await interaction.response.defer()

        if opponent.bot:
            await interaction.followup.send("❌ Can't duel a bot!")
            return
        if opponent.id == interaction.user.id:
            await interaction.followup.send("❌ Can't duel yourself!")
            return
        if bet < 50 or bet > 10000:
            await interaction.followup.send("❌ Bet must be between **50** and **10,000** Credits!")
            return

        challenger = await UserProfile.get_user(interaction.user.id)
        if not challenger:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            challenger = await UserProfile.get_user(interaction.user.id)

        opp_profile = await UserProfile.get_user(opponent.id)
        if not opp_profile:
            await UserProfile.create_user(opponent.id, opponent.name)
            opp_profile = await UserProfile.get_user(opponent.id)

        challenger_credits = challenger.get("studio_credits", 0)
        opp_credits = opp_profile.get("studio_credits", 0)

        if challenger_credits < bet:
            await interaction.followup.send(
                f"❌ You don't have **{bet}** Credits! You have **{challenger_credits}**."
            )
            return
        if opp_credits < bet:
            await interaction.followup.send(
                f"❌ {opponent.display_name} doesn't have **{bet}** Credits!"
            )
            return

        # Ask opponent to accept first
        accept_embed = discord.Embed(
            title="⚔️ Duel Challenge!",
            description=(
                f"**{interaction.user.display_name}** challenges **{opponent.display_name}**!\n"
                f"💰 **Bet:** {bet} Credits\n\n"
                f"{opponent.mention}, do you accept?"
            ),
            color=0xE74C3C
        )
        accept_view = DuelAcceptView(interaction.user.id, opponent.id, bet)
        await interaction.followup.send(embed=accept_embed, view=accept_view)

        await accept_view.wait()

        if not accept_view.accepted:
            if accept_view.accepted is None:
                # Timed out
                timeout_embed = discord.Embed(
                    title="⚔️ Duel Expired",
                    description=f"{opponent.display_name} didn't respond in time.",
                    color=0x95A5A6
                )
                try:
                    await interaction.edit_original_response(embed=timeout_embed, view=None)
                except Exception:
                    pass
            return

        # Re-fetch balances to prevent exploit
        challenger = await UserProfile.get_user(interaction.user.id)
        opp_profile = await UserProfile.get_user(opponent.id)
        challenger_credits = challenger.get("studio_credits", 0)
        opp_credits = opp_profile.get("studio_credits", 0)

        if challenger_credits < bet or opp_credits < bet:
            await interaction.channel.send("❌ Someone doesn't have enough credits anymore! Duel cancelled.")
            return

        # Start the duel
        question = random.choice(DUEL_QUESTIONS)
        duel_embed = discord.Embed(
            title="⚔️ CODE DUEL — FIGHT!",
            description=(
                f"**{interaction.user.display_name}** vs **{opponent.display_name}**\n"
                f"💰 **Bet:** {bet} Credits\n\n"
                f"**Question:**\n{question['q']}\n\n"
                f"⏱️ Both players click your answer! (15 seconds)"
            ),
            color=0xE74C3C
        )

        answer_view = DuelAnswerView(question, interaction.user.id, opponent.id, bet)
        duel_msg = await interaction.channel.send(embed=duel_embed, view=answer_view)

        await answer_view.wait()

        ca = answer_view.answers.get(interaction.user.id)
        oa = answer_view.answers.get(opponent.id)
        correct_text = question["options"][question["correct"]]

        # Determine winner
        winner_id = None
        loser_id = None
        result_title = ""
        result_desc = ""

        if not ca and not oa:
            result_title = "⚔️ Draw!"
            result_desc = f"Neither player answered!\nNo credits exchanged.\n✅ Answer: **{correct_text}**"

        elif not ca:
            winner_id = opponent.id
            loser_id = interaction.user.id
            result_title = f"⚔️ {opponent.display_name} WINS!"
            result_desc = (
                f"{interaction.user.display_name} didn't answer!\n"
                f"💰 {opponent.display_name} wins **{bet} Credits**!\n"
                f"✅ Answer: **{correct_text}**"
            )

        elif not oa:
            winner_id = interaction.user.id
            loser_id = opponent.id
            result_title = f"⚔️ {interaction.user.display_name} WINS!"
            result_desc = (
                f"{opponent.display_name} didn't answer!\n"
                f"💰 {interaction.user.display_name} wins **{bet} Credits**!\n"
                f"✅ Answer: **{correct_text}**"
            )

        elif ca["correct"] and not oa["correct"]:
            winner_id = interaction.user.id
            loser_id = opponent.id
            result_title = f"⚔️ {interaction.user.display_name} WINS!"
            result_desc = f"💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**"

        elif not ca["correct"] and oa["correct"]:
            winner_id = opponent.id
            loser_id = interaction.user.id
            result_title = f"⚔️ {opponent.display_name} WINS!"
            result_desc = f"💰 Wins **{bet} Credits**!\n✅ Answer: **{correct_text}**"

        elif ca["correct"] and oa["correct"]:
            # Both correct — fastest wins
            if ca["time"] < oa["time"]:
                winner_id = interaction.user.id
                loser_id = opponent.id
                result_title = f"⚔️ {interaction.user.display_name} WINS!"
                result_desc = f"Both correct but **faster**! ⚡\n💰 Wins **{bet} Credits**!"
            elif oa["time"] < ca["time"]:
                winner_id = opponent.id
                loser_id = interaction.user.id
                result_title = f"⚔️ {opponent.display_name} WINS!"
                result_desc = f"Both correct but **faster**! ⚡\n💰 Wins **{bet} Credits**!"
            else:
                result_title = "⚔️ Perfect Draw!"
                result_desc = f"Both correct at the exact same time!\nNo credits exchanged.\n✅ Answer: **{correct_text}**"
        else:
            result_title = "⚔️ Draw!"
            result_desc = f"Both wrong! No credits exchanged.\n✅ Answer: **{correct_text}**"

        # Transfer credits
        if winner_id and loser_id:
            # Re-fetch to prevent race conditions
            winner_data = await UserProfile.get_user(winner_id)
            loser_data = await UserProfile.get_user(loser_id)

            if winner_data and loser_data:
                loser_credits = loser_data.get("studio_credits", 0)
                winner_credits = winner_data.get("studio_credits", 0)

                # Make sure loser can still pay
                actual_bet = min(bet, loser_credits)
                if actual_bet > 0:
                    await UserProfile.update_user(loser_id, {
                        "studio_credits": loser_credits - actual_bet
                    })
                    await UserProfile.update_user(winner_id, {
                        "studio_credits": winner_credits + actual_bet
                    })

        color = 0x2ECC71 if winner_id else 0x95A5A6
        result_embed = discord.Embed(title=result_title, description=result_desc, color=color)
        await interaction.channel.send(embed=result_embed)

    # ========== 6. AI FIX (1 AI Credit) ==========
    @app_commands.command(name="ai-fix", description="🔧 AI rewrites your code optimized (1 AI Credit)")
    @app_commands.describe(code="Paste your code here")
    async def ai_fix(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer()

        if len(code.strip()) < 5:
            await interaction.followup.send("❌ Code is too short! Paste some actual code.")
            return

        if not await check_ai_credits(interaction, 1):
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Rewrite this Roblox Lua/Luau code to be optimized, clean, and bug-free.\n"
            f"Show the improved version with clear comments explaining changes.\n\n"
            f"ORIGINAL:\n```lua\n{code[:3000]}\n```\n\n"
            f"Provide:\n"
            f"1. Brief list of fixes/improvements (2-4 bullet points)\n"
            f"2. Complete improved code in a lua code block\n"
            f"3. One-line performance note"
        )

        try:
            result = await call_ai(prompt)

            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(
                title="🔧 Code Optimized!",
                description=f"By {AI_NAME} • Cost: 1 AI Credit",
                color=0x3498DB
            )
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")

            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name
            )

        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 7. DEV CONFESSION ==========
    @app_commands.command(name="dev-confession", description="🤫 Submit an anonymous dev confession")
    @app_commands.describe(confession="Your anonymous confession")
    async def dev_confession(self, interaction: discord.Interaction, confession: str):
        await interaction.response.defer(ephemeral=True)

        if len(confession.strip()) < 10:
            await interaction.followup.send("❌ Confession must be at least 10 characters!", ephemeral=True)
            return

        if len(confession) > 500:
            await interaction.followup.send("❌ Confession must be under 500 characters!", ephemeral=True)
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"A dev confessed: \"{confession}\"\n\n"
            f"Write a SHORT funny reaction (1-2 sentences max). Be witty and relatable to game devs."
        )

        try:
            ai_comment = await call_ai(prompt)

            embed = discord.Embed(
                title="🤫 Anonymous Dev Confession",
                description=f"*\"{confession}\"*",
                color=0x9B59B6
            )
            embed.add_field(
                name=f"💬 {AI_NAME}'s Take",
                value=ai_comment[:1024] if not ai_comment.startswith("❌") else "No comment. 😶",
                inline=False
            )
            embed.set_footer(text="Someone in this server wrote this... 👀")

            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ Posted anonymously!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to post: {str(e)[:200]}", ephemeral=True)

    # ========== 8. AI PREDICT GAME (1 AI Credit) ==========
    @app_commands.command(name="ai-predict-game", description="🔮 AI predicts if your game will hit 1M plays (1 AI Credit)")
    @app_commands.describe(idea="Describe your game idea")
    async def ai_predict_game(self, interaction: discord.Interaction, idea: str):
        await interaction.response.defer()

        if len(idea.strip()) < 10:
            await interaction.followup.send("❌ Describe your idea in at least 10 characters!")
            return

        if not await check_ai_credits(interaction, 1):
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Analyze this Roblox game idea and predict success. Be honest but helpful.\n\n"
            f"IDEA: {idea[:1000]}\n\n"
            f"Provide:\n"
            f"1. SUCCESS CHANCE: percentage (be realistic)\n"
            f"2. VERDICT: 🟢 Go for it / 🟡 Needs work / 🔴 Risky\n"
            f"3. STRENGTHS: 2-3 bullet points\n"
            f"4. WEAKNESSES: 2-3 bullet points\n"
            f"5. COMPETITION: Similar games on Roblox\n"
            f"6. MONETIZATION: Best strategy\n"
            f"7. DEV TIME: Estimated hours/weeks\n"
            f"8. KILLER TIP: One actionable advice"
        )

        try:
            result = await call_ai(prompt)

            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(
                title="🔮 Game Prediction",
                description=f"**Idea:** {idea[:200]}{'...' if len(idea) > 200 else ''}",
                color=0x9B59B6
            )
            embed.set_footer(
                text=f"By {AI_NAME} • {interaction.user.display_name} • 1 AI Credit"
            )

            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name
            )

        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 9. IDEAS (1 AI Credit) ==========
    @app_commands.command(name="ideas", description="💡 AI generates trending game ideas (1 AI Credit)")
    @app_commands.describe(keyword="Theme or keyword (optional)")
    async def ideas(self, interaction: discord.Interaction, keyword: str = None):
        await interaction.response.defer()

        if not await check_ai_credits(interaction, 1):
            return

        kw = f"based on the theme '{keyword}'" if keyword else "based on current Roblox trends in 2024-2025"
        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Generate 3 creative and unique Roblox game ideas {kw}.\n\n"
            f"For each idea provide:\n"
            f"1. 🎮 NAME (creative title)\n"
            f"2. 📝 DESCRIPTION (2-3 sentences)\n"
            f"3. 🎯 GENRE\n"
            f"4. 📊 PREDICTED PLAYS (first month)\n"
            f"5. ⏱️ DEV TIME (realistic)\n"
            f"6. 💰 MONETIZATION (gamepass ideas)\n"
            f"7. 🔥 WHY IT WOULD WORK"
        )

        try:
            result = await call_ai(prompt)

            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(
                title="💡 Game Ideas Generator",
                description=f"**Theme:** {keyword or 'Trending 2024-2025'}",
                color=0xF1C40F
            )
            embed.set_footer(
                text=f"By {AI_NAME} • {interaction.user.display_name} • 1 AI Credit"
            )

            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name
            )

        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 10. COIN FLIP (NEW) ==========
    @app_commands.command(name="coinflip", description="🪙 Flip a coin and bet credits!")
    @app_commands.describe(
        choice="Heads or Tails",
        bet="Credits to bet (0 for free flip)"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails"),
    ])
    async def coinflip(self, interaction: discord.Interaction, choice: str, bet: int = 0):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)

        if bet < 0:
            await interaction.followup.send("❌ Bet can't be negative!")
            return

        if bet > 5000:
            await interaction.followup.send("❌ Max bet is **5,000** Credits!")
            return

        if bet > 0 and current_credits < bet:
            await interaction.followup.send(
                f"❌ Not enough credits! You have **{current_credits}** but bet **{bet}**."
            )
            return

        result = random.choice(["heads", "tails"])
        won = result == choice

        # Animate
        msg = await interaction.followup.send("🪙 Flipping...", wait=True)
        await asyncio.sleep(1)
        await msg.edit(content="🪙 Flipping... 🌀")
        await asyncio.sleep(0.8)

        result_emoji = "👑" if result == "heads" else "🔮"

        if bet > 0:
            if won:
                await UserProfile.update_user(interaction.user.id, {
                    "studio_credits": current_credits + bet
                })
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU WIN!",
                    description=f"💰 You won **{bet}** Credits!\nNew balance: **{current_credits + bet}** Credits",
                    color=0x2ECC71
                )
            else:
                await UserProfile.update_user(interaction.user.id, {
                    "studio_credits": current_credits - bet
                })
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU LOSE!",
                    description=f"💸 You lost **{bet}** Credits!\nNew balance: **{current_credits - bet}** Credits",
                    color=0xE74C3C
                )
        else:
            embed = discord.Embed(
                title=f"{result_emoji} {result.upper()}!",
                description=f"{'✅ You guessed right!' if won else '❌ Wrong guess!'}",
                color=0x2ECC71 if won else 0xE74C3C
            )

        embed.add_field(name="Your Pick", value=choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        embed.set_footer(text=f"Flipped by {interaction.user.display_name}")

        await msg.edit(content=None, embed=embed)

    # ========== 11. DEV TRIVIA (NEW - Free) ==========
    @app_commands.command(name="trivia", description="🧠 Quick Roblox dev trivia question (free!)")
    async def trivia(self, interaction: discord.Interaction):
        await interaction.response.defer()

        question = random.choice(DUEL_QUESTIONS)

        embed = discord.Embed(
            title="🧠 Dev Trivia!",
            description=f"**{question['q']}**\n\n⏱️ You have 15 seconds!",
            color=0x3498DB
        )

        view = TriviaView(question, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)

        await view.wait()

        answer = view.user_answer
        correct_text = question["options"][question["correct"]]

        if answer is None:
            result = discord.Embed(
                title="⏱️ Time's Up!",
                description=f"✅ The answer was: **{correct_text}**",
                color=0x95A5A6
            )
        elif answer == question["correct"]:
            # Give small XP reward
            await UserProfile.add_xp(interaction.user.id, 15)
            await UserProfile.add_credits(interaction.user.id, 5)
            result = discord.Embed(
                title="✅ Correct!",
                description=f"**{correct_text}**\n\n✨ +15 XP | 💰 +5 Credits",
                color=0x2ECC71
            )
        else:
            result = discord.Embed(
                title="❌ Wrong!",
                description=(
                    f"You picked: **{question['options'][answer]}**\n"
                    f"✅ Correct answer: **{correct_text}**"
                ),
                color=0xE74C3C
            )

        result.set_footer(text=f"Player: {interaction.user.display_name}")
        await interaction.channel.send(embed=result)


# ==================== TRIVIA VIEW ====================
class TriviaView(discord.ui.View):
    def __init__(self, question, user_id):
        super().__init__(timeout=15)
        self.question = question
        self.user_id = user_id
        self.user_answer = None

        for i, option in enumerate(question["options"]):
            button = discord.ui.Button(
                label=option,
                style=discord.ButtonStyle.blurple,
                custom_id=f"trivia_{i}_{random.randint(10000, 99999)}"
            )
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not your trivia!", ephemeral=True)
                return
            if self.user_answer is not None:
                await interaction.response.send_message("❌ Already answered!", ephemeral=True)
                return

            self.user_answer = index

            # Disable all buttons
            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(view=self)
            self.stop()

        return callback


async def setup(bot):
    await bot.add_cog(FunCog(bot))