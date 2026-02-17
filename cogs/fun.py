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
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get(
    "AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get(
    "AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

anthropic_client = Anthropic(api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                             base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL)


async def call_ai(prompt):
    try:
        response = await asyncio.to_thread(anthropic_client.messages.create,
                                           model=AI_MODEL,
                                           max_tokens=8192,
                                           messages=[{
                                               "role": "user",
                                               "content": prompt
                                           }])
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
    "easy": {
        "emoji": "🟢",
        "xp": 10,
        "credits": 5,
        "color": 0x2ECC71
    },
    "medium": {
        "emoji": "🟡",
        "xp": 20,
        "credits": 10,
        "color": 0xF1C40F
    },
    "hard": {
        "emoji": "🟠",
        "xp": 35,
        "credits": 20,
        "color": 0xE67E22
    },
    "expert": {
        "emoji": "🔴",
        "xp": 50,
        "credits": 35,
        "color": 0xE74C3C
    },
    "demon": {
        "emoji": "💀",
        "xp": 100,
        "credits": 75,
        "color": 0x8B0000
    },
}

# 40 fallback questions (20 original + 20 new)
FALLBACK_QUESTIONS = [
    # ===== ORIGINAL 20 =====
    {
        "q":
        "What function creates a new Instance in Roblox?",
        "options": ["Instance.new()", "Create()", "Spawn()", "Make()"],
        "correct":
        0,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "Instance.new() is the standard way to create new objects in Roblox."
    },
    {
        "q":
        "What service handles player data saving?",
        "options":
        ["DataStoreService", "SaveService", "PlayerData", "StorageService"],
        "correct":
        0,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "DataStoreService provides access to persistent data storage."
    },
    {
        "q":
        "What property controls how fast a Humanoid walks?",
        "options": ["Speed", "WalkSpeed", "MoveSpeed", "RunSpeed"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "WalkSpeed is the property that controls movement speed, default is 16."
    },
    {
        "q":
        "What event fires when a player joins the game?",
        "options": ["PlayerJoined", "PlayerAdded", "OnJoin", "NewPlayer"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "Players.PlayerAdded fires when a new player enters the game."
    },
    {
        "q": "What is the max value of Transparency?",
        "options": ["100", "255", "1", "10"],
        "correct": 2,
        "category": "scripting",
        "difficulty": "easy",
        "explanation": "Transparency ranges from 0 (opaque) to 1 (invisible)."
    },
    {
        "q":
        "Which service handles physics simulation?",
        "options":
        ["PhysicsService", "RunService", "SimService", "GameService"],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "medium",
        "explanation":
        "RunService provides events like Heartbeat and RenderStepped for physics and rendering."
    },
    {
        "q":
        "What does task.wait() replace?",
        "options": ["delay()", "wait()", "sleep()", "pause()"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "task.wait() is the modern replacement for the deprecated wait() function."
    },
    {
        "q":
        "What property makes a Part not fall?",
        "options": ["Locked", "Fixed", "Anchored", "Static"],
        "correct":
        2,
        "category":
        "physics",
        "difficulty":
        "easy",
        "explanation":
        "Anchored = true prevents a part from being affected by physics."
    },
    {
        "q":
        "What is the Roblox scripting language called?",
        "options": ["Lua", "Luau", "RScript", "RobloxScript"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "Luau is Roblox's custom fork of Lua with type checking and performance improvements."
    },
    {
        "q":
        "What service handles tweening?",
        "options":
        ["AnimService", "TweenService", "MoveService", "TransitionService"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "TweenService creates smooth property transitions over time."
    },
    {
        "q":
        "What does pcall() do?",
        "options":
        ["Print call", "Protected call", "Player call", "Pause call"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "pcall() runs a function in protected mode, catching errors instead of crashing."
    },
    {
        "q":
        "How do you get the LocalPlayer?",
        "options": [
            "game.LocalPlayer", "Players.LocalPlayer", "GetPlayer()",
            "LocalPlayer()"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "game:GetService('Players').LocalPlayer or game.Players.LocalPlayer."
    },
    {
        "q":
        "What RemoteEvent method does CLIENT use to send to server?",
        "options": ["FireClient", "FireServer", "SendServer", "Invoke"],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "Clients use :FireServer() to send data to the server via RemoteEvents."
    },
    {
        "q": "What is the default WalkSpeed?",
        "options": ["10", "16", "20", "25"],
        "correct": 1,
        "category": "scripting",
        "difficulty": "easy",
        "explanation": "The default Humanoid WalkSpeed is 16 studs per second."
    },
    {
        "q":
        "Which folder is only visible to the server?",
        "options":
        ["ReplicatedStorage", "ServerStorage", "Workspace", "StarterPack"],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "ServerStorage contents are only accessible from server scripts."
    },
    {
        "q":
        "What does :Clone() return?",
        "options":
        ["Nothing", "A copy of the instance", "The original", "An error"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        ":Clone() creates and returns a deep copy of the instance."
    },
    {
        "q":
        "What method destroys an instance?",
        "options": ["Remove()", "Delete()", "Destroy()", "Kill()"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        ":Destroy() permanently removes an instance and disconnects all connections."
    },
    {
        "q":
        "What does math.clamp() do?",
        "options": [
            "Rounds a number", "Constrains between min/max",
            "Returns absolute value", "Floors a number"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "math.clamp(value, min, max) constrains a value within a range."
    },
    {
        "q":
        "What is HumanoidRootPart?",
        "options": [
            "The head", "The primary part of a character", "A GUI element",
            "A sound"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "HumanoidRootPart is the root/primary part that controls character position."
    },
    {
        "q":
        "What does :WaitForChild() do?",
        "options": [
            "Waits forever", "Yields until child exists", "Creates a child",
            "Deletes a child"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        ":WaitForChild() pauses the script until the named child instance appears."
    },

    # ===== 20 NEW HARDER QUESTIONS =====
    {
        "q":
        "What metamethod is called when you index a table with a missing key?",
        "options": ["__newindex", "__index", "__call", "__tostring"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "__index is invoked when accessing a key that doesn't exist in the table."
    },
    {
        "q":
        "What is the maximum number of requests per minute for OrderedDataStore:GetSortedAsync()?",
        "options": ["60", "30", "5", "100"],
        "correct":
        2,
        "category":
        "services",
        "difficulty":
        "expert",
        "explanation":
        "OrderedDataStore:GetSortedAsync() has a limit of 5 requests per minute per key."
    },
    {
        "q":
        "What CFrame method returns only the rotational component?",
        "options": [
            "CFrame.Angles()", "CFrame:GetComponents()", "CFrame.Rotation",
            "CFrame:ToEulerAngles()"
        ],
        "correct":
        2,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "CFrame.Rotation returns a copy of the CFrame with position zeroed out, keeping only rotation."
    },
    {
        "q":
        "In a client-server model, where should RemoteEvent data validation happen?",
        "options": ["Client only", "Both equally", "Server only", "Neither"],
        "correct":
        2,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "NEVER trust client data. Always validate on the server since clients can be exploited."
    },
    {
        "q":
        "What happens when you call :Destroy() on a player's character?",
        "options": [
            "Player is kicked", "Character respawns after delay",
            "Nothing happens", "Server crashes"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "Destroying a character triggers CharacterRemoving and the player respawns after RespawnTime."
    },
    {
        "q":
        "What is the purpose of CollectionService?",
        "options": [
            "Collect garbage", "Tag instances for batch operations",
            "Manage collections UI", "Handle microtransactions"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "hard",
        "explanation":
        "CollectionService lets you tag instances and iterate over all instances with a given tag."
    },
    {
        "q":
        "What does workspace.StreamingEnabled control?",
        "options": [
            "Audio streaming", "Instance streaming/replication",
            "Video playback", "Data transfer speed"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "StreamingEnabled controls content streaming, only loading parts of the map near the player."
    },
    {
        "q":
        "What Roblox API yields (pauses) the current thread?",
        "options": [
            "game.Loaded", "task.spawn()", "workspace:Raycast()",
            "MarketplaceService:GetProductInfo()"
        ],
        "correct":
        3,
        "category":
        "services",
        "difficulty":
        "expert",
        "explanation":
        "GetProductInfo() is an async HTTP call that yields the thread until the response arrives."
    },
    {
        "q":
        "What is the difference between task.spawn() and coroutine.wrap()?",
        "options": [
            "No difference",
            "task.spawn runs on next frame, coroutine.wrap runs immediately",
            "task.spawn uses Roblox scheduler, coroutine.wrap uses Lua scheduler",
            "They are aliases"
        ],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "expert",
        "explanation":
        "task.spawn uses Roblox's task scheduler with error handling; coroutine.wrap uses raw Lua coroutines."
    },
    {
        "q":
        "What property prevents a MeshPart from being modified by exploiters?",
        "options": [
            "Locked", "Archivable = false", "There is no such property",
            "SecurityLevel"
        ],
        "correct":
        2,
        "category":
        "security",
        "difficulty":
        "hard",
        "explanation":
        "There's no property that prevents client-side modification. Server validation is the only real protection."
    },
    {
        "q":
        "What does the '__mode' metamethod field control?",
        "options": [
            "Script execution mode", "Weak reference behavior",
            "Network replication", "Rendering priority"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "expert",
        "explanation":
        "__mode = 'k', 'v', or 'kv' makes table keys/values weak references for garbage collection."
    },
    {
        "q":
        "How many DataStore budget units does SetAsync consume?",
        "options": ["1", "5", "6", "10"],
        "correct":
        2,
        "category":
        "services",
        "difficulty":
        "expert",
        "explanation":
        "SetAsync costs 6 budget units (write request) in the DataStore budget system."
    },
    {
        "q":
        "What is the maximum Part size in studs (one axis)?",
        "options": ["512", "1024", "2048", "4096"],
        "correct":
        2,
        "category":
        "studio",
        "difficulty":
        "hard",
        "explanation":
        "Individual parts can be up to 2048 studs in any single dimension."
    },
    {
        "q":
        "What does Terrain:WriteVoxels() do?",
        "options": [
            "Writes save data", "Edits terrain voxels in bulk",
            "Creates voxel models", "Generates terrain heightmap"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "expert",
        "explanation":
        "WriteVoxels() efficiently modifies terrain data in bulk using Region3 and material/occupancy arrays."
    },
    {
        "q":
        "What is the render step order: PreRender, PreAnimation, PreSimulation?",
        "options": [
            "PreRender → PreAnimation → PreSimulation",
            "PreAnimation → PreSimulation → PreRender",
            "PreSimulation → PreAnimation → PreRender",
            "PreAnimation → PreRender → PreSimulation"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "expert",
        "explanation":
        "The order is PreAnimation → PreSimulation → PreRender in the Roblox task scheduler pipeline."
    },
    {
        "q":
        "What does HttpService:JSONEncode(math.huge) return?",
        "options": ["'Infinity'", "null", "Error is thrown", "'inf'"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "expert",
        "explanation":
        "math.huge (infinity) is not valid JSON. JSONEncode throws an error for non-finite numbers."
    },
    {
        "q":
        "How many players can a single RemoteEvent:FireClient() target?",
        "options":
        ["All players", "1 specific player", "Up to 50", "Server only"],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "FireClient(player, ...) targets exactly one specific player. Use FireAllClients() for all."
    },
    {
        "q":
        "What is the maximum string length DataStore can save per key?",
        "options": [
            "260,000 chars", "4,194,304 chars", "65,536 chars",
            "1,000,000 chars"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "expert",
        "explanation":
        "DataStore values can be up to 4,194,304 characters (4MB) when serialized as JSON."
    },
    {
        "q":
        "What does Actor in Roblox enable?",
        "options": [
            "NPC AI system", "Parallel Luau execution", "Animation playback",
            "Voice chat"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Actors enable Parallel Luau, allowing scripts to run on multiple threads for better performance."
    },
    {
        "q":
        "What is the frame budget (in ms) to maintain 60 FPS?",
        "options": ["33.33ms", "16.67ms", "8.33ms", "25ms"],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "At 60 FPS, each frame has ~16.67ms (1000ms / 60 frames) of budget."
    },
    # ===== 40 MORE QUESTIONS =====

    # --- SCRIPTING ---
    {
        "q":
        "What keyword is used to define a type in Luau?",
        "options": ["typedef", "type", "define", "struct"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "The 'type' keyword in Luau lets you create type aliases for type checking."
    },
    {
        "q":
        "What does table.freeze() do?",
        "options": [
            "Pauses a coroutine", "Makes a table read-only", "Clears a table",
            "Sorts a table"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "table.freeze() makes a table immutable — no keys can be added, removed, or changed."
    },
    {
        "q":
        "What does the # operator return on a table?",
        "options": [
            "Total key count", "Length of array portion", "Memory size",
            "Depth of table"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "# returns the length of the contiguous integer-keyed (array) portion of a table."
    },
    {
        "q":
        "What function connects a function to an event?",
        "options": [":Bind()", ":Listen()", ":Connect()", ":Attach()"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        ":Connect() attaches a callback function to a Roblox event (RBXScriptSignal)."
    },
    {
        "q":
        "What does tostring() do?",
        "options": [
            "Converts to number", "Converts value to string",
            "Creates a new string object", "Parses JSON"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "tostring() converts any Luau value into its string representation."
    },
    {
        "q":
        "What does tonumber('42') return?",
        "options": ["'42'", "nil", "42", "Error"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "tonumber() converts a string to a number. '42' becomes the number 42."
    },
    {
        "q":
        "How do you create a Vector3 with coordinates (1, 2, 3)?",
        "options": [
            "Vector3(1,2,3)", "Vector3.new(1,2,3)", "newVector3(1,2,3)",
            "Vec3(1,2,3)"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "Vector3.new(x, y, z) is the constructor for creating 3D vectors in Roblox."
    },
    {
        "q":
        "What does string.split() return?",
        "options":
        ["A number", "A boolean", "A table of substrings", "A single string"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "string.split(str, separator) returns a table of substrings split by the delimiter."
    },
    {
        "q":
        "What does unpack() (or table.unpack()) do?",
        "options": [
            "Compresses a table", "Returns all elements as separate values",
            "Removes duplicates", "Reverses a table"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "table.unpack() returns all array elements as individual return values."
    },
    {
        "q":
        "What is the difference between == and ~= in Luau?",
        "options": [
            "Both check equality", "== is assign, ~= is compare",
            "== is equal, ~= is not equal", "No difference"
        ],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "== checks equality, ~= checks inequality. Luau uses ~= instead of != like other languages."
    },
    {
        "q":
        "What does string.format('%d', 3.7) return?",
        "options": ["'3.7'", "'3'", "'4'", "Error"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "%d formats as an integer, truncating the decimal. 3.7 becomes '3'."
    },
    {
        "q":
        "What does the 'continue' keyword do in Luau?",
        "options": [
            "Exits the loop", "Skips to next iteration", "Pauses the loop",
            "Restarts the loop"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "continue skips the rest of the current loop iteration and moves to the next one."
    },
    {
        "q":
        "What is a buffer in Luau?",
        "options": [
            "A string type", "A fixed-size mutable binary data type",
            "A queue data structure", "An alias for table"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "expert",
        "explanation":
        "buffer is a Luau type for efficient fixed-size mutable binary data manipulation."
    },
    {
        "q":
        "What does rawset() do?",
        "options": [
            "Sets a value bypassing __newindex", "Sets a raw string",
            "Resets a table", "Encrypts a value"
        ],
        "correct":
        0,
        "category":
        "scripting",
        "difficulty":
        "expert",
        "explanation":
        "rawset(table, key, value) sets a value without triggering the __newindex metamethod."
    },
    {
        "q":
        "What does select('#', ...) return?",
        "options": [
            "The last argument", "The number of varargs", "The first argument",
            "A table of arguments"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "select('#', ...) returns the total count of arguments in the vararg list."
    },

    # --- SERVICES ---
    {
        "q":
        "What service handles in-game purchases?",
        "options": [
            "PurchaseService", "MarketplaceService", "EconomyService",
            "ShopService"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "MarketplaceService handles developer products, game passes, and asset purchases."
    },
    {
        "q":
        "What service provides user input detection?",
        "options": [
            "InputService", "UserInputService", "ControllerService",
            "KeyboardService"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "UserInputService detects keyboard, mouse, touch, and gamepad input."
    },
    {
        "q":
        "What does ContextActionService do?",
        "options": [
            "Manages UI context menus",
            "Binds actions to inputs with priority",
            "Handles right-click menus", "Sorts actions alphabetically"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "medium",
        "explanation":
        "ContextActionService binds functions to inputs with priority and automatic mobile button support."
    },
    {
        "q":
        "What method of DataStore is safer than SetAsync?",
        "options": ["SaveAsync", "UpdateAsync", "WriteAsync", "PushAsync"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "hard",
        "explanation":
        "UpdateAsync reads the current value first, preventing race conditions unlike SetAsync."
    },
    {
        "q":
        "What service manages teams in a game?",
        "options": ["GroupService", "Teams", "TeamService", "PartyService"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "The Teams service (game:GetService('Teams')) manages team objects in the game."
    },
    {
        "q":
        "What does MemoryStoreService provide?",
        "options": [
            "Permanent storage", "Low-latency temporary storage",
            "Client-side cache", "File system access"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "hard",
        "explanation":
        "MemoryStoreService offers fast, temporary storage (sorted maps, queues) that expires after 45 days max."
    },
    {
        "q":
        "What does MessagingService do?",
        "options": [
            "Sends chat messages", "Cross-server communication",
            "Email notifications", "Error logging"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "hard",
        "explanation":
        "MessagingService enables real-time communication between different game servers."
    },
    {
        "q":
        "What does ReplicatedStorage do?",
        "options": [
            "Stores server-only data",
            "Stores data visible to both client and server",
            "Replicates physics", "Backs up data"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "ReplicatedStorage holds objects that are replicated to both the server and all clients."
    },
    {
        "q":
        "What service manages sound playback globally?",
        "options":
        ["AudioService", "SoundService", "MusicService", "MediaService"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "easy",
        "explanation":
        "SoundService controls global sound properties like ambient reverb and distance model."
    },
    {
        "q":
        "What does PathfindingService do?",
        "options": [
            "Finds file paths", "Computes NPC navigation paths",
            "Draws bezier curves", "Maps terrain"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "medium",
        "explanation":
        "PathfindingService creates paths for NPCs to navigate around obstacles using A* pathfinding."
    },

    # --- PHYSICS ---
    {
        "q":
        "What does workspace:Raycast() return when it hits something?",
        "options": ["A Part", "A RaycastResult", "A Vector3", "A boolean"],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "medium",
        "explanation":
        "Raycast returns a RaycastResult containing Instance, Position, Normal, and Material."
    },
    {
        "q":
        "What property of a Part controls its physical density?",
        "options": ["Weight", "Mass", "CustomPhysicalProperties", "Density"],
        "correct":
        2,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "CustomPhysicalProperties lets you set Density, Friction, Elasticity, and more."
    },
    {
        "q":
        "What constraint acts like a spring between two parts?",
        "options": [
            "WeldConstraint", "SpringConstraint", "RopeConstraint",
            "HingeConstraint"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "medium",
        "explanation":
        "SpringConstraint simulates a spring force between two Attachments."
    },
    {
        "q":
        "What does Massless = true do on a Part?",
        "options": [
            "Removes the part", "Part doesn't contribute mass to assembly",
            "Disables collisions", "Makes part invisible"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "Massless parts don't add mass to their assembly, useful for cosmetic attachments."
    },
    {
        "q":
        "What does workspace.Gravity control?",
        "options": [
            "Player speed", "Acceleration due to gravity", "Time scale",
            "Air resistance"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "easy",
        "explanation":
        "workspace.Gravity sets the gravitational acceleration (default 196.2 studs/s²)."
    },

    # --- SECURITY ---
    {
        "q":
        "Why should you never store currency values on the client?",
        "options": [
            "It's slower", "Clients can modify local values via exploits",
            "It uses too much memory", "Roblox doesn't allow it"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "Exploiters can change any client-side value. Currency must be tracked server-side only."
    },
    {
        "q":
        "What is 'sanity checking' in Roblox security?",
        "options": [
            "Checking player mental health",
            "Verifying data is reasonable before processing",
            "Testing for bugs", "Checking ping"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "Sanity checking means validating that incoming data (especially from clients) is within expected bounds."
    },
    {
        "q":
        "What is rate limiting used for?",
        "options": [
            "Speeding up code", "Preventing spam/abuse of RemoteEvents",
            "Reducing latency", "Compressing data"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "hard",
        "explanation":
        "Rate limiting restricts how frequently a player can fire RemoteEvents, preventing abuse and spam."
    },

    # --- OPTIMIZATION ---
    {
        "q":
        "What does workspace.StreamingEnabled improve?",
        "options": [
            "Audio quality", "Client memory usage and load times",
            "Server tick rate", "Script speed"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "StreamingEnabled reduces client memory by only loading nearby parts of the map."
    },
    {
        "q":
        "What is the best practice for handling many similar objects?",
        "options": [
            "Clone each one individually", "Use object pooling",
            "Create them all at once", "Use wait() between each"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Object pooling reuses inactive objects instead of constantly creating/destroying, reducing GC pressure."
    },
    {
        "q":
        "What does task.defer() do?",
        "options": [
            "Delays by 1 second",
            "Runs function after current resumption cycle", "Cancels a task",
            "Runs synchronously"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "task.defer() schedules a function to run after the current thread and any threads it resumes finish."
    },

    # --- STUDIO ---
    {
        "q": "What keyboard shortcut plays a game in Roblox Studio?",
        "options": ["F1", "F5", "F8", "F12"],
        "correct": 1,
        "category": "studio",
        "difficulty": "easy",
        "explanation": "F5 starts playtesting the game in Roblox Studio."
    },
    {
        "q":
        "What is the Output window used for?",
        "options": [
            "3D modeling", "Viewing print/error messages",
            "Editing properties", "Managing plugins"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Output window shows print(), warn(), and error messages from scripts."
    },
    {
        "q":
        "What does Ctrl+Z do in Studio?",
        "options":
        ["Zoom in", "Undo last action", "Save file", "Open terminal"],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "Ctrl+Z undoes the last action in Roblox Studio, just like most applications."
    },
    # ===== 20 ADDITIONAL QUESTIONS =====

    # --- SCRIPTING ---
    {
        "q":
        "What does table.find() return if the value is not found?",
        "options": ["0", "false", "nil", "-1"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "table.find() returns nil if the value isn't found in the array portion of the table."
    },
    {
        "q":
        "What is the correct way to concatenate strings in Luau?",
        "options":
        ["str1 + str2", "str1 .. str2", "str1 & str2", "concat(str1, str2)"],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "The .. operator is used for string concatenation in Luau."
    },
    {
        "q":
        "What does game:GetService() do?",
        "options": [
            "Creates a new service", "Returns a reference to a service",
            "Deletes a service", "Restarts a service"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "easy",
        "explanation":
        "GetService() safely retrieves a reference to a Roblox service by name."
    },
    {
        "q":
        "What does os.clock() return?",
        "options": [
            "Current date", "CPU time elapsed in seconds", "Server uptime",
            "Unix timestamp"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "os.clock() returns high-precision CPU time, useful for benchmarking code performance."
    },
    {
        "q":
        "What does Instance:GetAttribute() do?",
        "options": [
            "Gets a property", "Gets a custom attribute value",
            "Gets the class name", "Gets children count"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "GetAttribute() retrieves the value of a custom attribute set on an instance."
    },
    {
        "q":
        "What does Instance:IsA() check?",
        "options": [
            "If instance exists",
            "If instance is a specific class or inherits from it",
            "If instance is anchored", "If instance is visible"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "IsA() returns true if the instance is of the given class or inherits from it."
    },
    {
        "q":
        "What does tick() return?",
        "options": [
            "Frames per second", "Unix timestamp (deprecated)",
            "Time since game start", "Server lag"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "tick() returns a Unix timestamp but is deprecated. Use os.clock() or workspace:GetServerTimeNow() instead."
    },
    {
        "q":
        "What is the purpose of typeof() over type()?",
        "options": [
            "No difference",
            "typeof() recognizes Roblox types like Vector3, CFrame",
            "typeof() is faster", "type() is deprecated"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "typeof() returns specific Roblox type names like 'Vector3' while type() would just return 'userdata'."
    },
    {
        "q":
        "What does table.create(10, 0) do?",
        "options": [
            "Creates 10 tables", "Creates array of 10 zeros",
            "Creates a dictionary", "Errors out"
        ],
        "correct":
        1,
        "category":
        "scripting",
        "difficulty":
        "hard",
        "explanation":
        "table.create(n, value) pre-allocates an array of size n filled with the given value."
    },
    {
        "q":
        "What happens if you index nil?",
        "options":
        ["Returns nil", "Returns 0", "Throws an error", "Returns false"],
        "correct":
        2,
        "category":
        "scripting",
        "difficulty":
        "medium",
        "explanation":
        "Attempting to index nil (e.g., nil.something) throws a runtime error."
    },

    # --- SERVICES ---
    {
        "q":
        "What does TeleportService do?",
        "options": [
            "Moves parts", "Teleports players between places/servers",
            "Handles fast travel UI", "Manages spawn points"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "medium",
        "explanation":
        "TeleportService teleports players to different places or reserved servers."
    },
    {
        "q":
        "What service handles player chat?",
        "options":
        ["ChatService", "TextChatService", "MessageService", "TalkService"],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "medium",
        "explanation":
        "TextChatService is the modern system for handling in-game text chat."
    },
    {
        "q":
        "What does TextService:GetTextSize() return?",
        "options": [
            "Font name", "Vector2 of text dimensions", "Character count",
            "Text color"
        ],
        "correct":
        1,
        "category":
        "services",
        "difficulty":
        "hard",
        "explanation":
        "GetTextSize() calculates the pixel width and height a string will occupy with given font settings."
    },

    # --- PHYSICS ---
    {
        "q":
        "What is an Assembly in Roblox physics?",
        "options": [
            "A script collection", "A group of connected rigid parts",
            "A plugin", "An animation set"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "An assembly is a group of parts connected by rigid joints that move as one physics body."
    },
    {
        "q":
        "What does Part.CanCollide = false do?",
        "options": [
            "Makes part invisible", "Other parts pass through it",
            "Disables gravity", "Locks the part"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "easy",
        "explanation":
        "CanCollide = false allows other parts and characters to pass through without physical collision."
    },
    {
        "q":
        "What constraint connects two parts with zero relative movement?",
        "options": [
            "HingeConstraint", "SpringConstraint", "WeldConstraint",
            "RopeConstraint"
        ],
        "correct":
        2,
        "category":
        "physics",
        "difficulty":
        "easy",
        "explanation":
        "WeldConstraint rigidly locks two parts together with no relative movement allowed."
    },

    # --- SECURITY ---
    {
        "q":
        "What is a 'noclip exploit'?",
        "options": [
            "Speed hack", "Bypassing collision to walk through walls",
            "Infinite jump", "Auto-aim"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "Noclip exploits disable CanCollide on the character, letting exploiters pass through solid objects."
    },

    # --- OPTIMIZATION ---
    {
        "q":
        "Why should you avoid using while true do wait() end?",
        "options": [
            "It crashes the server",
            "wait() is deprecated and it wastes performance",
            "It's a syntax error", "It only works on client"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "medium",
        "explanation":
        "wait() is deprecated. Use task.wait() and consider event-driven design instead of constant polling."
    },

    # --- STUDIO ---
    {
        "q":
        "What does the Explorer window show?",
        "options": [
            "Script errors", "Hierarchy of all instances in the game",
            "Properties of selected part", "Asset marketplace"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Explorer window displays the full instance tree/hierarchy of your game."
    },
    {
        "q":
        "What does the MicroProfiler help with?",
        "options": [
            "Writing code", "Analyzing frame-by-frame performance",
            "3D modeling", "Publishing games"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "expert",
        "explanation":
        "The MicroProfiler (Ctrl+F6) shows detailed per-frame timing data to find performance bottlenecks."
    },
    {
        "q":
        "What year was Roblox officially launched?",
        "options": ["2004", "2006", "2008", "2010"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "Roblox officially launched to the public in September 2006."
    },
    {
        "q":
        "What is the in-game currency of Roblox called?",
        "options": ["Coins", "Robux", "Credits", "Gems"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "Robux (R$) is the official virtual currency used across the Roblox platform."
    },
    {
        "q":
        "What is a 'Place' in Roblox?",
        "options": [
            "A player's profile", "An individual game world/map",
            "A type of Part", "A server region"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "A Place is a single game world. Multiple Places can exist within one Experience (Universe)."
    },
    {
        "q":
        "What is a Roblox 'Experience'?",
        "options": [
            "A single script", "A collection of Places (game)",
            "A player's level", "An animation"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "Experience (formerly Game) is the top-level project containing one or more Places."
    },
    {
        "q":
        "What does R6 mean in Roblox?",
        "options": [
            "Version 6", "6-part character rig", "6 players max",
            "Render level 6"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "R6 is the classic 6-part character model (head, torso, 2 arms, 2 legs)."
    },
    {
        "q":
        "What does R15 mean in Roblox?",
        "options": [
            "15 FPS mode", "15-part character rig", "15 players max",
            "Resolution 15"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "R15 is the modern 15-part character rig with upper/lower limbs for smoother animation."
    },
    {
        "q":
        "What is a 'stud' in Roblox?",
        "options": [
            "A player rank", "The base unit of measurement", "A type of bolt",
            "A decoration"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "A stud is Roblox's unit of distance. A default character is about 5 studs tall."
    },
    {
        "q":
        "What file format does Roblox use for place files?",
        "options": [".rblx", ".rbxl", ".rbx", ".rplace"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "medium",
        "explanation":
        ".rbxl is the Roblox place file format. .rbxm is used for model files."
    },
    {
        "q":
        "What is the Roblox Developer Hub called?",
        "options": ["DevDocs", "Creator Hub", "RobloxDev", "BuilderBase"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "The Creator Hub (create.roblox.com) is where developers manage and publish experiences."
    },
    {
        "q":
        "What is the maximum players a single Roblox server supports?",
        "options": ["50", "100", "700", "1000"],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "medium",
        "explanation":
        "A single Roblox server supports up to 100 players by default."
    },
    {
        "q":
        "What was Roblox originally called during development?",
        "options": ["Dynablocks", "BlockWorld", "BuildIt", "GoBlocks"],
        "correct":
        0,
        "category":
        "general",
        "difficulty":
        "hard",
        "explanation":
        "Roblox was originally called DynaBlocks before being renamed to Roblox in 2004."
    },
    {
        "q":
        "What does UGC stand for in Roblox?",
        "options": [
            "Universal Game Code", "User Generated Content",
            "Unified Graphics Card", "Ultra Game Creator"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "UGC stands for User Generated Content — items created by players for the Avatar Shop."
    },
    {
        "q":
        "What is a Game Pass?",
        "options": [
            "A monthly subscription", "A one-time purchasable perk for a game",
            "A free trial", "A cheat code"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "easy",
        "explanation":
        "Game Passes are one-time purchases that grant permanent perks within a specific experience."
    },
    {
        "q":
        "What is a Developer Product?",
        "options": [
            "A tool for developers",
            "A purchasable item that can be bought multiple times", "A plugin",
            "A badge"
        ],
        "correct":
        1,
        "category":
        "general",
        "difficulty":
        "medium",
        "explanation":
        "Developer Products can be purchased repeatedly, ideal for in-game currency or consumables."
    },
    {
        "q":
        "What percentage does Roblox take from developer earnings?",
        "options": ["10%", "30%", "50%", "70%"],
        "correct":
        3,
        "category":
        "general",
        "difficulty":
        "hard",
        "explanation":
        "Roblox takes approximately 70% of Robux transactions. Developers receive about 30% through DevEx."
    },
    {
        "q":
        "What does F8 do in Roblox Studio?",
        "options": [
            "Play solo", "Start server test with multiple clients",
            "Open properties", "Save file"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "medium",
        "explanation":
        "F8 starts a local server test allowing you to simulate multiple players."
    },
    {
        "q":
        "What is the Properties window used for?",
        "options": [
            "Writing scripts", "Viewing and editing instance properties",
            "Managing plugins", "File browsing"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Properties window shows all editable properties of the currently selected instance."
    },
    {
        "q":
        "What does the Toolbox in Studio contain?",
        "options": [
            "Script templates only", "Free models, plugins, and assets",
            "Debugging tools", "Version history"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Toolbox provides access to free models, decals, meshes, audio, and plugins from the library."
    },
    {
        "q":
        "What is Team Create?",
        "options": [
            "A PvP mode", "Collaborative real-time editing in Studio",
            "A team management plugin", "A group feature"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "Team Create allows multiple developers to edit the same place simultaneously in real time."
    },
    {
        "q":
        "What does the Command Bar do in Studio?",
        "options": [
            "Opens terminal", "Executes Luau code directly",
            "Runs shell commands", "Manages servers"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "medium",
        "explanation":
        "The Command Bar lets you type and execute Luau code instantly for quick testing and debugging."
    },
    {
        "q":
        "What tool is used to rotate parts in Studio?",
        "options":
        ["Move tool", "Scale tool", "Rotate tool", "Transform tool"],
        "correct":
        2,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Rotate tool (Ctrl+R shortcut) lets you rotate selected parts around their pivot."
    },
    {
        "q":
        "What does 'Publish to Roblox' do?",
        "options": [
            "Saves locally", "Uploads the place to Roblox servers",
            "Exports as file", "Sends to friends"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "Publishing uploads your place to Roblox's servers so players can access and play it."
    },
    {
        "q":
        "What is the Script Analysis window for?",
        "options": [
            "Performance stats",
            "Detecting script warnings and errors before runtime",
            "AI code generation", "Memory profiling"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "medium",
        "explanation":
        "Script Analysis shows static analysis warnings and errors without needing to run the game."
    },
    {
        "q":
        "What does the Terrain Editor do?",
        "options": [
            "Edits scripts", "Sculpts and paints 3D terrain", "Manages audio",
            "Creates UI"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "The Terrain Editor provides tools to generate, sculpt, paint, and smooth voxel terrain."
    },
    {
        "q":
        "How do you add a Script to a Part in Studio?",
        "options": [
            "Drag from toolbox only",
            "Right-click Part > Insert Object > Script",
            "Type it in command bar", "Scripts can't go in Parts"
        ],
        "correct":
        1,
        "category":
        "studio",
        "difficulty":
        "easy",
        "explanation":
        "Right-click any instance in Explorer, choose Insert Object, then select Script or LocalScript."
    },
    {
        "q":
        "What is 'micro-optimization' and why is it often bad?",
        "options": [
            "Optimizing tiny things that don't matter", "Making code smaller",
            "Using MicroProfiler", "Compressing assets"
        ],
        "correct":
        0,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Micro-optimization focuses on trivial gains that waste dev time. Focus on big bottlenecks first."
    },
    {
        "q":
        "Why should you use Enum instead of string comparisons?",
        "options": [
            "Enums look prettier",
            "Enums are compared by value, faster than strings",
            "Strings don't work in Roblox", "No difference"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Enum comparisons are integer-based and faster than string comparisons which check character by character."
    },
    {
        "q":
        "What is instance replication?",
        "options": [
            "Copying scripts", "Syncing instances from server to clients",
            "Duplicating parts", "Backup system"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "medium",
        "explanation":
        "Replication is the automatic process of syncing instance changes from server to connected clients."
    },
    {
        "q":
        "Why is table.insert() slower than t[#t+1]?",
        "options": [
            "It's not slower", "table.insert has function call overhead",
            "It creates a copy", "It sorts the table"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "expert",
        "explanation":
        "table.insert() has extra function call overhead compared to direct index assignment t[#t+1] = value."
    },
    {
        "q":
        "What does Level of Detail (LOD) mean in Roblox?",
        "options": [
            "Script detail level", "Reducing mesh quality at distance",
            "Lighting quality", "Sound fidelity"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "medium",
        "explanation":
        "LOD reduces the polygon count of meshes that are far from the camera to save rendering performance."
    },
    {
        "q":
        "Why should you avoid creating parts every frame?",
        "options": [
            "Parts are free", "It causes massive GC pressure and lag",
            "Roblox limits to 10 per frame", "They become invisible"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "medium",
        "explanation":
        "Creating instances every frame generates garbage collection pressure and tanks performance."
    },
    {
        "q":
        "What is the benefit of using BindableEvents over polling?",
        "options": [
            "They're faster to type",
            "Event-driven code only runs when needed", "They use less memory",
            "They work offline"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Event-driven design fires only when something happens, unlike polling which wastes cycles checking constantly."
    },
    {
        "q":
        "What does :GetChildren() return vs :GetDescendants()?",
        "options": [
            "Same thing",
            "GetChildren = direct children, GetDescendants = all nested",
            "GetDescendants = direct only", "GetChildren = all nested"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "medium",
        "explanation":
        "GetChildren() returns immediate children. GetDescendants() returns ALL nested instances recursively."
    },
    {
        "q":
        "Why should you cache FindFirstChild results?",
        "options": [
            "It returns different results each time",
            "Repeated calls search the hierarchy each time",
            "It might return nil randomly", "Caching is slower"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Each FindFirstChild call traverses children. Store the result in a variable if used multiple times."
    },
    {
        "q":
        "What happens if too many RemoteEvents fire per frame?",
        "options": [
            "Nothing", "Network bandwidth saturation and lag",
            "Server auto-scales", "Events queue forever"
        ],
        "correct":
        1,
        "category":
        "optimization",
        "difficulty":
        "hard",
        "explanation":
        "Excessive RemoteEvent firing saturates bandwidth, causing network lag and potential packet drops."
    },
    {
        "q":
        "What is 'server authority' in game design?",
        "options": [
            "Admin commands", "Server makes all important gameplay decisions",
            "Server has faster internet", "Server picks the host"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "Server authority means the server is the final decision-maker for game state, preventing client cheats."
    },
    {
        "q":
        "Can exploiters see LocalScripts code?",
        "options": [
            "No, it's encrypted", "Yes, they can decompile and read it",
            "Only if published", "Only server scripts"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "hard",
        "explanation":
        "Exploiters can decompile LocalScripts. Never put secrets, keys, or sensitive logic in them."
    },
    {
        "q":
        "What is a 'speed hack' and how to prevent it?",
        "options": [
            "Faster loading, can't prevent",
            "Modifying WalkSpeed, validate movement server-side",
            "Overclocking GPU, use anticheat", "Skipping cutscenes, use flags"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "hard",
        "explanation":
        "Speed hacks modify WalkSpeed/CFrame locally. Server should validate player position over time."
    },
    {
        "q":
        "Why should ModuleScripts with sensitive logic be in ServerScriptService?",
        "options": [
            "They run faster there",
            "Clients cannot access ServerScriptService contents",
            "It's alphabetically first", "No reason"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "medium",
        "explanation":
        "ServerScriptService is server-only. Modules there can't be seen or required by exploiters."
    },
    {
        "q":
        "What is 'remote spoofing'?",
        "options": [
            "Faking server events",
            "Exploiters firing RemoteEvents with fake data", "DNS spoofing",
            "Copying game assets"
        ],
        "correct":
        1,
        "category":
        "security",
        "difficulty":
        "hard",
        "explanation":
        "Remote spoofing is when exploiters fire RemoteEvents with fabricated arguments to cheat."
    },
    {
        "q":
        "What does NetworkOwnership control?",
        "options": [
            "Who owns the game", "Which machine simulates a part's physics",
            "Network speed", "Player permissions"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "expert",
        "explanation":
        "NetworkOwnership determines whether the server or a client simulates physics for a part."
    },
    {
        "q":
        "What is a BodyVelocity used for? (Legacy)",
        "options": [
            "Measuring speed", "Applying constant velocity force to a part",
            "Stopping movement", "Changing gravity"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "medium",
        "explanation":
        "BodyVelocity (legacy) applies force to maintain a target velocity. Modern alternative is LinearVelocity."
    },
    {
        "q":
        "What replaced BodyPosition and BodyVelocity?",
        "options": [
            "ForceField", "AlignPosition and LinearVelocity", "Anchoring",
            "TweenService"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "Constraint-based movers like AlignPosition and LinearVelocity replaced legacy body movers."
    },
    {
        "q":
        "What does Part.CanTouch control?",
        "options": [
            "Touch screen input", "Whether Touched event fires for this part",
            "Physical collision", "Player interaction"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "medium",
        "explanation":
        "CanTouch = false prevents the Touched and TouchEnded events from firing for that part."
    },
    {
        "q":
        "What does Part.CanQuery control?",
        "options": [
            "Database queries",
            "Whether raycasts and spatial queries detect this part",
            "Search functionality", "Chat filtering"
        ],
        "correct":
        1,
        "category":
        "physics",
        "difficulty":
        "hard",
        "explanation":
        "CanQuery = false makes the part invisible to raycasts, GetPartsInPart, and other spatial queries."
    },
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


def _get_unseen_fallback(user_id: int,
                         category: str = None,
                         difficulty: str = None) -> dict:
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


async def generate_ai_trivia(user_id: int,
                             category: str = "random",
                             difficulty: str = "medium",
                             force_ai: bool = False) -> dict:
    """Generate a trivia question — uses fallbacks first, then AI when exhausted"""
    global _recent_ai_questions

    if category == "random":
        actual_category = random.choice(
            [k for k in TRIVIA_CATEGORIES.keys() if k != "random"])
    else:
        actual_category = category

    cat_info = TRIVIA_CATEGORIES.get(actual_category,
                                     TRIVIA_CATEGORIES["general"])

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
        recent_context = f"\n\nDO NOT repeat these recent questions:\n" + "\n".join(
            f"- {q}" for q in recent_qs)

    # User's seen questions to avoid
    seen = _user_question_history.get(user_id, set())
    seen_fallback_qs = [
        q["q"] for q in FALLBACK_QUESTIONS if _question_hash(q) in seen
    ]
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
        f"{recent_context}")

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

            if not isinstance(question["options"], list) or len(
                    question["options"]) != 4:
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
    question = await generate_ai_trivia(0,
                                        category="random",
                                        difficulty=difficulty,
                                        force_ai=True)
    return question


# ==================== SNIPPET BOXES ====================
SNIPPET_BOXES = {
    "common": {
        "chance":
        60,
        "color":
        0x95A5A6,
        "emoji":
        "⬜",
        "snippets": [{
            "name": "Hello World",
            "code": 'print("Hello, World!")',
            "desc": "The classic first script"
        }, {
            "name": "Part Color Changer",
            "code": 'workspace.Part.BrickColor = BrickColor.new("Really red")',
            "desc": "Changes a part color"
        }, {
            "name": "Simple Kill Brick",
            "code":
            'script.Parent.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then hum.Health = 0 end\nend)',
            "desc": "A basic kill brick"
        }, {
            "name": "Anchored Toggle",
            "code":
            'local part = script.Parent\npart.Anchored = not part.Anchored',
            "desc": "Toggle part anchored state"
        }, {
            "name": "Print Player Name",
            "code":
            'game.Players.PlayerAdded:Connect(function(player)\n    print(player.Name .. " joined!")\nend)',
            "desc": "Prints when someone joins"
        }, {
            "name": "Part Transparency",
            "code":
            'local part = script.Parent\nfor i = 0, 1, 0.1 do\n    part.Transparency = i\n    task.wait(0.1)\nend',
            "desc": "Fades a part to invisible"
        }, {
            "name": "Damage on Touch",
            "code":
            'script.Parent.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then hum:TakeDamage(10) end\nend)',
            "desc": "Deals 10 damage on touch"
        }, {
            "name": "Spawn Message",
            "code":
            'game.Players.PlayerAdded:Connect(function(player)\n    player.CharacterAdded:Connect(function()\n        print(player.Name .. " has spawned!")\n    end)\nend)',
            "desc": "Prints when player character spawns"
        }, {
            "name": "Part Destroyer",
            "code":
            'script.Parent.Touched:Connect(function(hit)\n    if hit:IsA("BasePart") and not hit.Anchored then\n        hit:Destroy()\n    end\nend)',
            "desc": "Destroys unanchored parts on touch"
        }, {
            "name": "Brick Counter",
            "code":
            'local count = #workspace:GetChildren()\nprint("There are " .. count .. " objects in workspace")',
            "desc": "Counts workspace objects"
        }, {
            "name": "Loop Spawner",
            "code":
            'while true do\n    local p = Instance.new("Part")\n    p.Position = Vector3.new(math.random(-50,50), 20, math.random(-50,50))\n    p.Parent = workspace\n    task.wait(1)\nend',
            "desc": "Spawns parts every second"
        }, {
            "name": "WalkSpeed Setter",
            "code":
            'game.Players.PlayerAdded:Connect(function(player)\n    player.CharacterAdded:Connect(function(char)\n        char:WaitForChild("Humanoid").WalkSpeed = 32\n    end)\nend)',
            "desc": "Doubles walk speed for all players"
        }, {
            "name": "Part Cloner",
            "code":
            'local original = script.Parent\nlocal clone = original:Clone()\nclone.Position = original.Position + Vector3.new(5, 0, 0)\nclone.Parent = workspace',
            "desc": "Clones a part next to the original"
        }, {
            "name": "Simple Timer",
            "code":
            'for i = 10, 0, -1 do\n    print("Time left: " .. i)\n    task.wait(1)\nend\nprint("Time is up!")',
            "desc": "A basic countdown timer"
        }, {
            "name": "Jump Height Changer",
            "code":
            'game.Players.PlayerAdded:Connect(function(player)\n    player.CharacterAdded:Connect(function(char)\n        char:WaitForChild("Humanoid").JumpHeight = 100\n    end)\nend)',
            "desc": "Makes players jump super high"
        }, {
            "name": "Part Color Randomizer",
            "code":
            'local part = script.Parent\nwhile true do\n    part.BrickColor = BrickColor.random()\n    task.wait(0.5)\nend',
            "desc": "Randomizes part color every half second"
        }]
    },
    "uncommon": {
        "chance":
        25,
        "color":
        0x2ECC71,
        "emoji":
        "🟩",
        "snippets": [
            {
                "name": "Part Spinner",
                "code":
                'local part = script.Parent\nlocal RS = game:GetService("RunService")\nRS.Heartbeat:Connect(function(dt)\n    part.CFrame = part.CFrame * CFrame.Angles(0, math.rad(90) * dt, 0)\nend)',
                "desc": "Smoothly spinning part"
            },
            {
                "name": "Click Counter",
                "code":
                'local cd = Instance.new("ClickDetector", script.Parent)\nlocal count = 0\ncd.MouseClick:Connect(function(player)\n    count = count + 1\n    print(player.Name .. " clicked! Total: " .. count)\nend)',
                "desc": "Counts clicks on a part"
            },
            {
                "name": "Rainbow Part",
                "code":
                'local part = script.Parent\nwhile true do\n    for i = 0, 1, 0.01 do\n        part.Color = Color3.fromHSV(i, 1, 1)\n        task.wait(0.03)\n    end\nend',
                "desc": "Rainbow color cycling part"
            },
            {
                "name": "Speed Boost Pad",
                "code":
                'script.Parent.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then\n        hum.WalkSpeed = 50\n        task.wait(5)\n        hum.WalkSpeed = 16\n    end\nend)',
                "desc": "Temporary speed boost"
            },
            {
                "name": "Lava Floor",
                "code":
                'local lava = script.Parent\nlava.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    if hum then\n        hum:TakeDamage(5)\n        hit.Parent:FindFirstChild("HumanoidRootPart").Velocity = Vector3.new(0, 50, 0)\n    end\nend)',
                "desc": "Lava that damages and bounces players"
            },
            {
                "name": "Door System",
                "code":
                'local door = script.Parent\nlocal open = false\nlocal cd = Instance.new("ClickDetector", door)\ncd.MouseClick:Connect(function()\n    open = not open\n    local ts = game:GetService("TweenService")\n    local goal = open and {Position = door.Position + Vector3.new(0, door.Size.Y, 0)} or {Position = door.Position - Vector3.new(0, door.Size.Y, 0)}\n    ts:Create(door, TweenInfo.new(0.5), goal):Play()\nend)',
                "desc": "Clickable sliding door"
            },
            {
                "name": "Coin Collector",
                "code":
                'local coin = script.Parent\ncoin.Touched:Connect(function(hit)\n    local player = game.Players:GetPlayerFromCharacter(hit.Parent)\n    if player then\n        local ls = player:FindFirstChild("leaderstats")\n        if ls then\n            ls.Coins.Value = ls.Coins.Value + 1\n            coin:Destroy()\n        end\n    end\nend)',
                "desc": "Collectible coin with leaderstat"
            },
            {
                "name": "Proximity Prompt Door",
                "code":
                'local prompt = Instance.new("ProximityPrompt")\nprompt.ActionText = "Open"\nprompt.Parent = script.Parent\nlocal open = false\nprompt.Triggered:Connect(function()\n    open = not open\n    prompt.ActionText = open and "Close" or "Open"\n    script.Parent.Transparency = open and 0.8 or 0\n    script.Parent.CanCollide = not open\nend)',
                "desc": "ProximityPrompt toggle door"
            },
            {
                "name": "Leaderstats Setup",
                "code":
                'game.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new("Folder")\n    ls.Name = "leaderstats"\n    ls.Parent = player\n    local coins = Instance.new("IntValue")\n    coins.Name = "Coins"\n    coins.Value = 0\n    coins.Parent = ls\n    local wins = Instance.new("IntValue")\n    wins.Name = "Wins"\n    wins.Value = 0\n    wins.Parent = ls\nend)',
                "desc": "Standard leaderboard setup"
            },
            {
                "name": "Moving Platform",
                "code":
                'local platform = script.Parent\nlocal ts = game:GetService("TweenService")\nlocal startPos = platform.Position\nlocal endPos = startPos + Vector3.new(30, 0, 0)\nwhile true do\n    ts:Create(platform, TweenInfo.new(3, Enum.EasingStyle.Sine), {Position = endPos}):Play()\n    task.wait(3.5)\n    ts:Create(platform, TweenInfo.new(3, Enum.EasingStyle.Sine), {Position = startPos}):Play()\n    task.wait(3.5)\nend',
                "desc": "Platform that moves back and forth"
            },
            {
                "name": "Random Color Bricks",
                "code":
                'for _, part in ipairs(workspace:GetDescendants()) do\n    if part:IsA("BasePart") then\n        part.Color = Color3.fromRGB(math.random(0,255), math.random(0,255), math.random(0,255))\n    end\nend',
                "desc": "Randomizes every part color in workspace"
            },
            {
                "name": "Double Jump",
                "code":
                'local UIS = game:GetService("UserInputService")\nlocal player = game.Players.LocalPlayer\nlocal canDouble = false\nlocal hasDoubled = false\nplayer.CharacterAdded:Connect(function(char)\n    local hum = char:WaitForChild("Humanoid")\n    hum.StateChanged:Connect(function(_, new)\n        if new == Enum.HumanoidStateType.Jumping then\n            canDouble = true\n        elseif new == Enum.HumanoidStateType.Landed then\n            canDouble = false; hasDoubled = false\n        end\n    end)\nend)\nUIS.JumpRequest:Connect(function()\n    if canDouble and not hasDoubled then\n        hasDoubled = true\n        player.Character.Humanoid:ChangeState(Enum.HumanoidStateType.Jumping)\n    end\nend)',
                "desc": "Double jump system"
            },
        ]
    },
    "rare": {
        "chance":
        10,
        "color":
        0x3498DB,
        "emoji":
        "🟦",
        "snippets": [{
            "name": "Music Color Sync",
            "code":
            'local sound = workspace.Sound\nlocal part = script.Parent\nlocal RS = game:GetService("RunService")\nRS.Heartbeat:Connect(function()\n    local loud = sound.PlaybackLoudness / 500\n    part.Color = Color3.fromHSV(loud, 1, 1)\n    part.Size = Vector3.new(4 + loud * 3, 4 + loud * 3, 4 + loud * 3)\nend)',
            "desc": "Part reacts to music beat"
        }, {
            "name": "Teleport Pad",
            "code":
            'local padA = workspace.PadA\nlocal padB = workspace.PadB\nlocal db = {}\npadA.Touched:Connect(function(hit)\n    local hum = hit.Parent:FindFirstChild("Humanoid")\n    local hrp = hit.Parent:FindFirstChild("HumanoidRootPart")\n    if hum and hrp and not db[hum] then\n        db[hum] = true\n        hrp.CFrame = padB.CFrame + Vector3.new(0, 5, 0)\n        task.wait(2)\n        db[hum] = nil\n    end\nend)',
            "desc": "Two-way teleport pads"
        }, {
            "name": "NPC Dialog",
            "code":
            'local pp = Instance.new("ProximityPrompt")\npp.Parent = script.Parent\npp.ActionText = "Talk"\nlocal msgs = {"Hello!", "Nice day!", "Watch out!"}\nlocal i = 1\npp.Triggered:Connect(function()\n    game:GetService("Chat"):Chat(script.Parent, msgs[i])\n    i = i % #msgs + 1\nend)',
            "desc": "NPC with rotating dialog"
        }, {
            "name": "Health Regeneration",
            "code":
            'game.Players.PlayerAdded:Connect(function(player)\n    player.CharacterAdded:Connect(function(char)\n        local hum = char:WaitForChild("Humanoid")\n        while true do\n            task.wait(1)\n            if hum.Health < hum.MaxHealth then\n                hum.Health = hum.Health + 5\n            end\n        end\n    end)\nend)',
            "desc": "Auto-health regeneration"
        }, {
            "name": "Click Teleport",
            "code":
            'local cd = Instance.new("ClickDetector", script.Parent)\nlocal dest = workspace.Destination\ncd.MouseClick:Connect(function(player)\n    local char = player.Character\n    if char then\n        char:MoveTo(dest.Position)\n    end\nend)',
            "desc": "Click to teleport to destination"
        }, {
            "name": "DataStore Save/Load",
            "code":
            'local DSS = game:GetService("DataStoreService")\nlocal ds = DSS:GetDataStore("PlayerData")\ngame.Players.PlayerAdded:Connect(function(player)\n    local ls = Instance.new("Folder")\n    ls.Name = "leaderstats"; ls.Parent = player\n    local coins = Instance.new("IntValue")\n    coins.Name = "Coins"; coins.Parent = ls\n    local ok, data = pcall(function()\n        return ds:GetAsync("coins_" .. player.UserId)\n    end)\n    if ok and data then coins.Value = data end\nend)\ngame.Players.PlayerRemoving:Connect(function(player)\n    pcall(function()\n        ds:SetAsync("coins_" .. player.UserId, player.leaderstats.Coins.Value)\n    end)\nend)',
            "desc": "Basic DataStore saving system"
        }, {
            "name": "Tween Door System",
            "code":
            'local ts = game:GetService("TweenService")\nlocal door = script.Parent\nlocal hinge = door.CFrame\nlocal open = false\nlocal info = TweenInfo.new(0.8, Enum.EasingStyle.Back)\nlocal prompt = Instance.new("ProximityPrompt", door)\nprompt.ActionText = "Open Door"\nprompt.Triggered:Connect(function()\n    open = not open\n    local goal = open and {CFrame = hinge * CFrame.Angles(0, math.rad(90), 0)} or {CFrame = hinge}\n    ts:Create(door, info, goal):Play()\n    prompt.ActionText = open and "Close Door" or "Open Door"\nend)',
            "desc": "Smooth rotating door with tween"
        }, {
            "name": "Floating Damage Numbers",
            "code":
            'local function showDamage(part, amount)\n    local bg = Instance.new("BillboardGui")\n    bg.Size = UDim2.new(2, 0, 1, 0)\n    bg.StudsOffset = Vector3.new(0, 3, 0)\n    bg.Adornee = part\n    bg.Parent = part\n    local label = Instance.new("TextLabel", bg)\n    label.Size = UDim2.new(1, 0, 1, 0)\n    label.BackgroundTransparency = 1\n    label.Text = "-" .. amount\n    label.TextColor3 = Color3.new(1, 0, 0)\n    label.TextScaled = true\n    label.Font = Enum.Font.GothamBold\n    local ts = game:GetService("TweenService")\n    ts:Create(bg, TweenInfo.new(1), {StudsOffset = Vector3.new(0, 6, 0)}):Play()\n    ts:Create(label, TweenInfo.new(1), {TextTransparency = 1}):Play()\n    task.delay(1, function() bg:Destroy() end)\nend',
            "desc": "RPG-style floating damage numbers"
        }, {
            "name": "Inventory System",
            "code":
            'local Inventory = {}\nfunction Inventory.new(player)\n    local self = {items = {}, maxSlots = 20, player = player}\n    function self:addItem(name, qty)\n        if #self.items >= self.maxSlots then return false end\n        self.items[name] = (self.items[name] or 0) + (qty or 1)\n        return true\n    end\n    function self:removeItem(name, qty)\n        if not self.items[name] then return false end\n        self.items[name] = self.items[name] - (qty or 1)\n        if self.items[name] <= 0 then self.items[name] = nil end\n        return true\n    end\n    function self:hasItem(name)\n        return (self.items[name] or 0) > 0\n    end\n    return self\nend\nreturn Inventory',
            "desc": "Basic inventory module"
        }, {
            "name": "Round System",
            "code":
            'local Players = game:GetService("Players")\nlocal ROUND_TIME = 60\nlocal INTERMISSION = 15\nwhile true do\n    -- Intermission\n    for i = INTERMISSION, 0, -1 do\n        print("Intermission: " .. i .. "s")\n        task.wait(1)\n    end\n    -- Get players\n    local alive = Players:GetPlayers()\n    print("Round started with " .. #alive .. " players!")\n    -- Round countdown\n    for i = ROUND_TIME, 0, -1 do\n        print("Round: " .. i .. "s remaining")\n        task.wait(1)\n    end\n    print("Round over!")\nend',
            "desc": "Basic round/intermission loop"
        }, {
            "name": "Custom Particle Burst",
            "code":
            'local function burst(position)\n    local att = Instance.new("Attachment")\n    att.Position = position\n    att.Parent = workspace.Terrain\n    local pe = Instance.new("ParticleEmitter")\n    pe.Rate = 0\n    pe.Speed = NumberRange.new(10, 25)\n    pe.Lifetime = NumberRange.new(0.5, 1)\n    pe.SpreadAngle = Vector2.new(360, 360)\n    pe.Color = ColorSequence.new(Color3.fromRGB(255, 200, 0), Color3.fromRGB(255, 50, 0))\n    pe.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0)})\n    pe.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1)})\n    pe.Parent = att\n    pe:Emit(50)\n    task.delay(2, function() att:Destroy() end)\nend',
            "desc": "Explosion-like particle burst effect"
        }, {
            "name": "Waypoint NPC",
            "code":
            'local npc = script.Parent\nlocal hum = npc:WaitForChild("Humanoid")\nlocal waypoints = workspace.Waypoints:GetChildren()\ntable.sort(waypoints, function(a,b) return a.Name < b.Name end)\nwhile true do\n    for _, wp in ipairs(waypoints) do\n        hum:MoveTo(wp.Position)\n        hum.MoveToFinished:Wait()\n        task.wait(1)\n    end\nend',
            "desc": "NPC that walks between waypoints"
        }, {
            "name": "Proximity Prompt GUI",
            "code":
            'local prompt = Instance.new("ProximityPrompt")\nprompt.Parent = script.Parent\nprompt.ActionText = "Open Menu"\nlocal screenGui = script:WaitForChild("ScreenGui"):Clone()\nprompt.Triggered:Connect(function(player)\n    if not player.PlayerGui:FindFirstChild("MenuGui") then\n        screenGui.Parent = player.PlayerGui\n    end\ntask.wait(5)\nscreenGui:Destroy()\nend)',
            "desc": "ProximityPrompt that shows a GUI"
        }]
    },
    "epic": {
        "chance":
        4,
        "color":
        0x9B59B6,
        "emoji":
        "🟪",
        "snippets": [
            {
                "name": "Trail System",
                "code":
                'game.Players.PlayerAdded:Connect(function(p)\n    p.CharacterAdded:Connect(function(c)\n        local t = Instance.new("Trail")\n        local a0 = Instance.new("Attachment", c.Head)\n        local a1 = Instance.new("Attachment", c.HumanoidRootPart)\n        t.Attachment0 = a0\n        t.Attachment1 = a1\n        t.Lifetime = 0.5\n        t.Color = ColorSequence.new(Color3.fromRGB(255,0,255), Color3.fromRGB(0,255,255))\n        t.Transparency = NumberSequence.new(0, 1)\n        t.Parent = c\n    end)\nend)',
                "desc": "Auto trail for all players"
            },
            {
                "name": "Day/Night Cycle",
                "code":
                'local L = game:GetService("Lighting")\nwhile true do\n    L.ClockTime = L.ClockTime + 0.01\n    if L.ClockTime >= 24 then L.ClockTime = 0 end\n    L.Brightness = (L.ClockTime > 6 and L.ClockTime < 18) and 2 or 0.5\n    task.wait(0.1)\nend',
                "desc": "Smooth day/night cycle"
            },
            {
                "name": "Tycoon Dropper",
                "code":
                'local dropper = script.Parent\nlocal spawnPart = dropper:WaitForChild("SpawnPart")\nlocal value = dropper:GetAttribute("Value") or 1\nwhile true do\n    local drop = Instance.new("Part")\n    drop.Size = Vector3.new(1, 1, 1)\n    drop.Color = Color3.fromRGB(255, 215, 0)\n    drop.Material = Enum.Material.Neon\n    drop.CFrame = spawnPart.CFrame\n    drop.Parent = workspace\n    drop:SetAttribute("CoinValue", value)\n    game.Debris:AddItem(drop, 15)\n    task.wait(2)\nend',
                "desc": "Tycoon-style dropper system"
            },
            {
                "name": "Dash Ability",
                "code":
                'local UIS = game:GetService("UserInputService")\nlocal player = game.Players.LocalPlayer\nlocal cooldown = false\nUIS.InputBegan:Connect(function(input, gpe)\n    if gpe then return end\n    if input.KeyCode == Enum.KeyCode.Q and not cooldown then\n        cooldown = true\n        local char = player.Character\n        local hrp = char and char:FindFirstChild("HumanoidRootPart")\n        if hrp then\n            local bv = Instance.new("BodyVelocity")\n            bv.MaxForce = Vector3.new(1e5, 0, 1e5)\n            bv.Velocity = hrp.CFrame.LookVector * 120\n            bv.Parent = hrp\n            game.Debris:AddItem(bv, 0.2)\n            -- Trail effect\n            local trail = Instance.new("Trail")\n            local a0 = Instance.new("Attachment", hrp)\n            local a1 = Instance.new("Attachment", hrp)\n            a1.Position = Vector3.new(0, -2, 0)\n            trail.Attachment0 = a0; trail.Attachment1 = a1\n            trail.Lifetime = 0.3\n            trail.Color = ColorSequence.new(Color3.new(0, 1, 1))\n            trail.Transparency = NumberSequence.new(0, 1)\n            trail.Parent = hrp\n            game.Debris:AddItem(trail, 0.5)\n            game.Debris:AddItem(a0, 0.5)\n            game.Debris:AddItem(a1, 0.5)\n        end\n        task.wait(3)\n        cooldown = false\n    end\nend)',
                "desc": "Press Q to dash forward with trail effect"
            },
            {
                "name": "Zone Detection",
                "code":
                'local RunService = game:GetService("RunService")\nlocal Players = game:GetService("Players")\nlocal zone = workspace:WaitForChild("SafeZone")\nlocal inZone = {}\nRunService.Heartbeat:Connect(function()\n    for _, player in ipairs(Players:GetPlayers()) do\n        local char = player.Character\n        local hrp = char and char:FindFirstChild("HumanoidRootPart")\n        if hrp then\n            local pos = hrp.Position\n            local zPos = zone.Position\n            local zSize = zone.Size / 2\n            local inside = math.abs(pos.X - zPos.X) <= zSize.X\n                and math.abs(pos.Y - zPos.Y) <= zSize.Y\n                and math.abs(pos.Z - zPos.Z) <= zSize.Z\n            if inside and not inZone[player] then\n                inZone[player] = true\n                print(player.Name .. " entered safe zone")\n            elseif not inside and inZone[player] then\n                inZone[player] = nil\n                print(player.Name .. " left safe zone")\n            end\n        end\n    end\nend)',
                "desc": "Detects when players enter/leave a zone"
            },
            {
                "name": "Weapon Swing System",
                "code":
                'local tool = script.Parent\nlocal player = game.Players.LocalPlayer\nlocal cooldown = false\nlocal anims = {\n    tool:WaitForChild("Swing1"),\n    tool:WaitForChild("Swing2"),\n    tool:WaitForChild("Swing3"),\n}\nlocal combo = 1\nlocal lastSwing = 0\ntool.Activated:Connect(function()\n    if cooldown then return end\n    cooldown = true\n    if tick() - lastSwing > 1.5 then combo = 1 end\n    local char = player.Character\n    local hum = char and char:FindFirstChild("Humanoid")\n    if hum then\n        local track = hum:LoadAnimation(anims[combo])\n        track:Play()\n        combo = combo % #anims + 1\n        lastSwing = tick()\n    end\n    task.wait(0.4)\n    cooldown = false\nend)',
                "desc": "Combo melee weapon with 3-hit chain"
            },
            {
                "name": "Custom Chat Commands",
                "code":
                'local Players = game:GetService("Players")\nlocal admins = {123456789} -- Replace with your UserId\nPlayers.PlayerAdded:Connect(function(player)\n    player.Chatted:Connect(function(msg)\n        local lower = msg:lower()\n        if not table.find(admins, player.UserId) then return end\n        if lower == "/day" then\n            game.Lighting.ClockTime = 12\n        elseif lower == "/night" then\n            game.Lighting.ClockTime = 0\n        elseif lower:sub(1, 6) == "/speed" then\n            local spd = tonumber(lower:sub(7))\n            if spd and player.Character then\n                player.Character.Humanoid.WalkSpeed = spd\n            end\n        elseif lower == "/heal" then\n            if player.Character then\n                player.Character.Humanoid.Health = player.Character.Humanoid.MaxHealth\n            end\n        elseif lower == "/reset" then\n            if player.Character then\n                player.Character.Humanoid.Health = 0\n            end\n        end\n    end)\nend)',
                "desc": "Admin chat command system"
            },
            {
                "name": "Obby Checkpoint System",
                "code":
                'local Players = game:GetService("Players")\nlocal checkpoints = workspace.Checkpoints:GetChildren()\ntable.sort(checkpoints, function(a,b) return tonumber(a.Name) < tonumber(b.Name) end)\n\nPlayers.PlayerAdded:Connect(function(player)\n    local stage = Instance.new("IntValue")\n    stage.Name = "Stage"\n    stage.Value = 1\n    stage.Parent = player\n    \n    player.CharacterAdded:Connect(function(char)\n        task.wait(0.5)\n        local cp = checkpoints[stage.Value]\n        if cp then\n            char:WaitForChild("HumanoidRootPart").CFrame = cp.CFrame + Vector3.new(0, 3, 0)\n        end\n    end)\nend)\n\nfor i, cp in ipairs(checkpoints) do\n    cp.Touched:Connect(function(hit)\n        local player = Players:GetPlayerFromCharacter(hit.Parent)\n        if player and player.Stage.Value == i - 1 then\n            player.Stage.Value = i\n            print(player.Name .. " reached stage " .. i)\n        end\n    end)\nend',
                "desc": "Full obby checkpoint/stage system"
            },
            {
                "name": "Custom GUI HUD",
                "code":
                'local player = game.Players.LocalPlayer\nlocal gui = Instance.new("ScreenGui")\ngui.Name = "HUD"\ngui.Parent = player.PlayerGui\n\nlocal healthBar = Instance.new("Frame")\nhealthBar.Name = "HealthBar"\nhealthBar.Size = UDim2.new(0.2, 0, 0.03, 0) -- 20% width, 3% height\nhealthBar.Position = UDim2.new(0.4, 0, 0.9, 0)  -- Centered at bottom \nhealthBar.BackgroundColor3 = Color3.new(0.8, 0, 0)\nhealthBar.BorderSizePixel = 0\nhealthBar.Parent = gui\n\nlocal healthFill = Instance.new("Frame") -- Inner fill\nhealthFill.Name = "HealthFill"\nhealthFill.Size = UDim2.new(1, 0, 1, 0) -- Full width\nhealthFill.BackgroundColor3 = Color3.new(0, 0.8, 0)\nhealthFill.BorderSizePixel = 0\nhealthFill.Parent = healthBar\n\nlocal function updateHealth() \n    local char = player.Character\n    if char then\n        local hum = char:FindFirstChild("Humanoid")\n        if hum then\n            healthFill.Size = UDim2.new(hum.Health / hum.MaxHealth, 0, 1, 0)\n        end\n    end\nend\n\nplayer.CharacterAdded:Connect(function(char)\n    char:WaitForChild("Humanoid").HealthChanged:Connect(updateHealth)\n    updateHealth()\nend)',
                "desc": "Custom health bar HUD"
            },
        ]
    },
    "legendary": {
        "chance":
        1,
        "color":
        0xF1C40F,
        "emoji":
        "🌟",
        "snippets": [
            {
                "name": "Horror Camera Shake",
                "code":
                'local cam = workspace.CurrentCamera\nlocal RS = game:GetService("RunService")\nlocal shaking, intensity = false, 0\nlocal function shake(power, dur)\n    shaking = true; intensity = power\n    task.delay(dur, function() shaking = false; intensity = 0 end)\nend\nRS.RenderStepped:Connect(function()\n    if shaking then\n        cam.CFrame = cam.CFrame * CFrame.new(\n            math.random()*intensity - intensity/2,\n            math.random()*intensity - intensity/2,\n            math.random()*intensity - intensity/2\n        )\n    end\nend)\n-- shake(2, 3) to use',
                "desc": "Professional horror camera shake"
            },
            {
                "name": "Grid Placement System",
                "code":
                'local UIS = game:GetService("UserInputService")\nlocal RS = game:GetService("RunService")\nlocal player = game.Players.LocalPlayer\nlocal mouse = player:GetMouse()\nlocal GRID = 2\nlocal placing, preview = false, nil\nlocal function snap(p)\n    return Vector3.new(math.round(p.X/GRID)*GRID, p.Y, math.round(p.Z/GRID)*GRID)\nend\nRS.RenderStepped:Connect(function()\n    if placing and preview then\n        preview:SetPrimaryPartCFrame(CFrame.new(snap(mouse.Hit.Position)))\n    end\nend)\nUIS.InputBegan:Connect(function(i)\n    if i.UserInputType == Enum.UserInputType.MouseButton1 and placing then\n        local f = preview:Clone()\n        for _,p in ipairs(f:GetDescendants()) do\n            if p:IsA("BasePart") then p.Transparency = 0; p.CanCollide = true end\n        end\n        f.Parent = workspace\n        preview:Destroy(); placing = false\n    end\nend)',
                "desc": "Grid placement system like Bloxburg"
            },
            {
                "name": "Custom Physics Engine",
                "code":
                'local RunService = game:GetService("RunService")\nlocal parts = workspace:GetDescendants()\nlocal function applyPhysics(dt)\n    for _, part in ipairs(parts) do\n        if part:IsA("BasePart") and not part.Anchored then\n            local vel = part.Velocity\n            vel = vel + Vector3.new(0, -196.2 * dt, 0) -- Gravity\n            part.Velocity = vel\n            part.CFrame = part.CFrame + vel * dto\n        end\n    end\nend\nRunService.Heartbeat:Connect(applyPhysics)',
                "desc": "Basic physics engine simulation"
            },
            {
                "name": "Pet Follow System",
                "code":
                'local function createPet(player)\n    local char = player.Character\n    if not char then return end\n    local hrp = char:WaitForChild("HumanoidRootPart")\n    local pet = Instance.new("Part")\n    pet.Size = Vector3.new(2, 2, 2)\n    pet.Shape = Enum.PartType.Ball\n    pet.Color = Color3.fromRGB(255, 255, 0)\n    pet.Material = Enum.Material.Neon\n    pet.CanCollide = false\n    pet.Anchored = true\n    pet.Name = player.Name .. "_Pet"\n    pet.Parent = workspace\n    \n    local offset = Vector3.new(3, 2, -2)\n    local angle = 0\n    \n    game:GetService("RunService").Heartbeat:Connect(function(dt)\n        if not hrp.Parent then pet:Destroy() return end\n        angle = angle + dt * 2\n        local bob = math.sin(angle) * 0.5\n        local orbit = CFrame.new(hrp.Position) * CFrame.Angles(0, angle * 0.5, 0) * CFrame.new(offset)\n        local target = orbit.Position + Vector3.new(0, bob, 0)\n        pet.Position = pet.Position:Lerp(target, 0.1)\n        -- Sparkle effect\n        if not pet:FindFirstChild("Sparkles") then\n            local s = Instance.new("Sparkles", pet)\n            s.SparkleColor = Color3.fromRGB(255, 255, 100)\n        end\n    end)\nend\ngame.Players.PlayerAdded:Connect(function(p)\n    p.CharacterAdded:Connect(function() task.wait(1); createPet(p) end)\nend)',
                "desc":
                "Orbiting pet that follows player with bobbing animation"
            },
            {
                "name": "Ability Cooldown UI System",
                "code":
                'local UIS = game:GetService("UserInputService")\nlocal TS = game:GetService("TweenService")\nlocal player = game.Players.LocalPlayer\nlocal gui = player.PlayerGui:WaitForChild("AbilityGui")\n\nlocal abilities = {\n    {key = Enum.KeyCode.Z, name = "Fireball", cooldown = 5, color = Color3.new(1,0.3,0)},\n    {key = Enum.KeyCode.X, name = "Shield", cooldown = 8, color = Color3.new(0,0.5,1)},\n    {key = Enum.KeyCode.C, name = "Heal", cooldown = 12, color = Color3.new(0,1,0.3)},\n    {key = Enum.KeyCode.V, name = "Ultimate", cooldown = 30, color = Color3.new(1,0,1)},\n}\n\nlocal onCooldown = {}\nfor i, ab in ipairs(abilities) do\n    local frame = gui:FindFirstChild(ab.name)\n    if not frame then continue end\n    local overlay = frame:FindFirstChild("CooldownOverlay")\n    local label = frame:FindFirstChild("TimeLabel")\nend\n\nUIS.InputBegan:Connect(function(input, gpe)\n    if gpe then return end\n    for _, ab in ipairs(abilities) do\n        if input.KeyCode == ab.key and not onCooldown[ab.name] then\n            onCooldown[ab.name] = true\n            print(ab.name .. " activated!")\n            local frame = gui:FindFirstChild(ab.name)\n            if frame then\n                local overlay = frame.CooldownOverlay\n                overlay.Size = UDim2.new(1, 0, 1, 0)\n                local tween = TS:Create(overlay, TweenInfo.new(ab.cooldown, Enum.EasingStyle.Linear), {Size = UDim2.new(1, 0, 0, 0)})\n                tween:Play()\n                task.delay(ab.cooldown, function()\n                    onCooldown[ab.name] = false\n                end)\n            end\n        end\n    end\nend)',
                "desc": "Full ability cooldown system with UI overlay"
            },
            {
                "name": "Procedural Terrain Generator",
                "code":
                'local Terrain = workspace.Terrain\nlocal SEED = math.random(1, 999999)\nlocal SIZE = 200\nlocal RESOLUTION = 4\nlocal HEIGHT = 50\nlocal WATER_LEVEL = 10\n\nlocal function noise(x, z)\n    local n = math.noise(x / 80 + SEED, z / 80 + SEED) * HEIGHT\n    n = n + math.noise(x / 30 + SEED, z / 30 + SEED) * (HEIGHT * 0.3)\n    n = n + math.noise(x / 10 + SEED, z / 10 + SEED) * (HEIGHT * 0.1)\n    return n\nend\n\nlocal function getMaterial(height)\n    if height < WATER_LEVEL then return Enum.Material.Water end\n    if height < WATER_LEVEL + 3 then return Enum.Material.Sand end\n    if height < HEIGHT * 0.5 then return Enum.Material.Grass end\n    if height < HEIGHT * 0.75 then return Enum.Material.Rock end\n    return Enum.Material.Snow\nend\n\nfor x = -SIZE, SIZE, RESOLUTION do\n    for z = -SIZE, SIZE, RESOLUTION do\n        local h = noise(x, z)\n        local mat = getMaterial(h)\n        local region = Region3.new(\n            Vector3.new(x, -20, z),\n            Vector3.new(x + RESOLUTION, h, z + RESOLUTION)\n        ):ExpandToGrid(RESOLUTION)\n        Terrain:FillRegion(region, RESOLUTION, mat)\n    end\n    if x % 20 == 0 then task.wait() end\nend\nprint("Terrain generated with seed: " .. SEED)',
                "desc": "Procedural terrain with biomes using Perlin noise"
            },
            {
                "name":
                "Full Save System Module",
                "code":
                'local SaveSystem = {}\nlocal DSS = game:GetService("DataStoreService")\nlocal ds = DSS:GetDataStore("PlayerSaveV1")\n\nlocal template = {\n    Coins = 0,\n    Gems = 0,\n    Level = 1,\n    XP = 0,\n    Inventory = {},\n    Settings = {Music = true, SFX = true},\n}\n\nfunction SaveSystem:Load(player)\n    local key = "user_" .. player.UserId\n    local ok, data = pcall(function() return ds:GetAsync(key) end)\n    if ok and data then\n        for k, v in pairs(template) do\n            if data[k] == nil then data[k] = v end\n        end\n        return data\n    else\n        warn("Load failed for " .. player.Name .. ", using template")\n        return table.clone(template)\n    end\nend\n\nfunction SaveSystem:Save(player, data)\n    local key = "user_" .. player.UserId\n    local ok, err = pcall(function()\n        ds:UpdateAsync(key, function(old)\n            return data\n        end)\n    end)\n    if not ok then\n        warn("Save failed for " .. player.Name .. ": " .. err)\n    end\n    return ok\nend\n\nfunction SaveSystem:AutoSave(player, data, interval)\n    task.spawn(function()\n        while player.Parent do\n            task.wait(interval or 120)\n            self:Save(player, data)\n        end\n    end)\nend\n\nreturn SaveSystem',
                "desc":
                "Production-ready DataStore save system with template and auto-save"
            },
            {
                "name":
                "Advanced NPC Combat AI",
                "code":
                'local npc = script.Parent\nlocal hum = npc:WaitForChild("Humanoid")\nlocal hrp = npc:WaitForChild("HumanoidRootPart")\nlocal PS = game:GetService("PathfindingService")\nlocal RANGE_DETECT = 60\nlocal RANGE_ATTACK = 5\nlocal DAMAGE = 20\nlocal ATTACK_CD = 1.5\n\nlocal state = "idle"\nlocal target = nil\nlocal lastAttack = 0\n\nlocal function findTarget()\n    local closest, dist = nil, RANGE_DETECT\n    for _, p in ipairs(game.Players:GetPlayers()) do\n        local c = p.Character\n        local h = c and c:FindFirstChild("Humanoid")\n        local r = c and c:FindFirstChild("HumanoidRootPart")\n        if h and h.Health > 0 and r then\n            local d = (r.Position - hrp.Position).Magnitude\n            if d < dist then closest = c; dist = d end\n        end\n    end\n    return closest\nend\n\nlocal function pathTo(pos)\n    local path = PS:CreatePath({AgentRadius = 2, AgentHeight = 5, AgentCanJump = true})\n    local ok, err = pcall(function() path:ComputeAsync(hrp.Position, pos) end)\n    if ok and path.Status == Enum.PathStatus.Success then\n        for _, wp in ipairs(path:GetWaypoints()) do\n            if wp.Action == Enum.PathWaypointAction.Jump then hum.Jump = true end\n            hum:MoveTo(wp.Position)\n            local reached = hum.MoveToFinished:Wait()\n            if not reached then break end\n            if target and (target:FindFirstChild("HumanoidRootPart").Position - hrp.Position).Magnitude < RANGE_ATTACK then break end\n        end\n    end\nend\n\ngame:GetService("RunService").Heartbeat:Connect(function()\n    target = findTarget()\n    if not target then state = "idle"; return end\n    local tHRP = target:FindFirstChild("HumanoidRootPart")\n    if not tHRP then return end\n    local dist = (tHRP.Position - hrp.Position).Magnitude\n    if dist <= RANGE_ATTACK then\n        state = "attacking"\n        hrp.CFrame = CFrame.lookAt(hrp.Position, Vector3.new(tHRP.Position.X, hrp.Position.Y, tHRP.Position.Z))\n        if tick() - lastAttack >= ATTACK_CD then\n            lastAttack = tick()\n            target:FindFirstChild("Humanoid"):TakeDamage(DAMAGE)\n        end\n    else\n        state = "chasing"\n    end\nend)\n\nwhile true do\n    if state == "chasing" and target then\n        local tHRP = target:FindFirstChild("HumanoidRootPart")\n        if tHRP then pathTo(tHRP.Position) end\n    elseif state == "idle" then\n        task.wait(1)\n    end\n    task.wait(0.2)\nend',
                "desc":
                "Full NPC enemy AI with pathfinding, targeting, and melee attacks"
            },
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
    return "common", SNIPPET_BOXES["common"], random.choice(
        SNIPPET_BOXES["common"]["snippets"])


# ==================== DUEL VIEW ====================
class DuelAcceptView(discord.ui.View):

    def __init__(self, challenger_id: int, opponent_id: int, bet: int):
        super().__init__(timeout=30)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.bet = bet
        self.accepted = False

    @discord.ui.button(label="Accept Duel",
                       emoji="⚔️",
                       style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message(
                "❌ This duel isn't for you!", ephemeral=True)
            return
        self.accepted = True
        button.disabled = True
        self.children[1].disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Decline",
                       emoji="❌",
                       style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message(
                "❌ This duel isn't for you!", ephemeral=True)
            return
        self.accepted = False
        button.disabled = True
        self.children[0].disabled = True
        await interaction.response.edit_message(embed=discord.Embed(
            title="⚔️ Duel Declined",
            description=f"{interaction.user.display_name} declined the duel.",
            color=0x95A5A6),
                                                view=self)
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
                custom_id=f"duel_{i}_{random.randint(10000, 99999)}")
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index):

        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid != self.challenger_id and uid != self.opponent_id:
                await interaction.response.send_message("❌ Not your duel!",
                                                        ephemeral=True)
                return
            if uid in self.answers:
                await interaction.response.send_message("❌ Already answered!",
                                                        ephemeral=True)
                return

            self.answers[uid] = {
                "choice": index,
                "correct": index == self.correct,
                "time": interaction.created_at.timestamp()
            }
            await interaction.response.send_message("✅ Answer locked!",
                                                    ephemeral=True)

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
    async def claim(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        if interaction.user.id == self.creator_id:
            await interaction.response.send_message(
                "❌ Can't claim your own bounty!", ephemeral=True)
            return
        if self.claimed_by:
            await interaction.response.send_message("❌ Already claimed!",
                                                    ephemeral=True)
            return

        self.claimed_by = interaction.user.id
        await UserProfile.add_credits(interaction.user.id, self.reward)

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="🎯 Bounty Claimed!",
            description=(
                f"**{interaction.user.display_name}** claimed this bounty!\n"
                f"💰 **{self.reward} Credits** awarded!"),
            color=0x2ECC71)
        embed.add_field(name="Claimer",
                        value=interaction.user.mention,
                        inline=True)
        embed.add_field(name="Reward", value=f"💰 {self.reward}", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                "❌ Only the creator can cancel!", ephemeral=True)
            return
        if self.claimed_by:
            await interaction.response.send_message(
                "❌ Already claimed, can't cancel!", ephemeral=True)
            return

        await UserProfile.add_credits(self.creator_id, self.reward)

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="❌ Bounty Cancelled",
            description=
            f"**{self.reward} Credits** refunded to {interaction.user.mention}.",
            color=0xE74C3C)
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
                row=row)
            btn.callback = self._make_callback(key)
            self.add_item(btn)

    def _make_callback(self, category_key):

        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not your trivia!",
                                                        ephemeral=True)
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
                row=i // 2)
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index):

        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Not your trivia!",
                                                        ephemeral=True)
                return
            if self.answered:
                await interaction.response.send_message("❌ Already answered!",
                                                        ephemeral=True)
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
                    child.label = f"✖️ {labels[j]}. {self.question['options'][j][:55]}"
                else:
                    child.style = discord.ButtonStyle.secondary

            await interaction.response.edit_message(view=self)
            self.stop()

        return callback


class TriviaStreakView(discord.ui.View):

    def __init__(self, user_id: int, streak: int, category: str,
                 difficulty: str):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.streak = streak
        self.category = category
        self.difficulty = difficulty
        self.continue_playing = None

    async def interaction_check(self,
                                interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your trivia!",
                                                    ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Next Question!",
                       emoji="▶️",
                       style=discord.ButtonStyle.success)
    async def next_question(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        self.continue_playing = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cash Out",
                       emoji="💰",
                       style=discord.ButtonStyle.secondary)
    async def cash_out(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        self.continue_playing = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Harder!",
                       emoji="🔥",
                       style=discord.ButtonStyle.danger)
    async def go_harder(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        self.continue_playing = True
        diff_order = ["easy", "medium", "hard", "expert", "demon"]
        current_idx = diff_order.index(
            self.difficulty) if self.difficulty in diff_order else 1
        if current_idx < len(diff_order) - 1:
            self.difficulty = diff_order[current_idx + 1]
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


# ==================== UNBOX ANIMATION ====================
UNBOX_FRAMES_old = [
    # Frame 1 - Boot up
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Booting system...             ║\n"
    "║  > Loading modules...            ║\n"
    "║  > [░░░░░░░░░░░░░░░░░░░░]  0%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ INITIALIZING         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Booting complete           ║\n"
    "║  > Loading modules...            ║\n"
    "║  > [░░░░░░░░░░░░░░░░░░░░]  0%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ INITIALIZING         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Booting complele              ║\n"
    "║  > found ? Modules               ║\n"
    "║  > [░░░░░░░░░░░░░░░░░░░░]  0%    ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ INITIALIZING         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Connecting to server A421...  ║\n"
    "║  > Breaking the security codes   ║\n"
    "║  > [█░░░░░░░░░░░░░░░░░░░]  5%    ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ INITIALIZING         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 2 - Connecting
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault...        ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault..         ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault.         ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault..         ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault...        ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connecting to vault..         ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [███░░░░░░░░░░░░░░░░░] 10%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connected to the vault        ║\n"
    "║  > Authenticating user...        ║\n"
    "║  > [█████░░░░░░░░░░░░░░░] 20%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connected to the vault        ║\n"
    "║  > Authenticating user..         ║\n"
    "║  > [█████░░░░░░░░░░░░░░░] 20%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > System online                 ║\n"
    "║  > Connected to the vault        ║\n"
    "║  > Authenticating user.          ║\n"
    "║  > [█████░░░░░░░░░░░░░░░] 20%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 3 - Scanning
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Access GRANTED ✔              ║\n"
    "║  > Scanning code database...     ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > [██████████░░░░░░░░░░] 35%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Access GRANTED ✔              ║\n"
    "║  > Scanning code database..      ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > [██████████░░░░░░░░░░] 35%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Access GRANTED ✔              ║\n"
    "║  > Scanning code database.       ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > [██████████░░░░░░░░░░] 35%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Access GRANTED ✔              ║\n"
    "║  > Scanning code database..      ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > [██████████░░░░░░░░░░] 35%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Access GRANTED ✔              ║\n"
    "║  > Scanning code database...     ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > [██████████░░░░░░░░░░] 35%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 4 - Found snippet
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [██████░░░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [███████░░░] ???     ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [████████░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [█████████░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [████████░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [██████░░░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [█████░░░░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > snippet_0x3F located!         ║\n"
    "║  > Analyzing rarity signature... ║\n"
    "║  > Rarity: [████░░░░░░] ???      ║\n"
    "║  > [██████████████░░░░░░] 55%    ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 5 - Decrypting
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Decryption in progress...     ║\n"
    "║  > Key: A7-X9-Q2-██-██          ║\n"
    "║  > Bypassing firewall layer 3... ║\n"
    "║  > [████████████████░░░░] 80%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔐 DECRYPTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 6 - Almost there
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Firewall BYPASSED ✔           ║\n"
    "║  > Key: A7-X9-Q2-F4-Z1 ✔        ║\n"
    "║  > Rarity LOCKED IN ✔            ║\n"
    "║  > [██████████████████░░] 95%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⚡ EXTRACTING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 7 - Complete
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > ████████████████████████████  ║\n"
    "║  > [████████████████████] 100%  ║\n"
    "║  > ████████████████████████████  ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔓 DECRYPTED            ║\n"
    "╚═══════════════════════"

    # Frame 8 - Reveal
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║    💥 CODE EXTRACTED 💥           ║\n"
    "║                                  ║\n"
    "║    ✅ DECRYPTION COMPLETE         ║\n"
    "║    📄 SNIPPET READY              ║\n"
    "║    🎁 DISPLAYING BELOW...        ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```\n",
]
UNBOX_FRAMES = [
    # Frame 1 - Power on
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║          POWERING ON.            ║\n"
    "║              ⚡                  ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 2 - Power on dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║          POWERING ON..           ║\n"
    "║              ⚡⚡                ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 3 - Power on dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║          POWERING ON...          ║\n"
    "║             ⚡⚡⚡               ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 4 - Boot sequence
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Booting system.               ║\n"
    "║  > Checking memory.              ║\n"
    "║  > [░░░░░░░░░░░░░░░░░░░░]  0%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ BOOTING              ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 5 - Boot dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Booting system..              ║\n"
    "║  > Checking memory.. OK          ║\n"
    "║  > [██░░░░░░░░░░░░░░░░░░]  5%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⏳ BOOTING              ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 6 - Loading modules
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Loading core modules...       ║\n"
    "║  > crypto.lua ........... ✔      ║\n"
    "║  > vault_api.lua ........ ✔      ║\n"
    "║  > rarity_engine.lua .           ║\n"
    "║  > [████░░░░░░░░░░░░░░░░] 12%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📂 LOADING              ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 7 - Loading more
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Loading core modules...       ║\n"
    "║  > crypto.lua ........... ✔      ║\n"
    "║  > vault_api.lua ........ ✔      ║\n"
    "║  > rarity_engine.lua ..          ║\n"
    "║  > [█████░░░░░░░░░░░░░░░] 15%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📂 LOADING              ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 8 - Modules done
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Loading core modules...       ║\n"
    "║  > crypto.lua ........... ✔      ║\n"
    "║  > vault_api.lua ........ ✔      ║\n"
    "║  > rarity_engine.lua ... ✔       ║\n"
    "║  > firewall.lua ........ ✔       ║\n"
    "║  > [██████░░░░░░░░░░░░░░] 20%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ✅ MODULES LOADED       ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 9 - Connecting
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Establishing connection.      ║\n"
    "║  > Pinging vault server.         ║\n"
    "║  > Latency: --ms                 ║\n"
    "║  > [████████░░░░░░░░░░░░] 28%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 10 - Connecting dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Establishing connection..     ║\n"
    "║  > Pinging vault server..        ║\n"
    "║  > Latency: 7ms                  ║\n"
    "║  > [█████████░░░░░░░░░░░] 32%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔌 CONNECTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 11 - Connected + Auth
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Establishing connection... ✔  ║\n"
    "║  > Latency: 12ms                 ║\n"
    "║  > Authenticating user.          ║\n"
    "║  > Token: ██████████████         ║\n"
    "║  > [██████████░░░░░░░░░░] 38%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔑 AUTHENTICATING       ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 12 - Auth dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Establishing connection... ✔  ║\n"
    "║  > Latency: 12ms                 ║\n"
    "║  > Authenticating user..         ║\n"
    "║  > Token: ██████████████         ║\n"
    "║  > [███████████░░░░░░░░░] 40%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔑 AUTHENTICATING       ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 13 - Access granted
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Authenticating user... ✔      ║\n"
    "║  > ✅ ACCESS GRANTED             ║\n"
    "║  > Welcome, Developer.           ║\n"
    "║  > Clearance: LEVEL 5            ║\n"
    "║  > [████████████░░░░░░░░] 45%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ✅ AUTHORIZED           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 14 - Scanning
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Scanning code database.       ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > Searching for match.          ║\n"
    "║  > query: [██░░░░░░░░]           ║\n"
    "║  > [█████████████░░░░░░░] 50%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 15 - Scanning dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Scanning code database..      ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > Searching for match..         ║\n"
    "║  > query: [█████░░░░░]           ║\n"
    "║  > [██████████████░░░░░░] 53%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 16 - Scanning more dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Scanning code database...     ║\n"
    "║  > 1,847 snippets indexed        ║\n"
    "║  > Searching for match...        ║\n"
    "║  > query: [████████░░]           ║\n"
    "║  > [███████████████░░░░░] 56%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔍 SCANNING             ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 17 - Snippet found
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > ⚠️  SNIPPET LOCATED!          ║\n"
    "║  > ID: snippet_0x3F              ║\n"
    "║  > Sector: 7-BRAVO               ║\n"
    "║  > Encrypted: YES                ║\n"
    "║  > [████████████████░░░░] 60%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📡 TARGET FOUND         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 18 - Analyzing rarity
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Analyzing rarity signature.   ║\n"
    "║  > Wavelength: ████░░░░░░        ║\n"
    "║  > Frequency:  ██████░░░░        ║\n"
    "║  > Rarity:     [? ? ? ? ?]       ║\n"
    "║  > [████████████████░░░░] 63%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📊 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 19 - Analyzing dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Analyzing rarity signature..  ║\n"
    "║  > Wavelength: ████████░░        ║\n"
    "║  > Frequency:  ██████████        ║\n"
    "║  > Rarity:     [? ? ? ? ?]       ║\n"
    "║  > [█████████████████░░░] 66%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📊 ANALYZING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 20 - Begin decryption
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Beginning decryption.         ║\n"
    "║  > Cipher: AES-256-VAULT         ║\n"
    "║  > Key: ██-██-██-██-██           ║\n"
    "║  > Layer [1/3] cracking.         ║\n"
    "║  > [█████████████████░░░] 70%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔐 DECRYPTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 21 - Layer 1 cracking
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Beginning decryption..        ║\n"
    "║  > Cipher: AES-256-VAULT         ║\n"
    "║  > Key: A7-██-██-██-██           ║\n"
    "║  > Layer [1/3] cracking..        ║\n"
    "║  > [█████████████████░░░] 72%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔐 DECRYPTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 22 - Layer 1 done
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Layer [1/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-██-██-██           ║\n"
    "║  > Layer [2/3] cracking.         ║\n"
    "║  > Brute forcing combos.         ║\n"
    "║  > [██████████████████░░] 76%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔐 DECRYPTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 23 - Layer 2 cracking
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Layer [1/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-██-██-██           ║\n"
    "║  > Layer [2/3] cracking..        ║\n"
    "║  > Brute forcing combos..        ║\n"
    "║  > [██████████████████░░] 78%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔐 DECRYPTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 24 - Layer 2 done + firewall
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Layer [2/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-Q2-██-██           ║\n"
    "║  > Layer [3/3] cracking...       ║\n"
    "║  > ⚠️  FIREWALL DETECTED!        ║\n"
    "║  > [██████████████████░░] 82%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🛡️ ⚠️ FIREWALL          ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 25 - Bypassing firewall
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Deploying bypass protocol.    ║\n"
    "║  > Injecting payload.            ║\n"
    "║  > Firewall: ▓▓▓▓▓▓▓░░░ 70%    ║\n"
    "║  > Key: A7-X9-Q2-██-██           ║\n"
    "║  > [███████████████████░] 85%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⚔️ BYPASSING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 26 - Bypassing dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Deploying bypass protocol..   ║\n"
    "║  > Injecting payload..           ║\n"
    "║  > Firewall: ▓▓▓░░░░░░░ 30%    ║\n"
    "║  > Key: A7-X9-Q2-F4-██           ║\n"
    "║  > [███████████████████░] 88%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⚔️ BYPASSING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 27 - Bypassing more dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > Deploying bypass protocol...  ║\n"
    "║  > Injecting payload...          ║\n"
    "║  > Firewall: ▓░░░░░░░░░  5%    ║\n"
    "║  > Key: A7-X9-Q2-F4-██           ║\n"
    "║  > [███████████████████░] 90%   ║\n"
    "║                                  ║\n"
    "║  STATUS: ⚔️ ALMOST THERE         ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 28 - Firewall down
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > 🛡️  FIREWALL BYPASSED ✔       ║\n"
    "║  > Layer [3/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-Q2-F4-Z1 ✔        ║\n"
    "║  > Extracting snippet data.      ║\n"
    "║  > [███████████████████░] 93%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📤 EXTRACTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 29 - Extracting dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > 🛡️  FIREWALL BYPASSED ✔       ║\n"
    "║  > Layer [3/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-Q2-F4-Z1 ✔        ║\n"
    "║  > Extracting snippet data..     ║\n"
    "║  > [████████████████████] 96%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📤 EXTRACTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 30 - Extracting more dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > 🛡️  FIREWALL BYPASSED ✔       ║\n"
    "║  > Layer [3/3] cracked ✔         ║\n"
    "║  > Key: A7-X9-Q2-F4-Z1 ✔        ║\n"
    "║  > Extracting snippet data...    ║\n"
    "║  > [████████████████████] 98%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 📤 EXTRACTING           ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 31 - Verification
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > All layers cracked ✔          ║\n"
    "║  > Rarity confirmed ✔            ║\n"
    "║  > Code integrity check.         ║\n"
    "║  > Verifying checksum.           ║\n"
    "║  > [████████████████████] 99%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔎 VERIFYING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 32 - Verification dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > All layers cracked ✔          ║\n"
    "║  > Rarity confirmed ✔            ║\n"
    "║  > Code integrity check.. ✔      ║\n"
    "║  > Verifying checksum.. ✔        ║\n"
    "║  > [████████████████████] 99%   ║\n"
    "║                                  ║\n"
    "║  STATUS: 🔎 VERIFYING            ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 33 - Complete
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║   🖥️  CODE_VAULT v3.7.1         ║\n"
    "╠══════════════════════════════════╣\n"
    "║                                  ║\n"
    "║  > All layers cracked ✔          ║\n"
    "║  > Rarity confirmed ✔            ║\n"
    "║  > Code verified ✔               ║\n"
    "║  > Checksum valid ✔              ║\n"
    "║  > [████████████████████] 100%  ║\n"
    "║                                  ║\n"
    "║  STATUS: ✅ COMPLETE              ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 34 - Preparing reveal
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "║      > Preparing display.        ║\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 35 - Preparing dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "║      > Preparing display..       ║\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 36 - Preparing more dots
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "║      > Preparing display...      ║\n"
    "║                                  ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",

    # Frame 37 - Grand reveal
    "```\n"
    "╔══════════════════════════════════╗\n"
    "║                                  ║\n"
    "║  ██████████████████████████████  ║\n"
    "║  ██                          ██  ║\n"
    "║  ██  💥 CODE EXTRACTED 💥    ██  ║\n"
    "║  ██                          ██  ║\n"
    "║  ██  ✅ DECRYPTION COMPLETE  ██  ║\n"
    "║  ██  📄 SNIPPET READY        ██  ║\n"
    "║  ██  🎁 DISPLAYING BELOW     ██  ║\n"
    "║  ██                          ██  ║\n"
    "║  ██████████████████████████████  ║\n"
    "║                                  ║\n"
    "╚══════════════════════════════════╝\n"
    "```",
]


# ==================== HELPERS ====================
def is_user_admin(interaction: discord.Interaction) -> bool:
    try:
        if interaction.guild and hasattr(interaction.user,
                                         'guild_permissions'):
            return interaction.user.guild_permissions.administrator
    except Exception:
        pass
    return False


async def check_ai_credits(interaction: discord.Interaction,
                           cost: int = 1) -> bool:
    if is_user_admin(interaction):
        return True

    user = await UserProfile.get_user(interaction.user.id)
    if not user:
        await UserProfile.create_user(interaction.user.id,
                                      interaction.user.name)
        user = await UserProfile.get_user(interaction.user.id)

    current_ai = user.get("ai_credits", 0)
    if current_ai < cost:
        embed = discord.Embed(
            title="❌ Not Enough AI Credits",
            description=(f"This command costs **{cost}** AI Credit(s).\n"
                         f"You have **{current_ai}** AI Credits.\n\n"
                         f"**Get more:**\n"
                         f"`/convert` — Studio Credits → pCredits\n"
                         f"`/convert_ai` — pCredits → AI Credits"),
            color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)
        return False

    await UserProfile.update_user(interaction.user.id,
                                  {"ai_credits": current_ai - cost})
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
    @app_commands.command(
        name="ai-roast",
        description="💀 AI roasts a user based on their profile")
    @app_commands.describe(user="The user to roast")
    async def ai_roast(self, interaction: discord.Interaction,
                       user: discord.Member):
        await interaction.response.defer()

        if user.bot:
            await interaction.followup.send(
                "❌ Can't roast a bot... or can I? No, I can't.")
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
            f"5-6 sentences max. Be creative and specific to their stats.\n\n"
            f"TARGET: {user.display_name}\n"
            f"Roles: {roles}\n"
            f"Rank: {profile.get('rank', 'Beginner')} | Level: {profile.get('level', 1)} | XP: {profile.get('xp', 0)}\n"
            f"Credits: {profile.get('studio_credits', 0)} | Messages: {profile.get('message_count', 0)} | Rep: {profile.get('reputation', 0)}\n"
            f"Voice Minutes: {profile.get('voice_minutes', 0)}"
            f"the roast must be very funny make user laugh and cry at the same time. "
        )

        try:
            roast = await call_ai(prompt)
            if roast.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(roast)
                return

            embed = discord.Embed(title=f"💀 AI ROAST — {user.display_name}",
                                  description=roast[:2000],
                                  color=0xE74C3C)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(
                name="Victim's Stats",
                value=
                f"Level {profile.get('level', 1)} | {profile.get('rank', 'Beginner')} | 💰 {profile.get('studio_credits', 0)} Credits",
                inline=False)
            embed.set_footer(
                text=
                f"Roasted by {AI_NAME} • Requested by {interaction.user.display_name} • 1 AI Credit"
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Roast failed: {str(e)[:200]}")

    # ========== 2. DEV BOUNTY ==========
    @app_commands.command(
        name="dev-bounty",
        description="💰 Post a bounty for other devs to claim")
    @app_commands.describe(task="What needs to be done",
                           reward="Credits to offer (100-50000)")
    async def dev_bounty(self, interaction: discord.Interaction, task: str,
                         reward: int):
        await interaction.response.defer()

        if reward < 100 or reward > 50000:
            await interaction.followup.send(
                "❌ Reward must be between **100** and **50,000** Credits!")
            return
        if len(task) < 10 or len(task) > 500:
            await interaction.followup.send("❌ Task must be 10-500 characters!"
                                            )
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id,
                                          interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if current_credits < reward:
            await interaction.followup.send(
                f"❌ Not enough credits! You have **{current_credits}**.")
            return

        await UserProfile.update_user(
            interaction.user.id, {"studio_credits": current_credits - reward})

        bounty_id = f"bounty_{interaction.user.id}_{random.randint(10000, 99999)}"

        embed = discord.Embed(
            title="💰 Dev Bounty Posted!",
            description=
            f"**Task:** {task}\n\n**Reward:** 💰 {reward} Credits\n**Posted by:** {interaction.user.mention}\n**Expires:** 24 hours",
            color=0xF1C40F)
        embed.add_field(name="How to claim",
                        value="Click 🎯 **Claim Bounty** below!",
                        inline=False)
        embed.set_footer(text=f"Bounty ID: {bounty_id}")

        view = BountyClaimView(bounty_id, interaction.user.id, reward)
        await interaction.followup.send(embed=embed, view=view)

    # ========== 3. UNBOX SNIPPET ==========
    @app_commands.command(
        name="unbox-snippet",
        description="📦 Open a random code snippet box (500 Credits)")
    async def unbox_snippet(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id,
                                          interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if current_credits < 500:
            await interaction.followup.send(
                f"❌ You need **500 Credits**! You have **{current_credits}**.")
            return

        await UserProfile.update_user(
            interaction.user.id, {"studio_credits": current_credits - 500})

        msg = await interaction.followup.send(UNBOX_FRAMES[0], wait=True)
        for frame in UNBOX_FRAMES[1:]:
            await asyncio.sleep(0.8)
            try:
                await msg.edit(content=frame)
            except Exception:
                pass

        rarity, rarity_data, snippet = roll_snippet()
        xp_bonus = {
            "common": 5,
            "uncommon": 10,
            "rare": 25,
            "epic": 50,
            "legendary": 100
        }
        bonus = xp_bonus.get(rarity, 5)
        await UserProfile.add_xp(interaction.user.id, bonus)

        code_text = snippet['code'][:900]
        if len(snippet['code']) > 900:
            code_text += "\n-- ... (truncated)"

        embed = discord.Embed(
            title=
            f"{rarity_data['emoji']} {rarity.upper()} — {snippet['name']}!",
            description=f"**{snippet['desc']}**",
            color=rarity_data["color"])
        embed.add_field(name="📝 Code",
                        value=f"```lua\n{code_text}\n```",
                        inline=False)
        embed.add_field(
            name="Rarity",
            value=
            f"{rarity_data['emoji']} {rarity.upper()} ({rarity_data['chance']}%)",
            inline=True)
        embed.add_field(name="Bonus XP", value=f"✨ +{bonus}", inline=True)
        embed.set_footer(
            text=
            f"Unboxed by {interaction.user.display_name} | 500 Credits spent")
        await msg.edit(content=None, embed=embed)

    # ========== 4. FLEX WEALTH ==========
    @app_commands.command(name="flex-wealth",
                          description="💎 Show the richest devs in the server")
    async def flex_wealth(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from database import _memory_users

        if not _memory_users:
            await interaction.followup.send("❌ No users found!")
            return

        users = sorted(
            _memory_users.values(),
            key=lambda x:
            (x.get("pcredits", 0) * 1000) + x.get("studio_credits", 0),
            reverse=True)[:10]

        if not users:
            await interaction.followup.send("❌ No users found!")
            return

        embed = discord.Embed(title="💎💰 WEALTH LEADERBOARD 💰💎",
                              description="*The richest devs in the studio*\n",
                              color=0xF1C40F)

        medals = ["👑", "💎", "🥇", "🥈", "🥉", "💰", "💰", "💰", "💰", "💰"]
        for i, u in enumerate(users):
            total = (u.get('pcredits', 0) * 1000) + u.get('studio_credits', 0)
            embed.add_field(
                name=f"{medals[i]} #{i + 1} — {u.get('username', 'Unknown')}",
                value=
                f"💎 {u.get('pcredits', 0)} pCredits | 💰 {u.get('studio_credits', 0)} Credits | 🤖 {u.get('ai_credits', 0)} AI\n📊 Total: **{total:,}**",
                inline=False)

        embed.set_footer(text="Total = (pCredits × 1000) + Credits")
        await interaction.followup.send(embed=embed)

    # ========== 6. AI FIX ==========
    @app_commands.command(
        name="ai-fix",
        description="🔧 AI rewrites your code optimized (1 AI Credit)")
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

            embed = discord.Embed(title="🔧 Code Optimized!",
                                  description=f"By {AI_NAME} • 1 AI Credit",
                                  color=0x3498DB)
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 7. DEV CONFESSION ==========
    @app_commands.command(name="dev-confession",
                          description="🤫 Submit an anonymous dev confession")
    @app_commands.describe(confession="Your anonymous confession")
    async def dev_confession(self, interaction: discord.Interaction,
                             confession: str):
        await interaction.response.defer(ephemeral=True)

        if len(confession.strip()) < 10 or len(confession) > 500:
            await interaction.followup.send("❌ Must be 10-500 characters!",
                                            ephemeral=True)
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\nA dev confessed: \"{confession}\"\n\n"
            f"Write a SHORT funny reaction (1-2 sentences). Be witty and game-dev themed."
        )

        try:
            ai_comment = await call_ai(prompt)
            embed = discord.Embed(title="🤫 Anonymous Dev Confession",
                                  description=f"*\"{confession}\"*",
                                  color=0x9B59B6)
            embed.add_field(
                name=f"💬 {AI_NAME}'s Take",
                value=ai_comment[:1024]
                if not ai_comment.startswith("❌") else "No comment. 😶",
                inline=False)
            embed.set_footer(text="Someone in this server wrote this... 👀")
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ Posted anonymously!",
                                            ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {str(e)[:200]}",
                                            ephemeral=True)

    # ========== 8. AI PREDICT GAME ==========
    @app_commands.command(
        name="ai-predict-game",
        description="🔮 AI predicts game success (1 AI Credit)")
    @app_commands.describe(idea="Describe your game idea")
    async def ai_predict_game(self, interaction: discord.Interaction,
                              idea: str):
        await interaction.response.defer()

        if len(idea.strip()) < 10:
            await interaction.followup.send("❌ Need at least 10 characters!")
            return
        if not await check_ai_credits(interaction, 1):
            return

        prompt = (
            f"System: {AI_PERSONALITY}\n\nTASK: Analyze this Roblox game idea.\n\nIDEA: {idea[:1000]}\n\n"
            f"Provide:\n1. SUCCESS CHANCE %\n2. VERDICT: 🟢/🟡/🔴\n3. STRENGTHS\n4. WEAKNESSES\n"
            f"5. COMPETITION\n6. MONETIZATION\n7. DEV TIME\n8. KILLER TIP")

        try:
            result = await call_ai(prompt)
            if result.startswith("❌"):
                await refund_ai_credits(interaction.user.id, 1)
                await interaction.followup.send(result)
                return

            embed = discord.Embed(title="🔮 Game Prediction",
                                  description=f"**Idea:** {idea[:200]}",
                                  color=0x9B59B6)
            embed.set_footer(
                text=
                f"By {AI_NAME} • {interaction.user.display_name} • 1 AI Credit"
            )
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 9. IDEAS ==========
    @app_commands.command(
        name="ideas", description="💡 AI generates game ideas (1 AI Credit)")
    @app_commands.describe(keyword="Theme (optional)")
    async def ideas(self,
                    interaction: discord.Interaction,
                    keyword: str = None):
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

            embed = discord.Embed(
                title="💡 Game Ideas",
                description=f"**Theme:** {keyword or 'Trending'}",
                color=0xF1C40F)
            msg = await interaction.followup.send(embed=embed, wait=True)
            await ai_handler.send_response(
                message=msg,
                ai_text=result,
                user_name=interaction.user.display_name)
        except Exception as e:
            await refund_ai_credits(interaction.user.id, 1)
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    # ========== 10. COIN FLIP ==========
    COINFLIP_FRAMES = [
        # Frame 1 - Coin on thumb
        "\n\n\n\n            🪙\n            🤚\n",

        # Frame 2 - Lifting
        "\n\n\n          🪙\n\n            🤚\n",

        # Frame 3 - Rising
        "\n\n      🪙\n\n\n            🤚\n",

        # Frame 4 - Peak
        "\n  🪙\n\n\n\n            🤚\n",

        # Frame 5 - Spin ◼️
        "\n  ◼️\n\n\n\n            🤚\n",

        # Frame 6 - Spin ◻️
        "\n  ◻️\n\n\n\n            🤚\n",

        # Frame 7 - Spin ◼️
        "\n  ◼️\n\n\n\n            🤚\n",

        # Frame 8 - Spin ◻️
        "\n  ◻️\n\n\n\n            🤚\n",

        # Frame 9 - Spin ◼️
        "\n  ◼️\n\n\n\n            🤚\n",

        # Frame 10 - Spin ◻️
        "\n  ◻️\n\n\n\n            🤚\n",

        # Frame 11 - Falling
        "\n\n      🪙\n\n\n            🤚\n",

        # Frame 12 - Falling more
        "\n\n\n          🪙\n\n            🤚\n",

        # Frame 13 - Land
        "\n\n\n\n            🪙\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔\n",

        # Frame 14 - Bounce
        "\n\n\n\n         🪙\n    ▔▔▔▔▔▔▔▔▔▔▔▔▔\n",

        # Frame 15 - Settle
        "\n\n\n\n\n    ▔▔▔▔🪙▔▔▔▔▔▔▔▔\n",

        # Frame 16 - Suspense
        "\n\n\n\n\n    ▔▔▔▔🪙▔▔▔▔▔▔▔▔\n         ...\n",

        # Frame 17 - Placeholder (replaced in code)
        "RESULT",
    ]

    COINFLIP_SPEEDS = [
        0.3,  # Frame 1  - on thumb
        0.3,  # Frame 2  - lifting
        0.3,  # Frame 3  - rising
        0.2,  # Frame 4  - peak
        0.12,  # Frame 5  - spin ◼️
        0.12,  # Frame 6  - spin ◻️
        0.12,  # Frame 7  - spin ◼️
        0.12,  # Frame 8  - spin ◻️
        0.12,  # Frame 9  - spin ◼️
        0.12,  # Frame 10 - spin ◻️
        0.25,  # Frame 11 - falling
        0.25,  # Frame 12 - falling more
        0.3,  # Frame 13 - land
        0.3,  # Frame 14 - bounce
        0.4,  # Frame 15 - settle
        0.8,  # Frame 16 - suspense
    ]

    @app_commands.command(name="coinflip",
                          description="🪙 Flip a coin and bet credits!")
    @app_commands.describe(choice="Heads or Tails",
                           bet="Credits to bet (0 for free)")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails"),
    ])
    async def coinflip(self,
                       interaction: discord.Interaction,
                       choice: str,
                       bet: int = 0):
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id,
                                          interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)

        # ===== VALIDATION =====
        if bet < 0 or bet > 5000:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="Bet must be between **0** and **5,000** credits!",
                color=0xE74C3C)
            await interaction.followup.send(embed=embed)
            return

        if bet > 0 and current_credits < bet:
            embed = discord.Embed(
                title="💸 Not Enough Credits",
                description=
                f"You need **{bet:,}** but only have **{current_credits:,}** credits!",
                color=0xE74C3C)
            embed.set_footer(text="💡 Use /daily or /quiz to earn more!")
            await interaction.followup.send(embed=embed)
            return

        # ===== DETERMINE RESULT =====
        result = random.choice(["heads", "tails"])
        won = result == choice

        # ===== PLAY ANIMATION =====
        anim_embed = discord.Embed(title="🪙 Coin Flip",
                                   description=self.COINFLIP_FRAMES[0],
                                   color=0xF1C40F)
        anim_embed.add_field(name="🎯 Pick",
                             value=f"**{choice.upper()}**",
                             inline=True)
        if bet > 0:
            anim_embed.add_field(name="💰 Bet",
                                 value=f"**{bet:,}**",
                                 inline=True)

        msg = await interaction.followup.send(embed=anim_embed, wait=True)

        for i, frame in enumerate(self.COINFLIP_FRAMES[:-1]):
            # Color shifts during animation
            if i <= 3:
                color = 0xF1C40F  # Gold - toss
            elif i <= 10:
                color = 0xE67E22  # Orange - spinning
            elif i <= 12:
                color = 0xF1C40F  # Gold - falling
            elif i <= 14:
                color = 0x95A5A6  # Gray - landing
            else:
                color = 0x7F8C8D  # Dark gray - suspense

            anim_embed = discord.Embed(title="🪙 Coin Flip",
                                       description=frame,
                                       color=color)
            anim_embed.add_field(name="🎯 Pick",
                                 value=f"**{choice.upper()}**",
                                 inline=True)
            if bet > 0:
                anim_embed.add_field(name="💰 Bet",
                                     value=f"**{bet:,}**",
                                     inline=True)

            try:
                await msg.edit(embed=anim_embed)
            except Exception:
                pass

            await asyncio.sleep(self.COINFLIP_SPEEDS[i])

        # ===== DRAMATIC PAUSE =====
        await asyncio.sleep(0.5)

        # ===== BUILD RESULT FRAME =====
        result_face = "◼️" if result == "heads" else "◻️"

        if won:
            result_frame = f"\n\n\n\n\n    ▔▔▔▔{result_face}▔▔▔▔▔▔▔▔\n       {result.upper()}!\n"
        else:
            result_frame = f"\n\n\n\n\n    ▔▔▔▔{result_face}▔▔▔▔▔▔▔▔\n       {result.upper()}!\n"

        # ===== PROCESS CREDITS =====
        if bet > 0:
            if won:
                new_balance = current_credits + bet
            else:
                new_balance = current_credits - bet
            await UserProfile.update_user(interaction.user.id,
                                          {"studio_credits": new_balance})
        else:
            new_balance = current_credits

        # ===== STREAK =====
        old_streak = user.get("coinflip_streak", 0)
        best_streak = user.get("best_coinflip_streak", 0)
        total_flips = user.get("total_coinflips", 0) + 1
        total_wins = user.get("coinflip_wins", 0) + (1 if won else 0)
        win_rate = (total_wins / total_flips * 100) if total_flips > 0 else 0

        if won:
            new_streak = old_streak + 1
        else:
            new_streak = 0

        new_best = max(new_streak, best_streak)

        await UserProfile.update_user(
            interaction.user.id, {
                "coinflip_streak": new_streak,
                "best_coinflip_streak": new_best,
                "total_coinflips": total_flips,
                "coinflip_wins": total_wins
            })

        # ===== STREAK TEXT =====
        if won:
            if new_streak >= 10:
                streak_text = f"💎 {new_streak}x GODLIKE!"
            elif new_streak >= 7:
                streak_text = f"🌟 {new_streak}x UNSTOPPABLE!"
            elif new_streak >= 5:
                streak_text = f"🔥 {new_streak}x ON FIRE!"
            elif new_streak >= 3:
                streak_text = f"⚡ {new_streak}x streak!"
            else:
                streak_text = f"✨ {new_streak}x"
        else:
            if old_streak >= 5:
                streak_text = f"💔 {old_streak}x DESTROYED!"
            elif old_streak >= 3:
                streak_text = f"💔 {old_streak}x broken!"
            else:
                streak_text = "No streak"

        # ===== RESULT EMBED =====
        if won:
            if bet > 0:
                result_embed = discord.Embed(
                    title=f"🎉 {result_face} {result.upper()} — YOU WIN!",
                    description=result_frame,
                    color=0x2ECC71)
                result_embed.add_field(name="💰 Won",
                                       value=f"+**{bet:,}**",
                                       inline=True)
                result_embed.add_field(name="💎 Balance",
                                       value=f"**{new_balance:,}**",
                                       inline=True)
            else:
                result_embed = discord.Embed(
                    title=f"✅ {result_face} {result.upper()} — CORRECT!",
                    description=result_frame,
                    color=0x2ECC71)
        else:
            if bet > 0:
                result_embed = discord.Embed(
                    title=f"💀 {result_face} {result.upper()} — YOU LOSE!",
                    description=result_frame,
                    color=0xE74C3C)
                result_embed.add_field(name="💸 Lost",
                                       value=f"-**{bet:,}**",
                                       inline=True)
                result_embed.add_field(name="💎 Balance",
                                       value=f"**{new_balance:,}**",
                                       inline=True)
            else:
                result_embed = discord.Embed(
                    title=f"❌ {result_face} {result.upper()} — WRONG!",
                    description=result_frame,
                    color=0xE74C3C)

        result_embed.add_field(name="🎯 Pick",
                               value=f"**{choice.upper()}**",
                               inline=True)
        result_embed.add_field(name="🪙 Result",
                               value=f"**{result.upper()}**",
                               inline=True)
        result_embed.add_field(name="🔥 Streak", value=streak_text, inline=True)

        # ===== STATS =====
        stats = (f"Flips: **{total_flips}** • "
                 f"Wins: **{total_wins}** • "
                 f"Rate: **{win_rate:.1f}%** • "
                 f"Best: **{new_best}x**")
        result_embed.add_field(name="📊 Stats", value=stats, inline=False)

        result_embed.set_footer(text=f"🪙 {interaction.user.display_name}")
        result_embed.timestamp = discord.utils.utcnow()

        await msg.edit(embed=result_embed)
        await interaction.response.defer()

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id,
                                          interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_credits = user.get("studio_credits", 0)
        if bet < 0 or bet > 5000:
            await interaction.followup.send("❌ Bet must be 0-5,000!")
            return
        if bet > 0 and current_credits < bet:
            await interaction.followup.send(
                f"❌ Not enough! You have **{current_credits}**.")
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
                await UserProfile.update_user(
                    interaction.user.id,
                    {"studio_credits": current_credits + bet})
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU WIN!",
                    description=
                    f"💰 Won **{bet}** Credits! Balance: **{current_credits + bet}**",
                    color=0x2ECC71)
            else:
                await UserProfile.update_user(
                    interaction.user.id,
                    {"studio_credits": current_credits - bet})
                embed = discord.Embed(
                    title=f"{result_emoji} {result.upper()}! — YOU LOSE!",
                    description=
                    f"💸 Lost **{bet}** Credits! Balance: **{current_credits - bet}**",
                    color=0xE74C3C)
        else:
            embed = discord.Embed(
                title=f"{result_emoji} {result.upper()}!",
                description=f"{'✅ Correct!' if won else '❌ Wrong!'}",
                color=0x2ECC71 if won else 0xE74C3C)

        embed.add_field(name="Pick", value=choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        await msg.edit(content=None, embed=embed)

    # ========== 11. AI TRIVIA (FULLY UPGRADED) ==========
    @app_commands.command(
        name="trivia",
        description="🧠 AI trivia with categories, streaks, and 💀 DEMON mode!")
    @app_commands.describe(difficulty="Question difficulty",
                           category="Question category")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="🟢 Easy", value="easy"),
        app_commands.Choice(name="🟡 Medium", value="medium"),
        app_commands.Choice(name="🟠 Hard", value="hard"),
        app_commands.Choice(name="🔴 Expert", value="expert"),
        app_commands.Choice(name="💀 Demon", value="demon"),
    ])
    async def trivia(self,
                     interaction: discord.Interaction,
                     difficulty: str = "medium",
                     category: str = None):
        await interaction.response.defer()

        user_id = interaction.user.id

        # Check cooldown
        cooldown_remaining = format_cooldown_remaining(user_id)
        if cooldown_remaining:
            embed = discord.Embed(
                title="💀 DEMON COOLDOWN ACTIVE",
                description=
                (f"You got a question wrong! You must wait before trying again.\n\n"
                 f"⏰ **Time remaining:** {cooldown_remaining}\n\n"
                 f"*The demons don't forgive easily...*"),
                color=0x8B0000)
            embed.set_footer(
                text="Wrong answers on demon/AI questions = 20 minute cooldown"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if user_id in self._trivia_locks:
            await interaction.followup.send(
                "❌ You already have a trivia in progress!", ephemeral=True)
            return

        self._trivia_locks.add(user_id)
        try:
            await self._run_trivia_session(interaction, difficulty, category)
        finally:
            self._trivia_locks.discard(user_id)

    async def _run_trivia_session(self,
                                  interaction: discord.Interaction,
                                  difficulty: str,
                                  category: str = None):
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
                    f"⚠️ Wrong answer = **20 MINUTE COOLDOWN**")
            else:
                pool_status = f"\n\n📊 Progress: **{seen_count}/{total_fallbacks}** questions answered"

            picker_embed = discord.Embed(
                title="🧠 AI Trivia — Pick a Category!",
                description=
                (f"**Difficulty:** {TRIVIA_DIFFICULTIES.get(current_difficulty, TRIVIA_DIFFICULTIES['medium'])['emoji']} "
                 f"{current_difficulty.title()}"
                 f"{pool_status}"),
                color=0x5865F2)

            for key, info in TRIVIA_CATEGORIES.items():
                picker_embed.add_field(name=f"{info['emoji']} {info['name']}",
                                       value=info['description'],
                                       inline=True)

            picker_view = TriviaCategoryView(user_id, current_difficulty)
            await interaction.followup.send(embed=picker_embed,
                                            view=picker_view)
            await picker_view.wait()

            if picker_view.selected_category is None:
                await interaction.channel.send(
                    f"⏱️ {interaction.user.mention} Trivia timed out!")
                return
            category = picker_view.selected_category

        # Main trivia loop
        while True:
            # Check cooldown each round
            cooldown_remaining = format_cooldown_remaining(user_id)
            if cooldown_remaining:
                cooldown_embed = discord.Embed(
                    title="💀 COOLDOWN ACTIVATED",
                    description=
                    (f"You got a demon question wrong!\n\n"
                     f"⏰ **Wait:** {cooldown_remaining}\n\n"
                     f"**Session Stats:**\n"
                     f"🔥 Streak: {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits"
                     ),
                    color=0x8B0000)
                await interaction.channel.send(embed=cooldown_embed)
                break

            diff_info = TRIVIA_DIFFICULTIES.get(current_difficulty,
                                                TRIVIA_DIFFICULTIES["medium"])
            cat_info = TRIVIA_CATEGORIES.get(
                category if category != "random" else "general",
                TRIVIA_CATEGORIES["general"])

            # Check if all fallbacks are seen
            all_seen = _check_all_fallbacks_seen(user_id)
            is_demon_mode = all_seen or current_difficulty == "demon"

            # Loading
            streak_text = f" | 🔥 Streak: {streak}" if streak > 0 else ""
            demon_warning = "\n💀 **DEMON MODE** — Wrong = 20 min cooldown!" if is_demon_mode else ""

            loading_embed = discord.Embed(
                title="🧠 Generating Question...",
                description=
                (f"{'💀' if is_demon_mode else '🤖'} "
                 f"{'Summoning a DEMON question...' if is_demon_mode else 'Preparing question...'}"
                 f"{streak_text}{demon_warning}"),
                color=0x8B0000 if is_demon_mode else diff_info["color"])
            loading_msg = await interaction.channel.send(embed=loading_embed)

            # Generate question
            if is_demon_mode:
                question = await generate_ai_trivia(user_id,
                                                    category,
                                                    "demon",
                                                    force_ai=True)
            else:
                question = await generate_ai_trivia(user_id, category,
                                                    current_difficulty)

            ai_generated = question.get("ai_generated", False)
            remaining = question.get("remaining_fallbacks", 0)
            q_difficulty = question.get("difficulty", current_difficulty)
            is_demon_q = q_difficulty == "demon" or is_demon_mode

            actual_diff_info = TRIVIA_DIFFICULTIES.get(q_difficulty, diff_info)
            actual_cat = TRIVIA_CATEGORIES.get(
                question.get("category", "general"),
                TRIVIA_CATEGORIES["general"])

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
                title=
                f"{'💀' if is_demon_q else '🧠'} {'DEMON TRIVIA' if is_demon_q else 'Dev Trivia'} — {actual_cat['emoji']} {actual_cat['name']}",
                description=
                (f"{actual_diff_info['emoji']} **{q_difficulty.title()}** | {badge}\n\n"
                 f"**{question['q']}**"
                 f"{streak_bonus}"
                 f"{penalty_warning}\n\n"
                 f"⏱️ {timer} seconds!"),
                color=actual_diff_info["color"])

            if streak > 0:
                question_embed.set_footer(
                    text=
                    f"🔥 Streak: {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits"
                )

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
                    color=0x95A5A6)
                if explanation:
                    result.add_field(name="📖 Explanation",
                                     value=explanation[:500],
                                     inline=False)
                if streak > 0:
                    result.add_field(
                        name="🔥 Streak Ended!",
                        value=
                        f"Final: **{streak}** | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                        inline=False)

                # Apply cooldown if demon
                if is_demon_q:
                    _trivia_cooldowns[user_id] = time.time() + (20 * 60)
                    result.add_field(
                        name="💀 DEMON PUNISHMENT",
                        value=
                        "⏰ **20 minute cooldown** applied for not answering!",
                        inline=False)
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
                    description=
                    (f"**{correct_text}**\n\n"
                     f"✨ +{earned_xp} XP | 💰 +{earned_credits} Credits"
                     f"{f' (x{multiplier:.2f} bonus!)' if multiplier > 1 else ''}"
                     ),
                    color=0x57F287 if is_demon_q else 0x2ECC71)
                if explanation:
                    result.add_field(name="📖 Explanation",
                                     value=explanation[:500],
                                     inline=False)
                if fun_fact:
                    result.add_field(name="💡 Fun Fact",
                                     value=fun_fact[:300],
                                     inline=False)
                result.add_field(
                    name="📊 Session",
                    value=
                    f"🔥 {streak} | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                    inline=False)

                if is_demon_q:
                    result.set_footer(
                        text="You survived the demon... for now. 💀")
                await interaction.channel.send(embed=result)

                # Continue?
                continue_view = TriviaStreakView(user_id, streak, category,
                                                 current_difficulty)
                continue_msg = await interaction.channel.send(
                    f"🔥 **{streak} streak!** Keep going?", view=continue_view)
                await continue_view.wait()

                if continue_view.continue_playing is None or continue_view.continue_playing is False:
                    cashout_embed = discord.Embed(
                        title=f"💰 Session Complete!",
                        description=
                        (f"**Final Streak:** 🔥 {streak}\n"
                         f"**Total XP:** ✨ {total_xp}\n"
                         f"**Total Credits:** 💰 {total_credits}\n"
                         f"**Difficulty:** {actual_diff_info['emoji']} {current_difficulty.title()}"
                         ),
                        color=0xF1C40F)
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
                    description=(f"You picked: **{wrong_text}**\n"
                                 f"✅ Correct: **{correct_text}**"),
                    color=0x8B0000 if is_demon_q else 0xE74C3C)
                if explanation:
                    result.add_field(name="📖 Explanation",
                                     value=explanation[:500],
                                     inline=False)
                if fun_fact:
                    result.add_field(name="💡 Fun Fact",
                                     value=fun_fact[:300],
                                     inline=False)

                if streak > 0:
                    result.add_field(
                        name="🔥 Streak Ended!",
                        value=
                        f"Final: **{streak}** | ✨ {total_xp} XP | 💰 {total_credits} Credits",
                        inline=False)

                # Apply cooldown if demon/AI question
                if is_demon_q:
                    _trivia_cooldowns[user_id] = time.time() + (20 * 60
                                                                )  # 20 minutes
                    result.add_field(
                        name="💀 DEMON PUNISHMENT",
                        value=("⏰ **20 MINUTE COOLDOWN** applied!\n"
                               "You cannot play trivia for 20 minutes.\n\n"
                               "*The demons feast on your failure...*"),
                        inline=False)

                await interaction.channel.send(embed=result)
                break

    @trivia.autocomplete("category")
    async def trivia_category_autocomplete(
            self, interaction: discord.Interaction,
            current: str) -> list[app_commands.Choice[str]]:
        choices = []
        for key, info in TRIVIA_CATEGORIES.items():
            name = f"{info['emoji']} {info['name']}"
            if current.lower() in name.lower() or current.lower() in key.lower(
            ) or not current:
                choices.append(app_commands.Choice(name=name, value=key))
        return choices[:25]


async def setup(bot):
    await bot.add_cog(FunCog(bot))
