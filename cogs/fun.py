import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, AI_MODEL, AI_PERSONALITY, AI_NAME
import asyncio
import random
import json
import os
import time
from anthropic import Anthropic

from ai_tools import ai_handler

# Anthropic Integration Setup
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

anthropic_client = Anthropic(
    api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
    base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
)

async def call_ai(prompt):
    try:
        response = await asyncio.to_thread(
            anthropic_client.messages.create,
            model=AI_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"[AI Error] {e}")
        return f"❌ AI Error: {str(e)[:200]}"


# ============================================================
# AI TRIVIA GENERATOR
# ============================================================

TRIVIA_CATEGORIES = {
    "scripting": {
        "emoji": "📝",
        "name": "Luau Scripting",
        "description": "Roblox Luau/Lua coding questions"
    },
    "studio": {
        "emoji": "🏗️",
        "name": "Roblox Studio",
        "description": "Studio tools, UI, and workflow"
    },
    "services": {
        "emoji": "⚙️",
        "name": "Roblox Services",
        "description": "DataStore, RemoteEvents, TweenService, etc."
    },
    "physics": {
        "emoji": "🎱",
        "name": "Physics & Math",
        "description": "CFrame, Vector3, raycasting, physics"
    },
    "ui": {
        "emoji": "🖼️",
        "name": "UI/UX Design",
        "description": "GUI, ScreenGui, frames, buttons"
    },
    "security": {
        "emoji": "🔒",
        "name": "Game Security",
        "description": "Anti-exploit, server validation, remotes"
    },
    "optimization": {
        "emoji": "⚡",
        "name": "Performance",
        "description": "Optimization, memory, lag prevention"
    },
    "general": {
        "emoji": "🎮",
        "name": "General Roblox",
        "description": "Platform knowledge, history, features"
    },
    "random": {
        "emoji": "🎲",
        "name": "Random",
        "description": "Any category!"
    }
}

TRIVIA_DIFFICULTIES = {
    "easy": {"emoji": "🟢", "xp": 10, "credits": 5, "color": 0x2ECC71},
    "medium": {"emoji": "🟡", "xp": 20, "credits": 10, "color": 0xF1C40F},
    "hard": {"emoji": "🟠", "xp": 35, "credits": 20, "color": 0xE67E22},
    "expert": {"emoji": "🔴", "xp": 50, "credits": 35, "color": 0xE74C3C},
    "demon": {"emoji": "💀", "xp": 100, "credits": 75, "color": 0x8B0000},
}

# 40 fallback questions (20 original + 20 new)
FALLBACK_QUESTIONS = [
    # ===== ORIGINAL 20 =====
    {"q": "What function creates a new Instance in Roblox?", "options": ["Instance.new()", "Create()", "Spawn()", "Make()"], "correct": 0, "category": "scripting", "difficulty": "easy", "explanation": "Instance.new() is the standard way to create new objects in Roblox."},
    {"q": "What service handles player data saving?", "options": ["DataStoreService", "SaveService", "PlayerData", "StorageService"], "correct": 0, "category": "services", "difficulty": "easy", "explanation": "DataStoreService provides access to persistent data storage."},
    {"q": "What property controls how fast a Humanoid walks?", "options": ["Speed", "WalkSpeed", "MoveSpeed", "RunSpeed"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": "WalkSpeed is the property that controls movement speed, default is 16."},
    {"q": "What event fires when a player joins the game?", "options": ["PlayerJoined", "PlayerAdded", "OnJoin", "NewPlayer"], "correct": 1, "category": "services", "difficulty": "easy", "explanation": "Players.PlayerAdded fires when a new player enters the game."},
    {"q": "What is the max value of Transparency?", "options": ["100", "255", "1", "10"], "correct": 2, "category": "scripting", "difficulty": "easy", "explanation": "Transparency ranges from 0 (opaque) to 1 (invisible)."},
    {"q": "Which service handles physics simulation?", "options": ["PhysicsService", "RunService", "SimService", "GameService"], "correct": 1, "category": "physics", "difficulty": "medium", "explanation": "RunService provides events like Heartbeat and RenderStepped for physics and rendering."},
    {"q": "What does task.wait() replace?", "options": ["delay()", "wait()", "sleep()", "pause()"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": "task.wait() is the modern replacement for the deprecated wait() function."},
    {"q": "What property makes a Part not fall?", "options": ["Locked", "Fixed", "Anchored", "Static"], "correct": 2, "category": "physics", "difficulty": "easy", "explanation": "Anchored = true prevents a part from being affected by physics."},
    {"q": "What is the Roblox scripting language called?", "options": ["Lua", "Luau", "RScript", "RobloxScript"], "correct": 1, "category": "general", "difficulty": "easy", "explanation": "Luau is Roblox's custom fork of Lua with type checking and performance improvements."},
    {"q": "What service handles tweening?", "options": ["AnimService", "TweenService", "MoveService", "TransitionService"], "correct": 1, "category": "services", "difficulty": "easy", "explanation": "TweenService creates smooth property transitions over time."},
    {"q": "What does pcall() do?", "options": ["Print call", "Protected call", "Player call", "Pause call"], "correct": 1, "category": "scripting", "difficulty": "medium", "explanation": "pcall() runs a function in protected mode, catching errors instead of crashing."},
    {"q": "How do you get the LocalPlayer?", "options": ["game.LocalPlayer", "Players.LocalPlayer", "GetPlayer()", "LocalPlayer()"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": "game:GetService('Players').LocalPlayer or game.Players.LocalPlayer."},
    {"q": "What RemoteEvent method does CLIENT use to send to server?", "options": ["FireClient", "FireServer", "SendServer", "Invoke"], "correct": 1, "category": "security", "difficulty": "medium", "explanation": "Clients use :FireServer() to send data to the server via RemoteEvents."},
    {"q": "What is the default WalkSpeed?", "options": ["10", "16", "20", "25"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": "The default Humanoid WalkSpeed is 16 studs per second."},
    {"q": "Which folder is only visible to the server?", "options": ["ReplicatedStorage", "ServerStorage", "Workspace", "StarterPack"], "correct": 1, "category": "security", "difficulty": "medium", "explanation": "ServerStorage contents are only accessible from server scripts."},
    {"q": "What does :Clone() return?", "options": ["Nothing", "A copy of the instance", "The original", "An error"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": ":Clone() creates and returns a deep copy of the instance."},
    {"q": "What method destroys an instance?", "options": ["Remove()", "Delete()", "Destroy()", "Kill()"], "correct": 2, "category": "scripting", "difficulty": "easy", "explanation": ":Destroy() permanently removes an instance and disconnects all connections."},
    {"q": "What does math.clamp() do?", "options": ["Rounds a number", "Constrains between min/max", "Returns absolute value", "Floors a number"], "correct": 1, "category": "scripting", "difficulty": "medium", "explanation": "math.clamp(value, min, max) constrains a value within a range."},
    {"q": "What is HumanoidRootPart?", "options": ["The head", "The primary part of a character", "A GUI element", "A sound"], "correct": 1, "category": "scripting", "difficulty": "easy", "explanation": "HumanoidRootPart is the root/primary part that controls character position."},
    {"q": "What does :WaitForChild() do?", "options": ["Waits forever", "Yields until child exists", "Creates a child", "Deletes a child"], "correct": 1, "category": "scripting", "difficulty": "medium", "explanation": ":WaitForChild() pauses the script until the named child instance appears."},

    # ===== 20 NEW HARDER QUESTIONS =====
    {"q": "What metamethod is called when you index a table with a missing key?", "options": ["__newindex", "__index", "__call", "__tostring"], "correct": 1, "category": "scripting", "difficulty": "hard", "explanation": "__index is invoked when accessing a key that doesn't exist in the table."},
    {"q": "What is the maximum number of requests per minute for OrderedDataStore:GetSortedAsync()?", "options": ["60", "30", "5", "100"], "correct": 2, "category": "services", "difficulty": "expert", "explanation": "OrderedDataStore:GetSortedAsync() has a limit of 5 requests per minute per key."},
    {"q": "What CFrame method returns only the rotational component?", "options": ["CFrame.Angles()", "CFrame:GetComponents()", "CFrame.Rotation", "CFrame:ToEulerAngles()"], "correct": 2, "category": "physics", "difficulty": "hard", "explanation": "CFrame.Rotation returns a copy of the CFrame with position zeroed out, keeping only rotation."},
    {"q": "In a client-server model, where should RemoteEvent data validation happen?", "options": ["Client only", "Both equally", "Server only", "Neither"], "correct": 2, "category": "security", "difficulty": "medium", "explanation": "NEVER trust client data. Always validate on the server since clients can be exploited."},
    {"q": "What happens when you call :Destroy() on a player's character?", "options": ["Player is kicked", "Character respawns after delay", "Nothing happens", "Server crashes"], "correct": 1, "category": "scripting", "difficulty": "hard", "explanation": "Destroying a character triggers CharacterRemoving and the player respawns after RespawnTime."},
    {"q": "What is the purpose of CollectionService?", "options": ["Collect garbage", "Tag instances for batch operations", "Manage collections UI", "Handle microtransactions"], "correct": 1, "category": "services", "difficulty": "hard", "explanation": "CollectionService lets you tag instances and iterate over all instances with a given tag."},
    {"q": "What does workspace.StreamingEnabled control?", "options": ["Audio streaming", "Instance streaming/replication", "Video playback", "Data transfer speed"], "correct": 1, "category": "optimization", "difficulty": "hard", "explanation": "StreamingEnabled controls content streaming, only loading parts of the map near the player."},
    {"q": "What Roblox API yields (pauses) the current thread?", "options": ["game.Loaded", "task.spawn()", "workspace:Raycast()", "MarketplaceService:GetProductInfo()"], "correct": 3, "category": "services", "difficulty": "expert", "explanation": "GetProductInfo() is an async HTTP call that yields the thread until the response arrives."},
    {"q": "What is the difference between task.spawn() and coroutine.wrap()?", "options": ["No difference", "task.spawn runs on next frame, coroutine.wrap runs immediately", "task.spawn uses Roblox scheduler, coroutine.wrap uses Lua scheduler", "They are aliases"], "correct": 2, "category": "scripting", "difficulty": "expert", "explanation": "task.spawn uses Roblox's task scheduler with error handling; coroutine.wrap uses raw Lua coroutines."},
    {"q": "What property prevents a MeshPart from being modified by exploiters?", "options": ["Locked", "Archivable = false", "There is no such property", "SecurityLevel"], "correct": 2, "category": "security", "difficulty": "hard", "explanation": "There's no property that prevents client-side modification. Server validation is the only real protection."},
    {"q": "What does the '__mode' metamethod field control?", "options": ["Script execution mode", "Weak reference behavior", "Network replication", "Rendering priority"], "correct": 1, "category": "scripting", "difficulty": "expert", "explanation": "__mode = 'k', 'v', or 'kv' makes table keys/values weak references for garbage collection."},
    {"q": "How many DataStore budget units does SetAsync consume?", "options": ["1", "5", "6", "10"], "correct": 2, "category": "services", "difficulty": "expert", "explanation": "SetAsync costs 6 budget units (write request) in the DataStore budget system."},
    {"q": "What is the maximum Part size in studs (one axis)?", "options": ["512", "1024", "2048", "4096"], "correct": 2, "category": "studio", "difficulty": "hard", "explanation": "Individual parts can be up to 2048 studs in any single dimension."},
    {"q": "What does Terrain:WriteVoxels() do?", "options": ["Writes save data", "Edits terrain voxels in bulk", "Creates voxel models", "Generates terrain heightmap"], "correct": 1, "category": "studio", "difficulty": "expert", "explanation": "WriteVoxels() efficiently modifies terrain data in bulk using Region3 and material/occupancy arrays."},
    {"q": "What is the render step order: PreRender, PreAnimation, PreSimulation?", "options": ["PreRender → PreAnimation → PreSimulation", "PreAnimation → PreSimulation → PreRender", "PreSimulation → PreAnimation → PreRender", "PreAnimation → PreRender → PreSimulation"], "correct": 1, "category": "optimization", "difficulty": "expert", "explanation": "The order is PreAnimation → PreSimulation → PreRender in the Roblox task scheduler pipeline."},
    {"q": "What does HttpService:JSONEncode(math.huge) return?", "options": ["'Infinity'", "null", "Error is thrown", "'inf'"], "correct": 2, "category": "scripting", "difficulty": "expert", "explanation": "math.huge (infinity) is not valid JSON. JSONEncode throws an error for non-finite numbers."},
    {"q": "How many players can a single RemoteEvent:FireClient() target?", "options": ["All players", "1 specific player", "Up to 50", "Server only"], "correct": 1, "category": "security", "difficulty": "medium", "explanation": "FireClient(player, ...) targets exactly one specific player. Use FireAllClients() for all."},
    {"q": "What is the maximum string length DataStore can save per key?", "options": ["260,000 chars", "4,194,304 chars", "65,536 chars", "1,000,000 chars"], "correct": 1, "category": "services", "difficulty": "expert", "explanation": "DataStore values can be up to 4,194,304 characters (4MB) when serialized as JSON."},
    {"q": "What does Actor in Roblox enable?", "options": ["NPC AI system", "Parallel Luau execution", "Animation playback", "Voice chat"], "correct": 1, "category": "optimization", "difficulty": "hard", "explanation": "Actors enable Parallel Luau, allowing scripts to run on multiple threads for better performance."},
    {"q": "What is the frame budget (in ms) to maintain 60 FPS?", "options": ["33.33ms", "16.67ms", "8.33ms", "25ms"], "correct": 1, "category": "optimization", "difficulty": "hard", "explanation": "At 60 FPS, each frame has ~16.67ms (1000ms / 60 frames) of budget."},
]

# Tracking which questions each user has already seen
_user_question_history = {}  # user_id -> set of question hashes
_recent_ai_questions = []
_MAX_RECENT = 50

# Trivia cooldown tracking (wrong answer = 20 min cooldown)
_trivia_cooldowns = {}  # user_id -> timestamp when cooldown expires


def _question_hash(q: dict) -> str:
    """Create a hash for a question to track if user has seen it"""
    return str(hash(q.get("q", "")))


def _get_unseen_fallback(user_id: int, category: str = None, difficulty: str = None) -> dict:
    """Get a fallback question the user hasn't seen yet"""
    seen = _user_question_history.get(user_id, set())

    # Filter by category and difficulty if specified
    pool = FALLBACK_QUESTIONS.copy()
    if category and category != "random":
        filtered = [q for q in pool if q.get("category") == category]
        if filtered:
            pool = filtered
    if difficulty:
        filtered = [q for q in pool if q.get("difficulty") == difficulty]
        if filtered:
            pool = filtered

    # Find unseen questions
    unseen = [q for q in pool if _question_hash(q) not in seen]

    if unseen:
        question = random.choice(unseen).copy()
    else:
        # All seen — reset and pick random
        question = random.choice(pool).copy()

    # Mark as seen
    if user_id not in _user_question_history:
        _user_question_history[user_id] = set()
    _user_question_history[user_id].add(_question_hash(question))

    return question


def _check_all_fallbacks_seen(user_id: int) -> bool:
    """Check if user has seen all 40 fallback questions"""
    seen = _user_question_history.get(user_id, set())
    all_hashes = {_question_hash(q) for q in FALLBACK_QUESTIONS}
    return all_hashes.issubset(seen)


async def generate_ai_trivia(user_id: int, category: str = "random", difficulty: str = "medium", force_ai: bool = False) -> dict:
    """Generate a trivia question — uses fallbacks first, then AI when exhausted"""
    global _recent_ai_questions

    if category == "random":
        actual_category = random.choice([k for k in TRIVIA_CATEGORIES.keys() if k != "random"])
    else:
        actual_category = category

    cat_info = TRIVIA_CATEGORIES.get(actual_category, TRIVIA_CATEGORIES["general"])

    # Check if all fallback questions have been seen
    all_seen = _check_all_fallbacks_seen(user_id)

    if not all_seen and not force_ai:
        # Still have unseen fallback questions — use those
        question = _get_unseen_fallback(user_id, actual_category, difficulty)
        question["ai_generated"] = False

        # Count remaining
        seen = _user_question_history.get(user_id, set())
        all_hashes = {_question_hash(q) for q in FALLBACK_QUESTIONS}
        remaining = len(all_hashes - seen)
        question["remaining_fallbacks"] = remaining

        return question

    # All fallbacks exhausted OR force_ai — generate with AI
    # When generating AI questions, make them DEMON HARD
    demon_difficulty = difficulty
    if all_seen:
        demon_difficulty = "demon"

    recent_context = ""
    if _recent_ai_questions:
        recent_qs = [q.get("q", "") for q in _recent_ai_questions[-15:]]
        recent_context = f"\n\nDO NOT repeat these recent questions:\n" + "\n".join(f"- {q}" for q in recent_qs)

    # User's seen questions to avoid
    seen = _user_question_history.get(user_id, set())
    seen_fallback_qs = [q["q"] for q in FALLBACK_QUESTIONS if _question_hash(q) in seen]
    if seen_fallback_qs:
        recent_context += "\n\nUser has already answered these, make something COMPLETELY DIFFERENT:\n"
        recent_context += "\n".join(f"- {q}" for q in seen_fallback_qs[-10:])

    if demon_difficulty == "demon":
        difficulty_instruction = (
            "DIFFICULTY: 💀 DEMON — THIS IS THE HARDEST POSSIBLE DIFFICULTY.\n\n"
            "DEMON DIFFICULTY RULES:\n"
            "- Questions must be EXTREMELY obscure and specific\n"
            "- Test deep internal knowledge that only expert Roblox engineers would know\n"
            "- Include trick answers that LOOK correct but aren't\n"
            "- Ask about exact numbers, limits, internal behaviors, edge cases\n"
            "- Topics: internal scheduler timing, exact API limits, undocumented behaviors,\n"
            "  memory layout, replication internals, engine-specific quirks\n"
            "- Wrong answers should be VERY plausible — designed to fool even experienced devs\n"
            "- The question should make someone go 'wait, I've never thought about that'\n"
            "- Example topics:\n"
            "  * Exact throttle rates for specific API calls\n"
            "  * Order of internal engine events\n"
            "  * Memory consumption of specific instance types\n"
            "  * Undocumented behavior of deprecated functions\n"
            "  * Edge cases in physics simulation\n"
            "  * Exact limits (max instances, string lengths, etc.)\n"
            "  * Differences between similar-looking APIs\n"
            "  * Race conditions and timing issues\n"
            "  * Serialization quirks\n"
            "  * Behavior differences between client/server\n\n"
            "THIS SHOULD BE NEARLY IMPOSSIBLE. If you think it's too easy, make it harder.\n"
            "Wrong answer penalty: 20 MINUTE COOLDOWN. Make it worth that punishment.\n"
        )
    else:
        difficulty_guide = {
            "easy": "Basic concepts any beginner would know",
            "medium": "Intermediate knowledge, common patterns",
            "hard": "Advanced concepts, edge cases, best practices",
            "expert": "Deep internals, obscure features, optimization tricks",
        }
        difficulty_instruction = f"DIFFICULTY: {demon_difficulty.upper()} — {difficulty_guide.get(demon_difficulty, 'Advanced')}\n"

    prompt = (
        f"Generate a Roblox development trivia question.\n\n"
        f"CATEGORY: {cat_info['name']} — {cat_info['description']}\n"
        f"{difficulty_instruction}\n"
        f"Respond in EXACT JSON format (no markdown, raw JSON only):\n"
        f'{{"q": "question text", "options": ["correct answer", "wrong1", "wrong2", "wrong3"], '
        f'"correct": 0, "explanation": "brief explanation of the answer", '
        f'"category": "{actual_category}", "difficulty": "{demon_difficulty}", '
        f'"fun_fact": "optional interesting related fact"}}\n\n'
        f"RULES:\n"
        f"1. Question must be about {cat_info['name']}\n"
        f"2. Exactly 4 options\n"
        f"3. 'correct' is the INDEX (0-3) of the correct answer\n"
        f"4. RANDOMIZE where the correct answer appears (NOT always index 0)\n"
        f"5. Wrong answers should be VERY plausible — designed to trick people\n"
        f"6. Explanation should be educational and concise\n"
        f"7. Question should be specific and testable, not vague\n"
        f"8. ONLY output JSON, nothing else"
        f"{recent_context}"
    )

    try:
        result = await call_ai(prompt)

        if result.startswith("❌"):
            raise Exception("AI call failed")

        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            question = json.loads(cleaned[start:end])

            required = ["q", "options", "correct"]
            if not all(k in question for k in required):
                raise Exception("Missing required fields")

            if not isinstance(question["options"], list) or len(question["options"]) != 4:
                raise Exception("Need exactly 4 options")

            correct_idx = int(question["correct"])
            if correct_idx < 0 or correct_idx > 3:
                raise Exception("Invalid correct index")

            question.setdefault("explanation", "")
            question.setdefault("category", actual_category)
            question.setdefault("difficulty", demon_difficulty)
            question.setdefault("fun_fact", "")
            question["ai_generated"] = True
            question["remaining_fallbacks"] = 0

            _recent_ai_questions.append(question)
            if len(_recent_ai_questions) > _MAX_RECENT:
                _recent_ai_questions.pop(0)

            # Track for this user
            if user_id not in _user_question_history:
                _user_question_history[user_id] = set()
            _user_question_history[user_id].add(_question_hash(question))

            return question

        raise Exception("Could not parse JSON")

    except Exception as e:
        print(f"[AI Trivia] Generation failed: {e}, using fallback")
        question = _get_unseen_fallback(user_id, actual_category, difficulty)
        question["ai_generated"] = False
        return question


async def generate_ai_duel_question(difficulty: str = "medium") -> dict:
    """Generate a duel question using AI"""
    question = await generate_ai_trivia(0, category="random", difficulty=difficulty, force_ai=True)
    return question


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


# ==================== DUEL VIEW ====================
class DuelAcceptView(discord.ui.View):
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
                label=option[:80],
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
        super().__init__(timeout=86400)
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
        await UserProfile.add_credits(interaction.user.id, self.reward)

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
        if not self.claimed_by:
            await UserProfile.add_credits(self.creator_id, self.reward)


# ==================== TRIVIA VIEWS ====================

class TriviaCategoryView(discord.ui.View):
    def __init__(self, user_id: int, difficulty: str = "medium"):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.difficulty = difficulty
        self.selected_category = None

        categories = list(TRIVIA_CATEGORIES.items())
        for i, (key, info) in enumerate(categories):
            row = i // 5
            style = discord.ButtonStyle.primary if key == "random" else discord.ButtonStyle.secondary
            btn = discord.ui.Button(
                label=info["name"][:20],
                emoji=info["emoji"],
                style=style,
                custom_id=f"cat_{key}_{random.randint(1000, 9999)}",
                row=row
            )
            btn.callback = self._make_callback(key)
            self.add_item(btn)

    def _make_callback(self, category_key):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not your trivia!", ephemeral=True)
                return
            self.selected_category = category_key
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()
        return callback


class TriviaAnswerView(discord.ui.View):
    def __init__(self, question: dict, user_id: int, difficulty: str):
        timeout = 30 if difficulty == "demon" else 20
        super().__init__(timeout=timeout)
        self.question = question
        self.user_id = user_id
        self.difficulty = difficulty
        self.user_answer = None
        self.answered = False

        labels = ["A", "B", "C", "D"]

        for i, option in enumerate(question["options"][:4]):
            btn = discord.ui.Button(
                label=f"{labels[i]}. {option[:70]}",
                style=discord.ButtonStyle.primary,
                custom_id=f"trivia_ans_{i}_{random.randint(1000, 9999)}",
                row=i // 2
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not your trivia!", ephemeral=True)
                return
            if self.answered:
                await interaction.response.send_message("❌ Already answered!", ephemeral=True)
                return

            self.answered = True
            self.user_answer = index

            correct_idx = self.question["correct"]
            labels = ["A", "B", "C", "D"]

            for j, child in enumerate(self.children):
                child.disabled = True
                if j == correct_idx:
                    child.style = discord.ButtonStyle.success
                    child.label = f"✅ {labels[j]}. {self.question['options'][j][:55]}"
                elif j == index and j != correct_idx:
                    child.style = discord.ButtonStyle.danger
                    child.label = f"❌ {labels[j]}. {self.question['options'][j][:55]}"
                else:
                    child.style = discord.ButtonStyle.secondary

            await interaction.response.edit_message(view=self)
            self.stop()
        return callback


class TriviaStreakView(discord.ui.View):
    def __init__(self, user_id: int, streak: int, category: str, difficulty: str):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.streak = streak
        self.category = category
        self.difficulty = difficulty
        self.continue_playing = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your trivia!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Next Question!", emoji="▶️", style=discord.ButtonStyle.success)
    async def next_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.continue_playing = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cash Out", emoji="💰", style=discord.ButtonStyle.secondary)
    async def cash_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.continue_playing = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Harder!", emoji="🔥", style=discord.ButtonStyle.danger)
    async def go_harder(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.continue_playing = True
        diff_order = ["easy", "medium", "hard", "expert", "demon"]
        current_idx = diff_order.index(self.difficulty) if self.difficulty in diff_order else 1
        if current_idx < len(diff_order) - 1:
            self.difficulty = diff_order[current_idx + 1]
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


# ==================== UNBOX ANIMATION ====================
UNBOX_FRAMES = [
    "📦 Opening Code Box... 🎰",
    "📦 Opening Code Box... 🎰 ✨",
    "📦 Opening Code Box... 🎰 ✨✨",
    "📦 Opening Code Box... 🎰 ✨✨✨",
    "💥 **REVEALED!** 💥",
]


# ==================== HELPERS ====================
def is_user_admin(interaction: discord.Interaction) -> bool:
    try:
        if interaction.guild and hasattr(interaction.user, 'guild_permissions'):
            return interaction.user.guild_permissions.administrator
    except Exception:
        pass
    return False


async def check_ai_credits(interaction: discord.Interaction, cost: int = 1) -> bool:
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
    user = await UserProfile.get_user(user_id)
    if user:
        current = user.get("ai_credits", 0)
        await UserProfile.update_user(user_id, {"ai_credits": current + cost})


def format_cooldown_remaining(user_id: int) -> str:
    """Get formatted remaining cooldown time"""
    if user_id not in _trivia_cooldowns:
        return ""
    remaining = _trivia_cooldowns[user_id] - time.time()
    if remaining <= 0:
        del _trivia_cooldowns[user_id]
        return ""
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    return f"{minutes}m {seconds}s"


# ==================== FUN COG ====================
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._trivia_locks = set()

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
                f"❌ {user.display_name} doesn't have a profile yet! Tell them to use `/start`."
            )
            return

        if not await check_ai_credits(interaction, 1):
            return

        roles = profile.get("roles", profile.get("role", "None"))
        if isinstance(roles, list):
            roles = ", ".join(roles) if roles else "None"

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Write a devastating but FUNNY roast about this Roblox developer. "
            f"Be savage but playful and game-dev themed. Use their stats against them. "
            f"3-4 sentences max. Be creative and specific to their stats.\n\n"
            f"TARGET: {user.display_name}\n"
            f"Roles: {roles}\n"
            f"Rank: {profile.get('rank', 'Beginner')} | Level: {profile.get('level', 1)} | XP: {profile.get('xp', 0)}\n"
            f"Credits: {profile.get('studio_credits', 0)} | Messages: {profile.get('message_count', 0)} | Rep: {profile.get('reputation', 0)}\n"
            f"Voice Minutes: {profile.get('voice_minutes', 0)}"
        )

        try:
            roast = await call_ai(prompt)
            if roast.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(roast)
                return

            embed = discord.Embed(title=f"💀 AI ROAST — {user.display_name}", description=roast[:2000], color=0xE74C3C)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(
                name="Victim's Stats",
                value=f"Level {profile.get('level', 1)} | {profile.get('rank', 'Beginner')} | 💰 {profile.get('studio_credits', 0)} Credits",
                inline=False
            )
            embed.set_footer(text=f"Roasted by {AI_NAME} • Requested by {interaction.user.display_name} • 1 AI Credit")
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
        if len(task) < 10 or len(task) > 500:
            await interaction.followup.send("❌ Task must be 10-500 characters!")
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if current_credits < reward:
            await interaction.followup.send(f"❌ Not enough credits! You have **{current_credits}**.")
            return

        await UserProfile.update_user(interaction.user.id, {"studio_credits": current_credits - reward})

        bounty_id = f"bounty_{interaction.user.id}_{random.randint(10000, 99999)}"

        embed = discord.Embed(
            title="💰 Dev Bounty Posted!",
            description=f"**Task:** {task}\n\n**Reward:** 💰 {reward} Credits\n**Posted by:** {interaction.user.mention}\n**Expires:** 24 hours",
            color=0xF1C40F
        )
        embed.add_field(name="How to claim", value="Click 🎯 **Claim Bounty** below!", inline=False)
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
            await interaction.followup.send(f"❌ You need **500 Credits**! You have **{current_credits}**.")
            return

        await UserProfile.update_user(interaction.user.id, {"studio_credits": current_credits - 500})

        msg = await interaction.followup.send(UNBOX_FRAMES[0], wait=True)
        for frame in UNBOX_FRAMES[1:]:
            await asyncio.sleep(0.8)
            try:
                await msg.edit(content=frame)
            except Exception:
                pass

        rarity, rarity_data, snippet = roll_snippet()
        xp_bonus = {"common": 5, "uncommon": 10, "rare": 25, "epic": 50, "legendary": 100}
        bonus = xp_bonus.get(rarity, 5)
        await UserProfile.add_xp(interaction.user.id, bonus)

        code_text = snippet['code'][:900]
        if len(snippet['code']) > 900:
            code_text += "\n-- ... (truncated)"

        embed = discord.Embed(
            title=f"{rarity_data['emoji']} {rarity.upper()} — {snippet['name']}!",
            description=f"**{snippet['desc']}**",
            color=rarity_data["color"]
        )
        embed.add_field(name="📝 Code", value=f"```lua\n{code_text}\n```", inline=False)
        embed.add_field(name="Rarity", value=f"{rarity_data['emoji']} {rarity.upper()} ({rarity_data['chance']}%)", inline=True)
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

        users = sorted(
            _memory_users.values(),
            key=lambda x: (x.get("pcredits", 0) * 1000) + x.get("studio_credits", 0),
            reverse=True
        )[:10]

        if not users:
            await interaction.followup.send("❌ No users found!")
            return

        embed = discord.Embed(title="💎💰 WEALTH LEADERBOARD 💰💎", description="*The richest devs in the studio*\n", color=0xF1C40F)

        medals = ["👑", "💎", "🥇", "🥈", "🥉", "💰", "💰", "💰", "💰", "💰"]
        for i, u in enumerate(users):
            total = (u.get('pcredits', 0) * 1000) + u.get('studio_credits', 0)
            embed.add_field(
                name=f"{medals[i]} #{i + 1} — {u.get('username', 'Unknown')}",
                value=f"💎 {u.get('pcredits', 0)} pCredits | 💰 {u.get('studio_credits', 0)} Credits | 🤖 {u.get('ai_credits', 0)} AI\n📊 Total: **{total:,}**",
                inline=False
            )

        embed.set_footer(text="Total = (pCredits × 1000) + Credits")
        await interaction.followup.send(embed=embed)

    # ========== 5. CODE DUEL (AI QUESTIONS) ==========
    @app_commands.command(name="code-duel", description="⚔️ Challenge someone to a Luau knowledge duel")
    @app_commands.describe(opponent="Who to challenge", bet="Credits to bet (50-10000)")
    async def code_duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int = 100):
        await interaction.response.defer()

        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.followup.send("❌ Invalid opponent!")
            return
        if bet < 50 or bet > 10000:
            await interaction.followup.send("❌ Bet must be **50-10,000** Credits!")
            return

        challenger = await UserProfile.get_user(interaction.user.id)
        if not challenger:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            challenger = await UserProfile.get_user(interaction.user.id)

        opp_profile = await UserProfile.get_user(opponent.id)
        if not opp_profile:
            await UserProfile.create_user(opponent.id, opponent.name)
            opp_profile = await UserProfile.get_user(opponent.id)

        if challenger.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ You don't have **{bet}** Credits!")
            return
        if opp_profile.get("studio_credits", 0) < bet:
            await interaction.followup.send(f"❌ {opponent.display_name} doesn't have **{bet}** Credits!")
            return

        accept_embed = discord.Embed(
            title="⚔️ Duel Challenge!",
            description=f"**{interaction.user.display_name}** vs **{opponent.display_name}**\n💰 **Bet:** {bet} Credits | 🤖 AI Question\n\n{opponent.mention}, accept?",
            color=0xE74C3C
        )
        accept_view = DuelAcceptView(interaction.user.id, opponent.id, bet)
        await interaction.followup.send(embed=accept_embed, view=accept_view)
        await accept_view.wait()

        if not accept_view.accepted:
            if accept_view.accepted is None:
                try:
                    await interaction.edit_original_response(
                        embed=discord.Embed(title="⚔️ Duel Expired", description=f"{opponent.display_name} didn't respond.", color=0x95A5A6),
                        view=None
                    )
                except Exception:
                    pass
            return

        # Re-verify
        challenger = await UserProfile.get_user(interaction.user.id)
        opp_profile = await UserProfile.get_user(opponent.id)
        if challenger.get("studio_credits", 0) < bet or opp_profile.get("studio_credits", 0) < bet:
            await interaction.channel.send("❌ Someone doesn't have enough credits! Cancelled.")
            return

        duel_diff = "expert" if bet >= 5000 else "hard" if bet >= 2000 else "medium" if bet >= 500 else "easy"

        loading_msg = await interaction.channel.send(
            embed=discord.Embed(title="⚔️ Generating...", description="🤖 AI is crafting a question...", color=0xE74C3C)
        )

        question = await generate_ai_duel_question(duel_diff)
        diff_info = TRIVIA_DIFFICULTIES.get(duel_diff, TRIVIA_DIFFICULTIES["medium"])
        cat_info = TRIVIA_CATEGORIES.get(question.get("category", "general"), TRIVIA_CATEGORIES["general"])
        ai_badge = "🤖 AI" if question.get("ai_generated") else "📚 Classic"

        duel_embed = discord.Embed(
            title="⚔️ CODE DUEL — FIGHT!",
            description=(
                f"**{interaction.user.display_name}** vs **{opponent.display_name}**\n"
                f"💰 {bet} | {diff_info['emoji']} {duel_diff.title()} | {cat_info['emoji']} {cat_info['name']} | {ai_badge}\n\n"
                f"**{question['q']}**\n\n⏱️ 15 seconds!"
            ),
            color=0xE74C3C
        )

        answer_view = DuelAnswerView(question, interaction.user.id, opponent.id, bet)
        await loading_msg.edit(embed=duel_embed, view=answer_view)
        await answer_view.wait()

        ca = answer_view.answers.get(interaction.user.id)
        oa = answer_view.answers.get(opponent.id)
        correct_text = question["options"][question["correct"]]

        winner_id, loser_id, result_title, result_desc = None, None, "", ""

        if not ca and not oa:
            result_title, result_desc = "⚔️ Draw!", "Neither answered!"
        elif not ca:
            winner_id, loser_id = opponent.id, interaction.user.id
            result_title = f"⚔️ {opponent.display_name} WINS!"
            result_desc = f"{interaction.user.display_name} didn't answer! 💰 **{bet}** Credits won!"
        elif not oa:
            winner_id, loser_id = interaction.user.id, opponent.id
            result_title = f"⚔️ {interaction.user.display_name} WINS!"
            result_desc = f"{opponent.display_name} didn't answer! 💰 **{bet}** Credits won!"
        elif ca["correct"] and not oa["correct"]:
            winner_id, loser_id = interaction.user.id, opponent.id
            result_title = f"⚔️ {interaction.user.display_name} WINS!"
            result_desc = f"💰 **{bet}** Credits won!"
        elif not ca["correct"] and oa["correct"]:
            winner_id, loser_id = opponent.id, interaction.user.id
            result_title = f"⚔️ {opponent.display_name} WINS!"
            result_desc = f"💰 **{bet}** Credits won!"
        elif ca["correct"] and oa["correct"]:
            if ca["time"] < oa["time"]:
                winner_id, loser_id = interaction.user.id, opponent.id
                result_title = f"⚔️ {interaction.user.display_name} WINS!"
                result_desc = "Both correct — **faster**! ⚡"
            elif oa["time"] < ca["time"]:
                winner_id, loser_id = opponent.id, interaction.user.id
                result_title = f"⚔️ {opponent.display_name} WINS!"
                result_desc = "Both correct — **faster**! ⚡"
            else:
                result_title, result_desc = "⚔️ Perfect Draw!", "Same time!"
        else:
            result_title, result_desc = "⚔️ Draw!", "Both wrong!"

        if winner_id and loser_id:
            w = await UserProfile.get_user(winner_id)
            l = await UserProfile.get_user(loser_id)
            if w and l:
                actual = min(bet, l.get("studio_credits", 0))
                if actual > 0:
                    await UserProfile.update_user(loser_id, {"studio_credits": l.get("studio_credits", 0) - actual})
                    await UserProfile.update_user(winner_id, {"studio_credits": w.get("studio_credits", 0) + actual})

        result_embed = discord.Embed(title=result_title, description=result_desc, color=0x2ECC71 if winner_id else 0x95A5A6)
        result_embed.add_field(name="✅ Answer", value=f"**{correct_text}**", inline=False)
        if question.get("explanation"):
            result_embed.add_field(name="📖 Explanation", value=question["explanation"][:500], inline=False)
        if question.get("fun_fact"):
            result_embed.add_field(name="💡 Fun Fact", value=question["fun_fact"][:300], inline=False)
        await interaction.channel.send(embed=result_embed)

    # ========== 6. AI FIX ==========
    @app_commands.command(name="ai-fix", description="🔧 AI rewrites your code optimized (1 AI Credit)")
    @app_commands.describe(code="Paste your code here")
    async def ai_fix(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer()

        if len(code.strip()) < 5:
            await interaction.followup.send("❌ Code is too short!")
            return
        if not await check_ai_credits(interaction, 1):
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\n"
            f"TASK: Rewrite this Roblox Lua/Luau code optimized, clean, bug-free.\n\n"
            f"ORIGINAL:\n```lua\n{code[:3000]}\n```\n\n"
            f"Provide:\n1. Fixes (2-4 bullets)\n2. Complete code\n3. Performance note"
        )

        try:
            result = await call_ai(prompt)
            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(title="🔧 Code Optimized!", description=f"By {AI_NAME} • 1 AI Credit", color=0x3498DB)
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 7. DEV CONFESSION ==========
    @app_commands.command(name="dev-confession", description="🤫 Submit an anonymous dev confession")
    @app_commands.describe(confession="Your anonymous confession")
    async def dev_confession(self, interaction: discord.Interaction, confession: str):
        await interaction.response.defer(ephemeral=True)

        if len(confession.strip()) < 10 or len(confession) > 500:
            await interaction.followup.send("❌ Must be 10-500 characters!", ephemeral=True)
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\nA dev confessed: \"{confession}\"\n\n"
            f"Write a SHORT funny reaction (1-2 sentences). Be witty and game-dev themed."
        )

        try:
            ai_comment = await call_ai(prompt)
            embed = discord.Embed(title="🤫 Anonymous Dev Confession", description=f"*\"{confession}\"*", color=0x9B59B6)
            embed.add_field(
                name=f"💬 {AI_NAME}'s Take",
                value=ai_comment[:1024] if not ai_comment.startswith("❌") else "No comment. 😶",
                inline=False
            )
            embed.set_footer(text="Someone in this server wrote this... 👀")
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ Posted anonymously!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {str(e)[:200]}", ephemeral=True)

    # ========== 8. AI PREDICT GAME ==========
    @app_commands.command(name="ai-predict-game", description="🔮 AI predicts game success (1 AI Credit)")
    @app_commands.describe(idea="Describe your game idea")
    async def ai_predict_game(self, interaction: discord.Interaction, idea: str):
        await interaction.response.defer()

        if len(idea.strip()) < 10:
            await interaction.followup.send("❌ Need at least 10 characters!")
            return
        if not await check_ai_credits(interaction, 1):
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\nTASK: Analyze this Roblox game idea.\n\nIDEA: {idea[:1000]}\n\n"
            f"Provide:\n1. SUCCESS CHANCE %\n2. VERDICT: 🟢/🟡/🔴\n3. STRENGTHS\n4. WEAKNESSES\n"
            f"5. COMPETITION\n6. MONETIZATION\n7. DEV TIME\n8. KILLER TIP"
        )

        try:
            result = await call_ai(prompt)
            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(title="🔮 Game Prediction", description=f"**Idea:** {idea[:200]}", color=0x9B59B6)
            embed.set_footer(text=f"By {AI_NAME} • {interaction.user.display_name} • 1 AI Credit")
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 9. IDEAS ==========
    @app_commands.command(name="ideas", description="💡 AI generates game ideas (1 AI Credit)")
    @app_commands.describe(keyword="Theme (optional)")
    async def ideas(self, interaction: discord.Interaction, keyword: str = None):
        await interaction.response.defer()

        if not await check_ai_credits(interaction, 1):
            return

        kw = f"based on '{keyword}'" if keyword else "based on 2024-2025 Roblox trends"
        prompt = (
            f"System: {AI_PERSONALITY}\n\nTASK: Generate 3 Roblox game ideas {kw}.\n\n"
            f"For each: 🎮 NAME, 📝 DESCRIPTION, 🎯 GENRE, 📊 PREDICTED PLAYS, ⏱️ DEV TIME, 💰 MONETIZATION, 🔥 WHY IT WORKS"
        )

        try:
            result = await call_ai(prompt)
            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(title="💡 Game Ideas", description=f"**Theme:** {keyword or 'Trending'}", color=0xF1C40F)
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(message=msg, ai_text=result, user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 10. COIN FLIP ==========
    @app_commands.command(name="coinflip", description="🪙 Flip a coin and bet credits!")
    @app_commands.describe(choice="Heads or Tails", bet="Credits to bet (0 for free)")
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
        if bet < 0 or bet > 5000:
            await interaction.followup.send("❌ Bet must be 0-5,000!")
            return
        if bet > 0 and current_credits < bet:
            await interaction.followup.send(f"❌ Not enough! You have **{current_credits}**.")
            return

        result = random.choice(["heads", "tails"])
        won = result == choice

        msg = await interaction.followup.send("🪙 Flipping...", wait=True)
        await asyncio.sleep(1)
        await msg.edit(content="🪙 Flipping... 🌀")
        await asyncio.sleep(0.8)

        result_emoji = "👑" if result == "heads" else "🔮"

        if bet > 0:
            if won:
                await UserProfile.update_user(interaction.user.id, {"studio_credits": current_credits + bet})
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU WIN!",
                    description=f"💰 Won **{bet}** Credits! Balance: **{current_credits + bet}**",
                    color=0x2ECC71
                )
            else:
                await UserProfile.update_user(interaction.user.id, {"studio_credits": current_credits - bet})
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU LOSE!",
                    description=f"💸 Lost **{bet}** Credits! Balance: **{current_credits - bet}**",
                    color=0xE74C3C
                )
        else:
            embed = discord.Embed(
                title=f"{result_emoji} {result.upper()}!",
                description=f"{'✅ Correct!' if won else '❌ Wrong!'}",
                color=0x2ECC71 if won else 0xE74C3C
            )

        embed.add_field(name="Pick", value=choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        await msg.edit(content=None, embed=embed)

    # ========== 11. AI TRIVIA (FULLY UPGRADED) ==========
    @app_commands.command(name="trivia", description="🧠 AI trivia with categories, streaks, and 💀 DEMON mode!")
    @app_commands.describe(difficulty="Question difficulty", category="Question category")
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="🟢 Easy", value="easy"),
            app_commands.Choice(name="🟡 Medium", value="medium"),
            app_commands.Choice(name="🟠 Hard", value="hard"),
            app_commands.Choice(name="🔴 Expert", value="expert"),
            app_commands.Choice(name="💀 Demon", value="demon"),
        ]
    )
    async def trivia(self, interaction: discord.Interaction, difficulty: str = "medium", category: str = None):
        await interaction.response.defer()

        user_id = interaction.user.id

        # Check cooldown
        cooldown_remaining = format_cooldown_remaining(user_id)
        if cooldown_remaining:
            embed = discord.Embed(
                title="💀 DEMON COOLDOWN ACTIVE",
                description=(
                    f"You got a question wrong! You must wait before trying again.\n\n"
                    f"⏰ **Time remaining:** {cooldown_remaining}\n\n"
                    f"*The demons don't forgive easily...*"
                ),
                color=0x8B0000
            )
            embed.set_footer(text="Wrong answers on demon/AI questions = 20 minute cooldown")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if user_id in self._trivia_locks:
            await interaction.followup.send("❌ You already have a trivia in progress!", ephemeral=True)
            return

        self._trivia_locks.add(user_id)
        try:
            await self._run_trivia_session(interaction, difficulty, category)
        finally:
            self._trivia_locks.discard(user_id)

    async def _run_trivia_session(self, interaction: discord.Interaction, difficulty: str, category: str = None):
        user_id = interaction.user.id
        streak = 0
        total_xp = 0
        total_credits = 0
        current_difficulty = difficulty

        # Category picker if none specified
        if not category:
            # Show question pool status
            all_seen = _check_all_fallbacks_seen(user_id)
            seen_count = len(_user_question_history.get(user_id, set()))
            total_fallbacks = len(FALLBACK_QUESTIONS)

            pool_status = ""
            if all_seen:
                pool_status = (
                    f"\n\n💀 **ALL {total_fallbacks} QUESTIONS COMPLETED!**\n"
                    f"AI will now generate 💀 **DEMON-HARD** questions!\n"
                    f"⚠️ Wrong answer = **20 MINUTE COOLDOWN**"
                )
            else:
                pool_status = f"\n\n📊 Progress: **{seen_count}/{total_fallbacks}** questions answered"

            picker_embed = discord.Embed(
                title="🧠 AI Trivia — Pick a Category!",
                description=(
                    f"**Difficulty:** {TRIVIA_DIFFICULTIES.get(current_difficulty, TRIVIA_DIFFICULTIES['medium'])['emoji']} "
                    f"{current_difficulty.title()}"
                    f"{pool_status}"
                ),
                color=0x5865F2
            )

            for key, info in TRIVIA_CATEGORIES.items():
                picker_embed.add_field(name=f"{info['emoji']} {info['name']}", value=info['description'], inline=True)

            picker_view = TriviaCategoryView(user_id, current_difficulty)
            await interaction.followup.send(embed=picker_embed, view=picker_view)
            await picker_view.wait()

            if picker_view.selected_category is None:
                await interaction.channel.send(f"⏱️ {interaction.user.mention} Trivia timed out!")
                return
            category = picker_view.selected_category

        # Main trivia loop
        while True:
            # Check cooldown each round
            cooldown_remaining = format_cooldown_remaining(user_id)
            if cooldown_remaining:
                cooldown_embed = discord.Embed(
                    title="💀 COOLDOWN ACTIVATED",
                    description=(
                        f"You got a demon question wrong!\n\n"
                        f"⏰ **Wait:** {cooldown_remaining}\n\n"
                        f"**Session Stats:**\n"
                        f"🔥 Streak: {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits"
                    ),
                    color=0x8B0000
                )
                await interaction.channel.send(embed=cooldown_embed)
                break

            diff_info = TRIVIA_DIFFICULTIES.get(current_difficulty, TRIVIA_DIFFICULTIES["medium"])
            cat_info = TRIVIA_CATEGORIES.get(category if category != "random" else "general", TRIVIA_CATEGORIES["general"])

            # Check if all fallbacks are seen
            all_seen = _check_all_fallbacks_seen(user_id)
            is_demon_mode = all_seen or current_difficulty == "demon"

            # Loading
            streak_text = f" | 🔥 Streak: {streak}" if streak > 0 else ""
            demon_warning = "\n💀 **DEMON MODE** — Wrong = 20 min cooldown!" if is_demon_mode else ""

            loading_embed = discord.Embed(
                title="🧠 Generating Question...",
                description=(
                    f"{'💀' if is_demon_mode else '🤖'} "
                    f"{'Summoning a DEMON question...' if is_demon_mode else 'Preparing question...'}"
                    f"{streak_text}{demon_warning}"
                ),
                color=0x8B0000 if is_demon_mode else diff_info["color"]
            )
            loading_msg = await interaction.channel.send(embed=loading_embed)

            # Generate question
            if is_demon_mode:
                question = await generate_ai_trivia(user_id, category, "demon", force_ai=True)
            else:
                question = await generate_ai_trivia(user_id, category, current_difficulty)

            ai_generated = question.get("ai_generated", False)
            remaining = question.get("remaining_fallbacks", 0)
            q_difficulty = question.get("difficulty", current_difficulty)
            is_demon_q = q_difficulty == "demon" or is_demon_mode

            actual_diff_info = TRIVIA_DIFFICULTIES.get(q_difficulty, diff_info)
            actual_cat = TRIVIA_CATEGORIES.get(question.get("category", "general"), TRIVIA_CATEGORIES["general"])

            # Badge
            if is_demon_q:
                badge = "💀 DEMON"
            elif ai_generated:
                badge = "🤖 AI-Generated"
            else:
                badge = f"📚 Classic ({remaining} left)"

            # Streak bonus text
            streak_bonus = ""
            if streak > 0:
                multiplier = 1 + (streak * 0.25)
                streak_bonus = f"\n🔥 **Streak: {streak}** — x{multiplier:.2f} rewards!"

            # Demon warning
            penalty_warning = ""
            if is_demon_q:
                penalty_warning = "\n\n⚠️ **WRONG ANSWER = 20 MINUTE COOLDOWN**"

            # Timer
            timer = 30 if is_demon_q else 20

            question_embed = discord.Embed(
                title=f"{'💀' if is_demon_q else '🧠'} {'DEMON TRIVIA' if is_demon_q else 'Dev Trivia'} — {actual_cat['emoji']} {actual_cat['name']}",
                description=(
                    f"{actual_diff_info['emoji']} **{q_difficulty.title()}** | {badge}\n\n"
                    f"**{question['q']}**"
                    f"{streak_bonus}"
                    f"{penalty_warning}\n\n"
                    f"⏱️ {timer} seconds!"
                ),
                color=actual_diff_info["color"]
            )

            if streak > 0:
                question_embed.set_footer(text=f"🔥 Streak: {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits")

            answer_view = TriviaAnswerView(question, user_id, q_difficulty)
            await loading_msg.edit(embed=question_embed, view=answer_view)
            await answer_view.wait()

            answer = answer_view.user_answer
            correct_idx = question["correct"]
            correct_text = question["options"][correct_idx]
            explanation = question.get("explanation", "")
            fun_fact = question.get("fun_fact", "")

            if answer is None:
                # Timeout
                result = discord.Embed(
                    title="⏱️ Time's Up!",
                    description=f"✅ Answer: **{correct_text}**",
                    color=0x95A5A6
                )
                if explanation:
                    result.add_field(name="📖 Explanation", value=explanation[:500], inline=False)
                if streak > 0:
                    result.add_field(
                        name="🔥 Streak Ended!",
                        value=f"Final: **{streak}** | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                        inline=False
                    )

                # Apply cooldown if demon
                if is_demon_q:
                    _trivia_cooldowns[user_id] = time.time() + (20 * 60)
                    result.add_field(
                        name="💀 DEMON PUNISHMENT",
                        value="⏰ **20 minute cooldown** applied for not answering!",
                        inline=False
                    )
                    result.color = 0x8B0000

                await interaction.channel.send(embed=result)
                break

            elif answer == correct_idx:
                # CORRECT
                streak += 1
                multiplier = 1 + ((streak - 1) * 0.25)
                base_xp = actual_diff_info["xp"]
                base_credits = actual_diff_info["credits"]
                earned_xp = int(base_xp * multiplier)
                earned_credits = int(base_credits * multiplier)

                total_xp += earned_xp
                total_credits += earned_credits

                await UserProfile.add_xp(user_id, earned_xp)
                await UserProfile.add_credits(user_id, earned_credits)

                title_prefix = "💀 DEMON SLAYED!" if is_demon_q else "✅ Correct!"

                result = discord.Embed(
                    title=f"{title_prefix} 🔥 Streak: {streak}",
                    description=(
                        f"**{correct_text}**\n\n"
                        f"✨ +{earned_xp} XP | 💰 +{earned_credits} Credits"
                        f"{f' (x{multiplier:.2f} bonus!)' if multiplier > 1 else ''}"
                    ),
                    color=0x57F287 if is_demon_q else 0x2ECC71
                )
                if explanation:
                    result.add_field(name="📖 Explanation", value=explanation[:500], inline=False)
                if fun_fact:
                    result.add_field(name="💡 Fun Fact", value=fun_fact[:300], inline=False)
                result.add_field(
                    name="📊 Session",
                    value=f"🔥 {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                    inline=False
                )

                if is_demon_q:
                    result.set_footer(text="You survived the demon... for now. 💀")
                await interaction.channel.send(embed=result)

                # Continue?
                continue_view = TriviaStreakView(user_id, streak, category, current_difficulty)
                continue_msg = await interaction.channel.send(f"🔥 **{streak} streak!** Keep going?", view=continue_view)
                await continue_view.wait()

                if continue_view.continue_playing is None or continue_view.continue_playing is False:
                    cashout_embed = discord.Embed(
                        title=f"💰 Session Complete!",
                        description=(
                            f"**Final Streak:** 🔥 {streak}\n"
                            f"**Total XP:** ✨ {total_xp}\n"
                            f"**Total Credits:** 💰 {total_credits}\n"
                            f"**Difficulty:** {actual_diff_info['emoji']} {current_difficulty.title()}"
                        ),
                        color=0xF1C40F
                    )
                    await interaction.channel.send(embed=cashout_embed)
                    break
                else:
                    current_difficulty = continue_view.difficulty
                    continue

            else:
                # WRONG
                wrong_text = question["options"][answer]

                result = discord.Embed(
                    title=f"{'💀 DEMON WINS!' if is_demon_q else '❌ Wrong!'}",
                    description=(
                        f"You picked: **{wrong_text}**\n"
                        f"✅ Correct: **{correct_text}**"
                    ),
                    color=0x8B0000 if is_demon_q else 0xE74C3C
                )
                if explanation:
                    result.add_field(name="📖 Explanation", value=explanation[:500], inline=False)
                if fun_fact:
                    result.add_field(name="💡 Fun Fact", value=fun_fact[:300], inline=False)

                if streak > 0:
                    result.add_field(
                        name="🔥 Streak Ended!",
                        value=f"Final: **{streak}** | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                        inline=False
                    )

                # Apply cooldown if demon/AI question
                if is_demon_q:
                    _trivia_cooldowns[user_id] = time.time() + (20 * 60)  # 20 minutes
                    result.add_field(
                        name="💀 DEMON PUNISHMENT",
                        value=(
                            "⏰ **20 MINUTE COOLDOWN** applied!\n"
                            "You cannot play trivia for 20 minutes.\n\n"
                            "*The demons feast on your failure...*"
                        ),
                        inline=False
                    )

                await interaction.channel.send(embed=result)
                break

    @trivia.autocomplete("category")
    async def trivia_category_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = []
        for key, info in TRIVIA_CATEGORIES.items():
            name = f"{info['emoji']} {info['name']}"
            if current.lower() in name.lower() or current.lower() in key.lower() or not current:
                choices.append(app_commands.Choice(name=name, value=key))
        return choices[:25]


async def setup(bot):
    await bot.add_cog(FunCog(bot))