import os
import re
import json
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_COLOR
from database import UserProfile


# -----------------------------
# OpenRouter Configuration
# -----------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model pools for different purposes
CODER_MODELS = [
    "qwen/qwen3-coder:free",
    "deepseek/deepseek-chat-v3-0324:free",
]

EXPLAIN_MODELS = [
    "qwen/qwen3-235b-a22b:free",
    "qwen/qwen3-32b:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

ALL_MODELS = CODER_MODELS + EXPLAIN_MODELS

MAX_CONVERSATION_MESSAGES = 150


# -----------------------------
# 50 LESSONS (shortened for space - use your full LESSONS list)
# -----------------------------
LESSONS: List[dict] = [
    # ===== PHASE 1: FUNDAMENTALS (1-12) =====
    {
        "n": 1,
        "title": "print() and Basic Output",
        "phase": "Fundamentals",
        "keywords": ["print", "output", "console", "warn", "error", "debug"],
        "difficulty": "Beginner",
        "prerequisites": [],
        "learning_objectives": [
            "Understand what print() is and why it matters",
            "Use print() to debug code",
            "Distinguish between print(), warn(), and error()",
            "Print multiple values simultaneously",
            "Use string formatting within print",
        ],
        "subtopics": [
            {"name": "Basic print()", "description": "How to use print() to display text", "examples": 2},
            {"name": "In biến", "description": "How to print values of variables", "examples": 2},
            {"name": "In nhiều giá trị", "description": "print(a, b, c) with commas", "examples": 2},
            {"name": "warn() cho cảnh báo", "description": "When to use warn()", "examples": 1},
            {"name": "error() cho lỗi", "description": "When to use error()", "examples": 1},
            {"name": "Debug với print", "description": "Basic debugging techniques", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting parentheses: print 'hello' instead of print('hello')",
            "Confusing print and return",
            "Not knowing where output appears in Roblox Studio",
        ],
        "real_world": "Debug scripts, log player actions, test code",
        "estimated_time": "15-20 minutes",
        "mini_project": "Create a script to print player info when they join the game"
    },
    {
        "n": 2,
        "title": "Variables - Local and Global",
        "phase": "Fundamentals",
        "keywords": ["local", "global", "variable", "scope", "assignment", "declare"],
        "difficulty": "Beginner",
        "prerequisites": [1],
        "learning_objectives": [
            "Understand what variables are and why they are needed",
            "Declare local variables correctly",
            "Understand why you should AVOID global variables",
            "Follow variable naming conventions",
            "Assign and change variable values",
        ],
        "subtopics": [
            {"name": "What is a variable?", "description": "Data storage container concept", "examples": 2},
            {"name": "Declaring local", "description": "local variableName = value", "examples": 3},
            {"name": "Global variables", "description": "Why they should NOT be used", "examples": 2},
            {"name": "Naming conventions", "description": "camelCase, UPPER_CASE for constants", "examples": 2},
            {"name": "Reassignment", "description": "Changing variable values", "examples": 2},
            {"name": "Multiple assignment", "description": "local a, b, c = 1, 2, 3", "examples": 1},
        ],
        "common_mistakes": [
            "Not using local -> creating global variables",
            "Using unclear variable names: x, temp, data",
            "Using a variable before declaring it",
        ],
        "real_world": "Save player health, game settings, counters",
        "estimated_time": "20-25 minutes",
        "mini_project": "Create a player data system using variables"
    },
    {
        "n": 3,
        "title": "Data Types",
        "phase": "Fundamentals",
        "keywords": ["number", "string", "boolean", "nil", "table", "typeof", "type"],
        "difficulty": "Beginner",
        "prerequisites": [2],
        "learning_objectives": [
            "Identify 6 basic data types in Lua",
            "Use typeof() to check types",
            "Understand when to use each type",
            "Convert between types",
        ],
        "subtopics": [
            {"name": "Numbers", "description": "Integers and decimals, no distinction", "examples": 2},
            {"name": "Strings", "description": "Text in quotes", "examples": 2},
            {"name": "Booleans", "description": "true and false", "examples": 2},
            {"name": "nil", "description": "The 'nothing' value", "examples": 2},
            {"name": "Tables", "description": "Basic introduction to tables", "examples": 1},
            {"name": "typeof()", "description": "Checking the type of a value", "examples": 2},
            {"name": "Type conversion", "description": "tonumber(), tostring()", "examples": 2},
        ],
        "common_mistakes": [
            "Confusing '5' (string) with 5 (number)",
            "Forgetting nil is not 'nil' (string)",
            "Not checking type before operations",
        ],
        "real_world": "Player health (number), name (string), isAlive (boolean)",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a player data table with various types"
    },
    {
        "n": 4,
        "title": "Strings - Advanced Text Manipulation",
        "phase": "Fundamentals",
        "keywords": ["string", "..", "concat", "format", "interpolation", "length", "sub", "find"],
        "difficulty": "Beginner",
        "prerequisites": [3],
        "learning_objectives": [
            "Master creating and manipulating strings",
            "Concatenate strings using the .. operator",
            "Use string methods effectively",
            "Use string interpolation with backticks",
        ],
        "subtopics": [
            {"name": "Creating strings", "description": "Single, double quotes, [[multiline]]", "examples": 2},
            {"name": "Concatenation", "description": "Joining strings with ..", "examples": 2},
            {"name": "String length", "description": "#string or string.len()", "examples": 1},
            {"name": "string.sub()", "description": "Extracting part of a string", "examples": 2},
            {"name": "string.find()", "description": "Finding substring positions", "examples": 2},
            {"name": "string.upper/lower", "description": "Changing case", "examples": 1},
            {"name": "string.format()", "description": "Formatting strings with placeholders", "examples": 2},
            {"name": "String interpolation", "description": "`Hello {name}`", "examples": 2},
        ],
        "common_mistakes": [
            "Joining numbers with strings without conversion: 'Score: ' .. 100",
            "Confusing # with .len()",
            "Indexing strings from 1, not 0",
        ],
        "real_world": "Chat messages, UI text, formatted output",
        "estimated_time": "20-25 minutes",
        "mini_project": "Create a chat format system with colors and prefixes"
    },
    {
        "n": 5,
        "title": "Math - Mathematics in Lua",
        "phase": "Fundamentals",
        "keywords": ["math", "random", "floor", "ceil", "abs", "clamp", "+", "-", "*", "/", "%", "^"],
        "difficulty": "Beginner",
        "prerequisites": [3],
        "learning_objectives": [
            "Use all arithmetic operators",
            "Understand math library functions",
            "Generate random numbers for game mechanics",
            "Clamp values within a range",
        ],
        "subtopics": [
            {"name": "Arithmetic operators", "description": "+, -, *, /, %, ^", "examples": 2},
            {"name": "Order of operations", "description": "PEMDAS in Lua", "examples": 2},
            {"name": "math.floor/ceil", "description": "Rounding down/up", "examples": 2},
            {"name": "math.abs", "description": "Absolute value", "examples": 1},
            {"name": "math.random", "description": "Random numbers", "examples": 3},
            {"name": "math.clamp", "description": "Limiting values within a range", "examples": 2},
            {"name": "math.min/max", "description": "Finding minimum/maximum", "examples": 1},
        ],
        "common_mistakes": [
            "Division by zero",
            "Forgetting that math.random() may need a seed",
            "Not using clamp for health/values",
        ],
        "real_world": "Damage calculations, random loot, health regen",
        "estimated_time": "20-25 minutes",
        "mini_project": "Create a damage calculator with random critical chance"
    },
    {
        "n": 6,
        "title": "Booleans and Comparisons",
        "phase": "Fundamentals",
        "keywords": ["true", "false", "==", "~=", "<", ">", "<=", ">=", "and", "or", "not"],
        "difficulty": "Beginner",
        "prerequisites": [3],
        "learning_objectives": [
            "Understand true/false and truthy/falsy",
            "Use comparison operators",
            "Combine conditions with and/or/not",
            "Short-circuit evaluation",
        ],
        "subtopics": [
            {"name": "true and false", "description": "Boolean values", "examples": 2},
            {"name": "Comparison operators", "description": "==, ~=, <, >, <=, >=", "examples": 3},
            {"name": "Logical AND", "description": "Both must be true", "examples": 2},
            {"name": "Logical OR", "description": "One of them must be true", "examples": 2},
            {"name": "Logical NOT", "description": "Inverting a boolean", "examples": 2},
            {"name": "Truthy/Falsy", "description": "nil and false are falsy", "examples": 2},
            {"name": "Short-circuit", "description": "and/or returning values", "examples": 2},
        ],
        "common_mistakes": [
            "Using = instead of == for comparison",
            "Using != instead of ~=",
            "Not understanding truthy/falsy",
        ],
        "real_world": "Checking player conditions, game state logic",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a permission system with multiple conditions"
    },
    {
        "n": 7,
        "title": "if/elseif/else - Conditions",
        "phase": "Fundamentals",
        "keywords": ["if", "then", "elseif", "else", "end", "conditional", "branch"],
        "difficulty": "Beginner",
        "prerequisites": [6],
        "learning_objectives": [
            "Write if statements correctly",
            "Use elseif for multiple conditions",
            "Nested if statements",
            "Guard clauses pattern",
        ],
        "subtopics": [
            {"name": "if-then-end", "description": "Basic structure", "examples": 2},
            {"name": "if-else", "description": "Adding an alternative branch", "examples": 2},
            {"name": "elseif chains", "description": "Multiple conditions", "examples": 2},
            {"name": "Nested if", "description": "If inside an if", "examples": 2},
            {"name": "Guard clauses", "description": "Early return pattern", "examples": 2},
            {"name": "Ternary-like", "description": "condition and a or b", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting 'then' after a condition",
            "Forgetting 'end'",
            "Using too many nested ifs (pyramid of doom)",
        ],
        "real_world": "Permission checks, level requirements, game state",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a rank system based on player level"
    },
    {
        "n": 8,
        "title": "Functions - Basic Functions",
        "phase": "Fundamentals",
        "keywords": ["function", "end", "call", "invoke", "define", "declaration"],
        "difficulty": "Beginner",
        "prerequisites": [7],
        "learning_objectives": [
            "Understand what a function is and why it's needed",
            "Define and call functions",
            "DRY (Don't Repeat Yourself) principle",
            "Local vs global functions",
        ],
        "subtopics": [
            {"name": "What is a function?", "description": "Reusable code blocks", "examples": 2},
            {"name": "Defining a function", "description": "local function name() end", "examples": 2},
            {"name": "Calling a function", "description": "functionName()", "examples": 2},
            {"name": "Anonymous functions", "description": "Unnamed function() end", "examples": 2},
            {"name": "Functions as values", "description": "local f = function() end", "examples": 1},
            {"name": "DRY principle", "description": "Don't Repeat Yourself", "examples": 2},
        ],
        "common_mistakes": [
            "Calling a function before defining it",
            "Not using local for functions",
            "Forgetting to call the function (only defining it)",
        ],
        "real_world": "Reusable game logic, event handlers",
        "estimated_time": "25-30 minutes",
        "mini_project": "Refactor repeated code into functions"
    },
    {
        "n": 9,
        "title": "Functions - Parameters and Return",
        "phase": "Fundamentals",
        "keywords": ["parameter", "argument", "return", "multiple return", "default", "variadic"],
        "difficulty": "Intermediate",
        "prerequisites": [8],
        "learning_objectives": [
            "Pass data into functions using parameters",
            "Return data with the return statement",
            "Multiple return values",
            "Default parameter pattern",
        ],
        "subtopics": [
            {"name": "Parameters", "description": "Receiving input into a function", "examples": 2},
            {"name": "Arguments", "description": "Values passed when calling", "examples": 2},
            {"name": "Return statement", "description": "Returning a value", "examples": 2},
            {"name": "Multiple returns", "description": "return a, b, c", "examples": 2},
            {"name": "Default values", "description": "param = param or default", "examples": 2},
            {"name": "Variadic (...)", "description": "Receiving unlimited number of args", "examples": 2},
        ],
        "common_mistakes": [
            "Not returning anything (nil by default)",
            "Forgetting to receive multiple returns",
            "Changing a parameter doesn't affect outside the function",
        ],
        "real_world": "Damage calculation, utility functions",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create utility functions for your game"
    },
    {
        "n": 10,
        "title": "Tables - Arrays",
        "phase": "Fundamentals",
        "keywords": ["table", "array", "index", "insert", "remove", "ipairs"],
        "difficulty": "Intermediate",
        "prerequisites": [9],
        "learning_objectives": [
            "Tạo và thao tác arrays",
            "Index từ 1 (không phải 0)",
            "Thêm/xóa elements",
            "Lấy length với #",
        ],
        "subtopics": [
            {"name": "Tạo array", "description": "local arr = {1, 2, 3}", "examples": 2},
            {"name": "Truy cập elements", "description": "arr[1], arr[2]", "examples": 2},
            {"name": "Thay đổi elements", "description": "arr[1] = newValue", "examples": 2},
            {"name": "table.insert", "description": "Thêm element", "examples": 2},
            {"name": "table.remove", "description": "Xóa element", "examples": 2},
            {"name": "Array length", "description": "#array", "examples": 2},
            {"name": "Nested arrays", "description": "Array trong array", "examples": 1},
        ],
        "common_mistakes": [
            "Index từ 0 (Lua bắt đầu từ 1)",
            "Dùng table.insert sai cách",
            "Quên # chỉ work với sequential indices",
        ],
        "real_world": "Inventory systems, player lists",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo inventory system đơn giản"
    },
    {
        "n": 11,
        "title": "Tables - Dictionaries",
        "phase": "Fundamentals",
        "keywords": ["dictionary", "key", "value", "pairs", "hash"],
        "difficulty": "Intermediate",
        "prerequisites": [10],
        "learning_objectives": [
            "Tạo key-value pairs",
            "Truy cập với dot và bracket notation",
            "Thêm/xóa keys",
            "Check key exists",
        ],
        "subtopics": [
            {"name": "Tạo dictionary", "description": "{key = value}", "examples": 2},
            {"name": "Dot notation", "description": "dict.key", "examples": 2},
            {"name": "Bracket notation", "description": "dict['key'] và dict[variable]", "examples": 2},
            {"name": "Thêm key mới", "description": "dict.newKey = value", "examples": 2},
            {"name": "Xóa key", "description": "dict.key = nil", "examples": 1},
            {"name": "Check exists", "description": "if dict.key then", "examples": 2},
            {"name": "Mixed tables", "description": "Array + dictionary", "examples": 2},
        ],
        "common_mistakes": [
            "Dùng dot cho key là biến",
            "Không check nil trước khi truy cập nested",
            "Nhầm giữa array và dictionary",
        ],
        "real_world": "Player stats, game config, data storage",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo player stats system"
    },
    {
        "n": 12,
        "title": "Loops - for và ipairs",
        "phase": "Fundamentals",
        "keywords": ["for", "ipairs", "loop", "iterate", "numeric", "break", "continue"],
        "difficulty": "Intermediate",
        "prerequisites": [10],
        "learning_objectives": [
            "Numeric for loop",
            "ipairs() cho arrays",
            "break và continue patterns",
            "Nested loops",
        ],
        "subtopics": [
            {"name": "Numeric for", "description": "for i = 1, 10 do", "examples": 2},
            {"name": "Step value", "description": "for i = 1, 10, 2 do", "examples": 2},
            {"name": "Counting backwards", "description": "for i = 10, 1, -1 do", "examples": 1},
            {"name": "ipairs()", "description": "Iterate arrays", "examples": 2},
            {"name": "break", "description": "Thoát loop sớm", "examples": 2},
            {"name": "continue pattern", "description": "Dùng if để skip", "examples": 2},
            {"name": "Nested loops", "description": "Loop trong loop", "examples": 2},
        ],
        "common_mistakes": [
            "Thay đổi loop variable trong loop",
            "Infinite loop",
            "Off-by-one errors",
        ],
        "real_world": "Process all players, spawn items",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo spawn system cho nhiều objects"
    },

    # ===== PHASE 2: INTERMEDIATE (13-24) =====
    {
        "n": 13,
        "title": "Loops - pairs và while",
        "phase": "Intermediate",
        "keywords": ["pairs", "while", "do", "repeat", "until"],
        "difficulty": "Intermediate",
        "prerequisites": [11, 12],
        "learning_objectives": [
            "pairs() cho dictionaries",
            "while loops",
            "repeat...until",
            "Choosing the right loop",
        ],
        "subtopics": [
            {"name": "pairs()", "description": "Iterate dictionaries", "examples": 2},
            {"name": "pairs vs ipairs", "description": "Khi nào dùng cái nào", "examples": 2},
            {"name": "while loop", "description": "while condition do", "examples": 2},
            {"name": "Infinite while", "description": "while true do (với break)", "examples": 2},
            {"name": "repeat until", "description": "Chạy ít nhất 1 lần", "examples": 2},
            {"name": "Loop comparison", "description": "for vs while vs repeat", "examples": 2},
        ],
        "common_mistakes": [
            "pairs() order không đảm bảo",
            "Infinite loop không có break/condition",
            "Modify table while iterating",
        ],
        "real_world": "Game loops, waiting for conditions",
        "estimated_time": "25-30 minutes",
        "mini_project": "Tạo game loop với countdown"
    },
    {
        "n": 14,
        "title": "Colon Syntax và Methods",
        "phase": "Intermediate",
        "keywords": [":", "self", "method", "colon", "dot", "object"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 11],
        "learning_objectives": [
            "Hiểu : vs . syntax",
            "self parameter",
            "Định nghĩa methods",
            "Roblox API dùng colon",
        ],
        "subtopics": [
            {"name": "Dot vs colon", "description": "Sự khác biệt quan trọng", "examples": 3},
            {"name": "self là gì?", "description": "Reference đến object", "examples": 2},
            {"name": "Colon auto-passes self", "description": "obj:method() = obj.method(obj)", "examples": 2},
            {"name": "Định nghĩa methods", "description": "function obj:methodName()", "examples": 2},
            {"name": "Roblox uses colon", "description": "part:Destroy(), player:Kick()", "examples": 2},
        ],
        "common_mistakes": [
            "Dùng . khi cần :",
            "Dùng : khi cần .",
            "Quên self trong method body",
        ],
        "real_world": "Tất cả Roblox methods dùng colon",
        "estimated_time": "25-30 minutes",
        "mini_project": "Tạo object với methods"
    },
    {
        "n": 15,
        "title": "Scope và Closures",
        "phase": "Intermediate",
        "keywords": ["scope", "local", "block", "lifetime", "closure", "upvalue"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 13],
        "learning_objectives": [
            "Block scope trong Lua",
            "Variable lifetime",
            "Closures là gì",
            "Practical closure uses",
        ],
        "subtopics": [
            {"name": "Block scope", "description": "Variables trong do...end", "examples": 2},
            {"name": "Function scope", "description": "Local trong function", "examples": 2},
            {"name": "Variable shadowing", "description": "Cùng tên ở scope khác", "examples": 2},
            {"name": "Closures", "description": "Function nhớ scope", "examples": 3},
            {"name": "Upvalues", "description": "Variables từ outer scope", "examples": 2},
            {"name": "Practical closures", "description": "Factories, callbacks", "examples": 2},
        ],
        "common_mistakes": [
            "Không hiểu variable bị shadowed",
            "Closure giữ reference, không phải copy",
            "Memory leaks từ closures",
        ],
        "real_world": "Event handlers, factory functions",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo counter factory với closures"
    },
    {
        "n": 16,
        "title": "Error Handling - pcall và xpcall",
        "phase": "Intermediate",
        "keywords": ["pcall", "xpcall", "error", "assert", "debug", "protected"],
        "difficulty": "Intermediate",
        "prerequisites": [9],
        "learning_objectives": [
            "Tại sao cần error handling",
            "pcall() protected calls",
            "xpcall() với error handler",
            "assert() cho validation",
        ],
        "subtopics": [
            {"name": "error()", "description": "Throw errors", "examples": 2},
            {"name": "pcall()", "description": "Protected call", "examples": 3},
            {"name": "pcall returns", "description": "success, result/error", "examples": 2},
            {"name": "xpcall()", "description": "Custom error handler", "examples": 2},
            {"name": "assert()", "description": "Condition or error", "examples": 2},
            {"name": "Error patterns", "description": "Try-catch style", "examples": 2},
        ],
        "common_mistakes": [
            "Không check pcall success",
            "Swallow errors không log",
            "Dùng pcall cho mọi thứ",
        ],
        "real_world": "API calls, user input validation",
        "estimated_time": "25-30 minutes",
        "mini_project": "Tạo safe function wrapper"
    },
    {
        "n": 17,
        "title": "ModuleScripts và require()",
        "phase": "Intermediate",
        "keywords": ["modulescript", "module", "require", "return", "reusable", "organize"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 11],
        "learning_objectives": [
            "Tại sao cần ModuleScripts",
            "Cách tạo module đúng cách",
            "require() và caching",
            "Organize code với modules",
        ],
        "subtopics": [
            {"name": "ModuleScript là gì?", "description": "Reusable code container", "examples": 1},
            {"name": "Cấu trúc module", "description": "local M = {} ... return M", "examples": 2},
            {"name": "require()", "description": "Import module", "examples": 2},
            {"name": "Caching behavior", "description": "require() chỉ chạy 1 lần", "examples": 2},
            {"name": "Return table vs function", "description": "Patterns phổ biến", "examples": 2},
            {"name": "Module organization", "description": "Best practices", "examples": 2},
        ],
        "common_mistakes": [
            "Không return gì",
            "Return trước khi định nghĩa",
            "Circular dependencies",
        ],
        "real_world": "Shared utilities, config, game systems",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo module cho utility functions"
    },
    {
        "n": 18,
        "title": "Roblox Instances Basics",
        "phase": "Intermediate",
        "keywords": ["instance", "new", "parent", "workspace", "clone", "destroy", "findFirstChild"],
        "difficulty": "Intermediate",
        "prerequisites": [11, 14],
        "learning_objectives": [
            "Instance hierarchy",
            "Instance.new() đúng cách",
            "Parent và Children",
            "Tìm instances với Find methods",
        ],
        "subtopics": [
            {"name": "Instance là gì?", "description": "Objects trong Roblox", "examples": 2},
            {"name": "Instance.new()", "description": "Tạo instance mới", "examples": 2},
            {"name": "Parent property", "description": "Set Parent CUỐI CÙNG", "examples": 2},
            {"name": "FindFirstChild", "description": "Tìm child an toàn", "examples": 2},
            {"name": "WaitForChild", "description": "Đợi child load", "examples": 2},
            {"name": "Clone()", "description": "Copy instance", "examples": 2},
            {"name": "Destroy()", "description": "Xóa instance", "examples": 2},
        ],
        "common_mistakes": [
            "Set Parent trước Properties (performance)",
            "Dùng . thay vì FindFirstChild",
            "Không nil check sau Find",
        ],
        "real_world": "Spawning objects, creating effects",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo object spawner"
    },
    {
        "n": 19,
        "title": "Properties và CFrame Basics",
        "phase": "Intermediate",
        "keywords": ["property", "position", "size", "cframe", "vector3", "color3"],
        "difficulty": "Intermediate",
        "prerequisites": [18],
        "learning_objectives": [
            "Đọc và set properties",
            "Vector3 cho positions/sizes",
            "CFrame basics",
            "Color3 cho màu sắc",
        ],
        "subtopics": [
            {"name": "Reading properties", "description": "part.Position, part.Size", "examples": 2},
            {"name": "Setting properties", "description": "part.Transparency = 0.5", "examples": 2},
            {"name": "Vector3", "description": "Vector3.new(x, y, z)", "examples": 2},
            {"name": "CFrame basics", "description": "Position + Rotation", "examples": 3},
            {"name": "CFrame.new()", "description": "Tạo CFrame", "examples": 2},
            {"name": "Color3", "description": "RGB và fromRGB", "examples": 2},
        ],
        "common_mistakes": [
            "Modify Vector3 trực tiếp (immutable)",
            "Nhầm Position với CFrame",
            "Color values 0-255 vs 0-1",
        ],
        "real_world": "Moving objects, changing appearance",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo part mover với color change"
    },
    {
        "n": 20,
        "title": "Events và Connections",
        "phase": "Intermediate",
        "keywords": ["event", "connect", "disconnect", "touched", "signal", "callback", "rbxScriptSignal"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 18],
        "learning_objectives": [
            "Event-driven programming",
            ":Connect() method",
            "Event parameters",
            "Disconnect và cleanup",
        ],
        "subtopics": [
            {"name": "Events là gì?", "description": "Signals khi something happens", "examples": 2},
            {"name": ":Connect()", "description": "Listen to events", "examples": 2},
            {"name": "Callback functions", "description": "Function chạy khi event fires", "examples": 2},
            {"name": "Event parameters", "description": "Data passed to callback", "examples": 2},
            {"name": "Storing connections", "description": "local conn = event:Connect()", "examples": 2},
            {"name": ":Disconnect()", "description": "Stop listening", "examples": 2},
            {"name": ":Once()", "description": "Listen chỉ 1 lần", "examples": 1},
            {"name": ":Wait()", "description": "Yield until event", "examples": 1},
        ],
        "common_mistakes": [
            "Không disconnect → memory leak",
            "Connect trong loop → multiple connections",
            "Quên event có parameters",
        ],
        "real_world": "Collision detection, player input, UI",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo touch-activated door"
    },
    {
        "n": 21,
        "title": "Player và Character",
        "phase": "Intermediate",
        "keywords": ["player", "character", "humanoid", "playerAdded", "characterAdded"],
        "difficulty": "Intermediate",
        "prerequisites": [20],
        "learning_objectives": [
            "Player vs Character",
            "Truy cập Players service",
            "PlayerAdded event",
            "CharacterAdded event",
        ],
        "subtopics": [
            {"name": "Player object", "description": "Account/data container", "examples": 2},
            {"name": "Character object", "description": "Avatar trong game", "examples": 2},
            {"name": "Players service", "description": "game:GetService('Players')", "examples": 2},
            {"name": "PlayerAdded", "description": "Khi player joins", "examples": 2},
            {"name": "PlayerRemoving", "description": "Khi player leaves", "examples": 2},
            {"name": "CharacterAdded", "description": "Khi character spawns", "examples": 2},
            {"name": "Humanoid", "description": "Control character", "examples": 2},
        ],
        "common_mistakes": [
            "Access character mà nil",
            "Không handle CharacterAdded",
            "Player vs Character confusion",
        ],
        "real_world": "Player join handling, respawn logic",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo welcome system với player data"
    },
    {
        "n": 22,
        "title": "Services trong Roblox",
        "phase": "Intermediate",
        "keywords": ["service", "getService", "workspace", "replicatedStorage", "serverStorage"],
        "difficulty": "Intermediate",
        "prerequisites": [18],
        "learning_objectives": [
            "Services là gì",
            "GetService() đúng cách",
            "Các services phổ biến",
            "Server vs Client services",
        ],
        "subtopics": [
            {"name": "Services là gì?", "description": "Singletons cung cấp functionality", "examples": 1},
            {"name": "GetService()", "description": "game:GetService('Name')", "examples": 2},
            {"name": "Workspace", "description": "Contains 3D objects", "examples": 2},
            {"name": "Players", "description": "All players", "examples": 1},
            {"name": "ReplicatedStorage", "description": "Shared assets", "examples": 2},
            {"name": "ServerStorage", "description": "Server-only assets", "examples": 2},
            {"name": "RunService", "description": "Game loop events", "examples": 2},
        ],
        "common_mistakes": [
            "Access ServerStorage từ client",
            "Không cache services",
            "Dùng game.Workspace thay vì workspace",
        ],
        "real_world": "Access game components properly",
        "estimated_time": "25-30 minutes",
        "mini_project": "Setup proper service references"
    },
    {
        "n": 23,
        "title": "task Library và Timing",
        "phase": "Intermediate",
        "keywords": ["task.wait", "task.spawn", "task.defer", "task.delay", "runservice", "heartbeat"],
        "difficulty": "Intermediate",
        "prerequisites": [13, 20],
        "learning_objectives": [
            "task vs wait()",
            "Parallel execution với spawn",
            "Frame-based timing",
            "Delta time",
        ],
        "subtopics": [
            {"name": "task.wait()", "description": "Better than wait()", "examples": 2},
            {"name": "task.spawn()", "description": "Run in parallel", "examples": 2},
            {"name": "task.defer()", "description": "Run next frame", "examples": 2},
            {"name": "task.delay()", "description": "Run after delay", "examples": 2},
            {"name": "task.cancel()", "description": "Cancel scheduled task", "examples": 1},
            {"name": "RunService.Heartbeat", "description": "Every frame", "examples": 2},
            {"name": "Delta time", "description": "Time since last frame", "examples": 2},
        ],
        "common_mistakes": [
            "Dùng wait() thay vì task.wait()",
            "Không handle task cancellation",
            "Không dùng dt cho smooth movement",
        ],
        "real_world": "Smooth animations, cooldowns, timers",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo cooldown system"
    },
    {
        "n": 24,
        "title": "Attributes và Tags",
        "phase": "Intermediate",
        "keywords": ["attribute", "tag", "collectionService", "setAttribute", "getAttribute"],
        "difficulty": "Intermediate",
        "prerequisites": [18, 22],
        "learning_objectives": [
            "Attributes cho custom data",
            "Tags cho categorization",
            "CollectionService",
            "Khi dùng attribute vs value",
        ],
        "subtopics": [
            {"name": "Attributes là gì?", "description": "Custom properties", "examples": 2},
            {"name": "SetAttribute()", "description": "Set attribute value", "examples": 2},
            {"name": "GetAttribute()", "description": "Get attribute value", "examples": 2},
            {"name": "GetAttributeChangedSignal", "description": "Listen for changes", "examples": 2},
            {"name": "Tags là gì?", "description": "Labels for instances", "examples": 2},
            {"name": "CollectionService", "description": "Get tagged instances", "examples": 2},
        ],
        "common_mistakes": [
            "Attribute types giới hạn",
            "Tag name typos",
            "Không handle nil attributes",
        ],
        "real_world": "Enemy types, item rarity, game states",
        "estimated_time": "25-30 minutes",
        "mini_project": "Tạo enemy tagging system"
    },

    # ===== PHASE 3: ADVANCED (25-36) =====
    {
        "n": 25,
        "title": "Client-Server Architecture",
        "phase": "Advanced",
        "keywords": ["client", "server", "localScript", "script", "replicate", "network"],
        "difficulty": "Advanced",
        "prerequisites": [17, 22],
        "learning_objectives": [
            "Client vs Server trong Roblox",
            "Script types",
            "Filtering Enabled",
            "Trust boundary",
        ],
        "subtopics": [
            {"name": "Client là gì?", "description": "Player's computer", "examples": 2},
            {"name": "Server là gì?", "description": "Roblox's computer", "examples": 2},
            {"name": "Script (Server)", "description": "Chạy trên server", "examples": 2},
            {"name": "LocalScript (Client)", "description": "Chạy trên client", "examples": 2},
            {"name": "Filtering Enabled", "description": "Client changes don't replicate", "examples": 2},
            {"name": "Trust boundary", "description": "NEVER trust client", "examples": 3},
        ],
        "common_mistakes": [
            "Trust client data",
            "Game logic on client",
            "Sensitive data to client",
        ],
        "real_world": "Multiplayer game architecture",
        "estimated_time": "35-40 minutes",
        "mini_project": "Design secure game system"
    },
    {
        "n": 26,
        "title": "RemoteEvents Basics",
        "phase": "Advanced",
        "keywords": ["remoteEvent", "fireServer", "onServerEvent", "fireClient", "onClientEvent"],
        "difficulty": "Advanced",
        "prerequisites": [25],
        "learning_objectives": [
            "RemoteEvent là gì",
            "Client → Server communication",
            "Server → Client communication",
            "Setup đúng cách",
        ],
        "subtopics": [
            {"name": "RemoteEvent là gì?", "description": "Cross-boundary communication", "examples": 1},
            {"name": "Create RemoteEvent", "description": "In ReplicatedStorage", "examples": 2},
            {"name": "FireServer()", "description": "Client sends to server", "examples": 2},
            {"name": "OnServerEvent", "description": "Server receives", "examples": 2},
            {"name": "FireClient()", "description": "Server sends to client", "examples": 2},
            {"name": "FireAllClients()", "description": "Broadcast to all", "examples": 2},
            {"name": "OnClientEvent", "description": "Client receives", "examples": 2},
        ],
        "common_mistakes": [
            "FireServer từ server",
            "OnServerEvent trên client",
            "Không pass player argument",
        ],
        "real_world": "Multiplayer actions, UI updates",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo simple chat system"
    },
    {
        "n": 27,
        "title": "RemoteEvents Security",
        "phase": "Advanced",
        "keywords": ["validate", "sanity", "exploit", "hack", "secure", "sanitize"],
        "difficulty": "Advanced",
        "prerequisites": [26],
        "learning_objectives": [
            "Tại sao security quan trọng",
            "Validate ALL inputs",
            "Sanity checks",
            "Common exploits",
        ],
        "subtopics": [
            {"name": "Never trust client", "description": "Rule #1", "examples": 2},
            {"name": "Type validation", "description": "typeof() check", "examples": 2},
            {"name": "Range validation", "description": "Giá trị hợp lý", "examples": 2},
            {"name": "Permission checks", "description": "Can player do this?", "examples": 2},
            {"name": "Rate limiting", "description": "Prevent spam", "examples": 2},
            {"name": "Common exploits", "description": "Examples of hacks", "examples": 3},
        ],
        "common_mistakes": [
            "Trust client-sent data",
            "Only validate on client",
            "Expose sensitive endpoints",
        ],
        "real_world": "Prevent cheating, secure economy",
        "estimated_time": "40-45 minutes",
        "mini_project": "Secure a RemoteEvent properly"
    },
    {
        "n": 28,
        "title": "RemoteFunctions",
        "phase": "Advanced",
        "keywords": ["remoteFunction", "invokeServer", "invokeClient", "callback", "return"],
        "difficulty": "Advanced",
        "prerequisites": [27],
        "learning_objectives": [
            "RemoteFunction vs RemoteEvent",
            "Request-Response pattern",
            "Khi nào dùng RemoteFunction",
            "Risks của InvokeClient",
        ],
        "subtopics": [
            {"name": "RemoteFunction là gì?", "description": "Returns a value", "examples": 2},
            {"name": "InvokeServer()", "description": "Client requests, gets response", "examples": 2},
            {"name": "OnServerInvoke", "description": "Server handles, returns", "examples": 2},
            {"name": "InvokeClient risks", "description": "NEVER use in production", "examples": 2},
            {"name": "Event vs Function", "description": "When to use which", "examples": 2},
            {"name": "Timeout handling", "description": "Handle no response", "examples": 2},
        ],
        "common_mistakes": [
            "Use InvokeClient",
            "No timeout handling",
            "Return sensitive data",
        ],
        "real_world": "Shop purchase, data requests",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo shop system với RemoteFunction"
    },
    {
        "n": 29,
        "title": "DataStoreService Basics",
        "phase": "Advanced",
        "keywords": ["dataStore", "save", "load", "getAsync", "setAsync", "persist"],
        "difficulty": "Advanced",
        "prerequisites": [16, 21],
        "learning_objectives": [
            "DataStore là gì",
            "GetAsync/SetAsync",
            "Error handling cho DataStore",
            "Rate limits",
        ],
        "subtopics": [
            {"name": "DataStoreService", "description": "Persistent storage", "examples": 1},
            {"name": "GetDataStore()", "description": "Get a data store", "examples": 2},
            {"name": "GetAsync()", "description": "Load data", "examples": 2},
            {"name": "SetAsync()", "description": "Save data", "examples": 2},
            {"name": "Error handling", "description": "pcall required", "examples": 3},
            {"name": "Rate limits", "description": "Request budgets", "examples": 2},
        ],
        "common_mistakes": [
            "Không pcall DataStore calls",
            "Spam SetAsync",
            "Save on every change",
        ],
        "real_world": "Player data persistence",
        "estimated_time": "40-45 minutes",
        "mini_project": "Basic data save system"
    },
    {
        "n": 30,
        "title": "DataStore Advanced Patterns",
        "phase": "Advanced",
        "keywords": ["updateAsync", "session", "cache", "autosave", "backup"],
        "difficulty": "Advanced",
        "prerequisites": [29],
        "learning_objectives": [
            "UpdateAsync for safety",
            "Session locking",
            "Caching patterns",
            "Autosave systems",
        ],
        "subtopics": [
            {"name": "UpdateAsync()", "description": "Atomic updates", "examples": 2},
            {"name": "Session locking", "description": "Prevent multi-server", "examples": 2},
            {"name": "In-memory cache", "description": "Store data in RAM", "examples": 2},
            {"name": "Autosave loop", "description": "Periodic saves", "examples": 2},
            {"name": "Save on leave", "description": "PlayerRemoving handler", "examples": 2},
            {"name": "Backup systems", "description": "Multiple keys", "examples": 2},
        ],
        "common_mistakes": [
            "Data loss on crash",
            "Race conditions",
            "No session handling",
        ],
        "real_world": "Production-grade save systems",
        "estimated_time": "45-50 minutes",
        "mini_project": "Complete save system với autosave"
    },
    {
        "n": 31,
        "title": "UI Basics với ScreenGui",
        "phase": "Advanced",
        "keywords": ["screenGui", "frame", "textLabel", "textButton", "imageLabel"],
        "difficulty": "Advanced",
        "prerequisites": [20, 25],
        "learning_objectives": [
            "ScreenGui structure",
            "Common UI elements",
            "Positioning với UDim2",
            "UI events",
        ],
        "subtopics": [
            {"name": "ScreenGui", "description": "UI container", "examples": 2},
            {"name": "Frame", "description": "Container/background", "examples": 2},
            {"name": "TextLabel", "description": "Display text", "examples": 2},
            {"name": "TextButton", "description": "Clickable button", "examples": 2},
            {"name": "UDim2 positioning", "description": "Scale và Offset", "examples": 3},
            {"name": "AnchorPoint", "description": "Origin point", "examples": 2},
            {"name": "MouseButton1Click", "description": "Button event", "examples": 2},
        ],
        "common_mistakes": [
            "Wrong parent for ScreenGui",
            "Mix Scale và Offset badly",
            "No AnchorPoint consideration",
        ],
        "real_world": "Game menus, HUDs",
        "estimated_time": "35-40 minutes",
        "mini_project": "Tạo simple menu UI"
    },
    {
        "n": 32,
        "title": "UI Layouts và Constraints",
        "phase": "Advanced",
        "keywords": ["uiListLayout", "uiGridLayout", "uiPadding", "uiCorner", "constraint"],
        "difficulty": "Advanced",
        "prerequisites": [31],
        "learning_objectives": [
            "Auto-layout UI",
            "UIListLayout, UIGridLayout",
            "UIConstraints",
            "Responsive design",
        ],
        "subtopics": [
            {"name": "UIListLayout", "description": "Stack elements", "examples": 2},
            {"name": "UIGridLayout", "description": "Grid arrangement", "examples": 2},
            {"name": "UIPageLayout", "description": "Swipeable pages", "examples": 1},
            {"name": "UIPadding", "description": "Inner spacing", "examples": 2},
            {"name": "UICorner", "description": "Rounded corners", "examples": 1},
            {"name": "UIAspectRatioConstraint", "description": "Keep ratio", "examples": 2},
            {"name": "UISizeConstraint", "description": "Min/max size", "examples": 1},
        ],
        "common_mistakes": [
            "Conflict với manual positioning",
            "Wrong layout order",
            "Forget SortOrder",
        ],
        "real_world": "Inventory grids, menus",
        "estimated_time": "30-35 minutes",
        "mini_project": "Tạo inventory grid UI"
    },
    {
        "n": 33,
        "title": "TweenService và Animations",
        "phase": "Advanced",
        "keywords": ["tween", "tweenService", "tweenInfo", "animate", "easing"],
        "difficulty": "Advanced",
        "prerequisites": [19, 23],
        "learning_objectives": [
            "TweenService basics",
            "TweenInfo options",
            "Easing styles",
            "Chained tweens",
        ],
        "subtopics": [
            {"name": "TweenService", "description": "Smooth animations", "examples": 1},
            {"name": "TweenInfo", "description": "Configuration", "examples": 2},
            {"name": "Create tween", "description": ":Create(instance, info, goals)", "examples": 2},
            {"name": "Easing styles", "description": "Linear, Quad, Bounce...", "examples": 2},
            {"name": "Easing direction", "description": "In, Out, InOut", "examples": 2},
            {"name": "Tween:Play()", "description": "Start animation", "examples": 2},
            {"name": "Tween.Completed", "description": "Wait for finish", "examples": 2},
        ],
        "common_mistakes": [
            "Tween destroyed instance",
            "Conflict tweens",
            "Wrong property type",
        ],
        "real_world": "UI animations, door opening",
        "estimated_time": "35-40 minutes",
        "mini_project": "Animated UI với TweenService"
    },
    {
        "n": 34,
        "title": "Object-Oriented Programming",
        "phase": "Advanced",
        "keywords": ["oop", "class", "object", "metatable", "inheritance", "__index"],
        "difficulty": "Advanced",
        "prerequisites": [14, 15],
        "learning_objectives": [
            "OOP concepts trong Lua",
            "Metatables cho classes",
            "__index metamethod",
            "Inheritance patterns",
        ],
        "subtopics": [
            {"name": "OOP là gì?", "description": "Objects với data và methods", "examples": 2},
            {"name": "Metatables", "description": "Change table behavior", "examples": 2},
            {"name": "__index", "description": "Property lookup", "examples": 3},
            {"name": "Class pattern", "description": "Standard Lua class", "examples": 3},
            {"name": ".new() constructor", "description": "Create instances", "examples": 2},
            {"name": "Inheritance", "description": "Extend classes", "examples": 2},
        ],
        "common_mistakes": [
            "Forget setmetatable",
            "Wrong self in methods",
            "Shallow copy issues",
        ],
        "real_world": "Game entities, systems",
        "estimated_time": "45-50 minutes",
        "mini_project": "Tạo Entity class system"
    },
    {
        "n": 35,
        "title": "Raycasting",
        "phase": "Advanced",
        "keywords": ["raycast", "ray", "hit", "normal", "raycastParams", "filter"],
        "difficulty": "Advanced",
        "prerequisites": [19, 22],
        "learning_objectives": [
            "Raycast là gì",
            "workspace:Raycast()",
            "RaycastParams",
            "Practical uses",
        ],
        "subtopics": [
            {"name": "Raycasting là gì?", "description": "Invisible line detection", "examples": 2},
            {"name": "workspace:Raycast()", "description": "Cast a ray", "examples": 2},
            {"name": "RaycastParams", "description": "Filter objects", "examples": 2},
            {"name": "RaycastResult", "description": "Instance, Position, Normal", "examples": 2},
            {"name": "FilterType", "description": "Include/Exclude", "examples": 2},
            {"name": "Multiple raycasts", "description": "Pattern examples", "examples": 2},
        ],
        "common_mistakes": [
            "Wrong direction vector",
            "Forget FilterDescendantsInstances",
            "Ray too short/long",
        ],
        "real_world": "Shooting, ground detection, line of sight",
        "estimated_time": "40-45 minutes",
        "mini_project": "Simple gun raycast system"
    },
    {
        "n": 36,
        "title": "Physics và BodyMovers",
        "phase": "Advanced",
        "keywords": ["physics", "bodyVelocity", "bodyForce", "alignPosition", "linearVelocity"],
        "difficulty": "Advanced",
        "prerequisites": [19, 23],
        "learning_objectives": [
            "Roblox physics system",
            "Legacy BodyMovers",
            "New Constraints",
            "When to use which",
        ],
        "subtopics": [
            {"name": "Physics engine", "description": "Automatic simulation", "examples": 1},
            {"name": "Anchored property", "description": "Freeze in place", "examples": 2},
            {"name": "AssemblyLinearVelocity", "description": "Direct velocity set", "examples": 2},
            {"name": "LinearVelocity", "description": "Continuous force", "examples": 2},
            {"name": "AlignPosition", "description": "Move to target", "examples": 2},
            {"name": "BodyVelocity (legacy)", "description": "Old but still works", "examples": 2},
        ],
        "common_mistakes": [
            "Fight physics engine",
            "Wrong attachment setup",
            "Performance with many",
        ],
        "real_world": "Flying, knockback, vehicles",
        "estimated_time": "40-45 minutes",
        "mini_project": "Simple flying system"
    },

    # ===== PHASE 4: EXPERT (37-45) =====
    {
        "n": 37,
        "title": "BindableEvents và Custom Signals",
        "phase": "Expert",
        "keywords": ["bindableEvent", "bindableFunction", "signal", "observer", "pubsub"],
        "difficulty": "Expert",
        "prerequisites": [20, 17],
        "learning_objectives": [
            "BindableEvents cho same-boundary",
            "Custom signal implementation",
            "Observer pattern",
            "Decoupled systems",
        ],
        "subtopics": [
            {"name": "BindableEvent", "description": "Same-boundary events", "examples": 2},
            {"name": "BindableFunction", "description": "Same-boundary functions", "examples": 2},
            {"name": "Custom signals", "description": "Build your own", "examples": 3},
            {"name": "Observer pattern", "description": "Decouple systems", "examples": 2},
            {"name": "Pub/sub pattern", "description": "Message broadcasting", "examples": 2},
        ],
        "common_mistakes": [
            "Use for cross-boundary",
            "Memory leaks in signals",
            "Circular dependencies",
        ],
        "real_world": "Game event system, modular code",
        "estimated_time": "35-40 minutes",
        "mini_project": "Build custom signal class"
    },
    {
        "n": 38,
        "title": "Pathfinding",
        "phase": "Expert",
        "keywords": ["pathfindingService", "path", "waypoint", "npc", "navigation"],
        "difficulty": "Expert",
        "prerequisites": [23, 34],
        "learning_objectives": [
            "PathfindingService basics",
            "Create và compute paths",
            "Follow waypoints",
            "Handle blocked paths",
        ],
        "subtopics": [
            {"name": "PathfindingService", "description": "NPC navigation", "examples": 1},
            {"name": "CreatePath()", "description": "Path configuration", "examples": 2},
            {"name": "ComputeAsync()", "description": "Calculate path", "examples": 2},
            {"name": "GetWaypoints()", "description": "Path points", "examples": 2},
            {"name": "Move along path", "description": "Humanoid:MoveTo", "examples": 2},
            {"name": "Blocked event", "description": "Recompute path", "examples": 2},
        ],
        "common_mistakes": [
            "No blocked handling",
            "Path on client",
            "Ignore path status",
        ],
        "real_world": "NPC AI, enemy following",
        "estimated_time": "45-50 minutes",
        "mini_project": "NPC that follows player"
    },
    {
        "n": 39,
        "title": "State Machines",
        "phase": "Expert",
        "keywords": ["state", "machine", "fsm", "transition", "pattern"],
        "difficulty": "Expert",
        "prerequisites": [34],
        "learning_objectives": [
            "State machine concept",
            "Implement FSM trong Lua",
            "State transitions",
            "Use cases",
        ],
        "subtopics": [
            {"name": "FSM là gì?", "description": "Finite State Machine", "examples": 2},
            {"name": "States", "description": "Possible conditions", "examples": 2},
            {"name": "Transitions", "description": "Moving between states", "examples": 2},
            {"name": "Lua implementation", "description": "Clean FSM code", "examples": 3},
            {"name": "State callbacks", "description": "Enter/Exit/Update", "examples": 2},
            {"name": "Enemy AI FSM", "description": "Practical example", "examples": 2},
        ],
        "common_mistakes": [
            "Invalid transitions",
            "State explosion",
            "No default state",
        ],
        "real_world": "AI behavior, game flow",
        "estimated_time": "45-50 minutes",
        "mini_project": "Enemy AI với state machine"
    },
    {
        "n": 40,
        "title": "Promise Pattern",
        "phase": "Expert",
        "keywords": ["promise", "async", "await", "then", "catch", "chain"],
        "difficulty": "Expert",
        "prerequisites": [16, 23],
        "learning_objectives": [
            "Promises là gì",
            "Roblox Promise library",
            "Chaining promises",
            "Error handling",
        ],
        "subtopics": [
            {"name": "Promises là gì?", "description": "Async value container", "examples": 2},
            {"name": "Promise.new()", "description": "Create promise", "examples": 2},
            {"name": ":andThen()", "description": "Chain operations", "examples": 2},
            {"name": ":catch()", "description": "Handle errors", "examples": 2},
            {"name": ":finally()", "description": "Always run", "examples": 2},
            {"name": "Promise.all()", "description": "Wait for multiple", "examples": 2},
        ],
        "common_mistakes": [
            "Forget error handling",
            "Nested promises",
            "Promise hell",
        ],
        "real_world": "Complex async flows",
        "estimated_time": "40-45 minutes",
        "mini_project": "Async data loading với promises"
    },
    {
        "n": 41,
        "title": "Component Pattern",
        "phase": "Expert",
        "keywords": ["component", "entity", "composition", "modular", "reusable"],
        "difficulty": "Expert",
        "prerequisites": [24, 34],
        "learning_objectives": [
            "Component-based design",
            "Composition over inheritance",
            "Reusable behaviors",
            "CollectionService + Components",
        ],
        "subtopics": [
            {"name": "Components là gì?", "description": "Reusable behaviors", "examples": 2},
            {"name": "Composition", "description": "Combine behaviors", "examples": 2},
            {"name": "Component lifecycle", "description": "Init/Start/Destroy", "examples": 2},
            {"name": "Tag-based components", "description": "CollectionService", "examples": 2},
            {"name": "Component framework", "description": "Build your own", "examples": 3},
        ],
        "common_mistakes": [
            "Components too coupled",
            "No cleanup",
            "Heavy init",
        ],
        "real_world": "Modular game objects",
        "estimated_time": "45-50 minutes",
        "mini_project": "Build component system"
    },
    {
        "n": 42,
        "title": "Performance Optimization",
        "phase": "Expert",
        "keywords": ["performance", "optimize", "micro profiler", "memory", "gc"],
        "difficulty": "Expert",
        "prerequisites": [23, 34],
        "learning_objectives": [
            "Profile game performance",
            "Common bottlenecks",
            "Memory optimization",
            "Code optimization",
        ],
        "subtopics": [
            {"name": "MicroProfiler", "description": "Debug performance", "examples": 2},
            {"name": "Script profiler", "description": "Find slow code", "examples": 2},
            {"name": "Memory usage", "description": "Reduce allocations", "examples": 2},
            {"name": "Object pooling", "description": "Reuse instances", "examples": 2},
            {"name": "Spatial optimization", "description": "Only update nearby", "examples": 2},
            {"name": "Common mistakes", "description": "Performance killers", "examples": 2},
        ],
        "common_mistakes": [
            "Premature optimization",
            "Not profiling first",
            "Optimize wrong things",
        ],
        "real_world": "Smooth gameplay at scale",
        "estimated_time": "45-50 minutes",
        "mini_project": "Optimize a slow system"
    },
    {
        "n": 43,
        "title": "Testing và Debugging",
        "phase": "Expert",
        "keywords": ["test", "debug", "unit test", "integration", "mock"],
        "difficulty": "Expert",
        "prerequisites": [16, 17],
        "learning_objectives": [
            "Testing importance",
            "Unit tests trong Lua",
            "Debug strategies",
            "Logging best practices",
        ],
        "subtopics": [
            {"name": "Tại sao test?", "description": "Catch bugs early", "examples": 1},
            {"name": "Unit testing", "description": "Test functions", "examples": 2},
            {"name": "Test framework", "description": "Simple test runner", "examples": 2},
            {"name": "Mocking", "description": "Fake dependencies", "examples": 2},
            {"name": "Debug strategies", "description": "Find bugs efficiently", "examples": 2},
            {"name": "Logging", "description": "Good log practices", "examples": 2},
        ],
        "common_mistakes": [
            "No tests at all",
            "Test implementation, not behavior",
            "Too many mocks",
        ],
        "real_world": "Professional development",
        "estimated_time": "40-45 minutes",
        "mini_project": "Add tests to a system"
    },
    {
        "n": 44,
        "title": "Security Deep Dive",
        "phase": "Expert",
        "keywords": ["security", "exploit", "anticheat", "validate", "server authority"],
        "difficulty": "Expert",
        "prerequisites": [27, 30],
        "learning_objectives": [
            "Advanced security patterns",
            "Anti-exploit techniques",
            "Server authority model",
            "Security audit checklist",
        ],
        "subtopics": [
            {"name": "Attack vectors", "description": "How exploiters attack", "examples": 2},
            {"name": "Server authority", "description": "Server decides everything", "examples": 2},
            {"name": "Sanity checks", "description": "Validate everything", "examples": 3},
            {"name": "Rate limiting", "description": "Prevent spam", "examples": 2},
            {"name": "Anti-exploit patterns", "description": "Common defenses", "examples": 2},
            {"name": "Security audit", "description": "Checklist", "examples": 2},
        ],
        "common_mistakes": [
            "Security by obscurity",
            "Client-side validation only",
            "Trust client timing",
        ],
        "real_world": "Hack-proof games",
        "estimated_time": "50-55 minutes",
        "mini_project": "Security audit một game system"
    },
    {
        "n": 45,
        "title": "Architecture và Clean Code",
        "phase": "Expert",
        "keywords": ["architecture", "clean code", "solid", "patterns", "maintainable"],
        "difficulty": "Expert",
        "prerequisites": [17, 34, 41],
        "learning_objectives": [
            "Game architecture patterns",
            "Clean code principles",
            "SOLID trong Lua",
            "Maintainable codebase",
        ],
        "subtopics": [
            {"name": "Architecture patterns", "description": "MVC, ECS, etc.", "examples": 2},
            {"name": "Clean code", "description": "Readable, maintainable", "examples": 2},
            {"name": "SOLID principles", "description": "Applied to Lua", "examples": 2},
            {"name": "Naming conventions", "description": "Consistent naming", "examples": 2},
            {"name": "Code organization", "description": "Folder structure", "examples": 2},
            {"name": "Documentation", "description": "Comments, types", "examples": 2},
        ],
        "common_mistakes": [
            "Over-engineering",
            "Inconsistent style",
            "God objects",
        ],
        "real_world": "Large-scale game development",
        "estimated_time": "45-50 minutes",
        "mini_project": "Refactor codebase với patterns"
    },

    # ===== PHASE 5: MASTERY (46-50) =====
    {
        "n": 46,
        "title": "Project: Combat System",
        "phase": "Mastery",
        "keywords": ["combat", "damage", "hitbox", "combo", "blocking"],
        "difficulty": "Master Project",
        "prerequisites": [35, 33, 39],
        "learning_objectives": [
            "Design combat architecture",
            "Implement hitbox detection",
            "Combo system",
            "Networking combat",
        ],
        "subtopics": [
            {"name": "Combat design", "description": "Plan the system", "examples": 1},
            {"name": "Hitbox detection", "description": "Damage regions", "examples": 2},
            {"name": "Combo system", "description": "Chain attacks", "examples": 2},
            {"name": "Blocking/Parry", "description": "Defense mechanics", "examples": 2},
            {"name": "Network sync", "description": "Multiplayer combat", "examples": 2},
            {"name": "Effects/Feedback", "description": "Visual/audio", "examples": 2},
        ],
        "is_project": True,
        "project_requirements": [
            "Melee attack with hitbox",
            "3-hit combo system",
            "Block ability",
            "Damage numbers UI",
            "Works in multiplayer"
        ],
        "estimated_time": "2-3 hours",
    },
    {
        "n": 47,
        "title": "Project: Inventory System",
        "phase": "Mastery",
        "keywords": ["inventory", "item", "stack", "equip", "persistence"],
        "difficulty": "Master Project",
        "prerequisites": [30, 32, 34],
        "learning_objectives": [
            "Inventory data structure",
            "Item management",
            "UI integration",
            "Data persistence",
        ],
        "subtopics": [
            {"name": "Inventory design", "description": "Slots, stacks", "examples": 1},
            {"name": "Item system", "description": "Item definitions", "examples": 2},
            {"name": "Add/remove items", "description": "Core operations", "examples": 2},
            {"name": "Stack management", "description": "Stackable items", "examples": 2},
            {"name": "UI grid", "description": "Visual inventory", "examples": 2},
            {"name": "Save/load", "description": "Persist inventory", "examples": 2},
        ],
        "is_project": True,
        "project_requirements": [
            "Grid-based inventory UI",
            "Add/remove/stack items",
            "Drag and drop",
            "Item tooltips",
            "Saves to DataStore"
        ],
        "estimated_time": "2-3 hours",
    },
    {
        "n": 48,
        "title": "Project: Enemy AI System",
        "phase": "Mastery",
        "keywords": ["ai", "enemy", "patrol", "chase", "attack"],
        "difficulty": "Master Project",
        "prerequisites": [38, 39, 41],
        "learning_objectives": [
            "AI behavior design",
            "State machine for AI",
            "Pathfinding integration",
            "Combat AI",
        ],
        "subtopics": [
            {"name": "AI design", "description": "Behavior patterns", "examples": 1},
            {"name": "State machine AI", "description": "Idle/Patrol/Chase/Attack", "examples": 2},
            {"name": "Pathfinding", "description": "Navigate to target", "examples": 2},
            {"name": "Combat behavior", "description": "Attack patterns", "examples": 2},
            {"name": "Spawn system", "description": "Wave spawning", "examples": 2},
            {"name": "Difficulty scaling", "description": "Adjust AI", "examples": 1},
        ],
        "is_project": True,
        "project_requirements": [
            "Multiple enemy types",
            "Patrol behavior",
            "Chase player when spotted",
            "Attack with cooldowns",
            "Death and respawn"
        ],
        "estimated_time": "3-4 hours",
    },
    {
        "n": 49,
        "title": "Project: Multiplayer Game Framework",
        "phase": "Mastery",
        "keywords": ["framework", "multiplayer", "lobby", "matchmaking", "round"],
        "difficulty": "Master Project",
        "prerequisites": [27, 44, 45],
        "learning_objectives": [
            "Game framework design",
            "Lobby/matchmaking",
            "Round-based gameplay",
            "Secure architecture",
        ],
        "subtopics": [
            {"name": "Framework design", "description": "Core systems", "examples": 1},
            {"name": "Lobby system", "description": "Waiting area", "examples": 2},
            {"name": "Round manager", "description": "Game flow", "examples": 2},
            {"name": "Team system", "description": "Assign teams", "examples": 2},
            {"name": "Score/Leaderboard", "description": "Track scores", "examples": 2},
            {"name": "Anti-exploit", "description": "Secure everything", "examples": 2},
        ],
        "is_project": True,
        "project_requirements": [
            "Lobby with player list",
            "Vote to start",
            "Round timer",
            "Team assignment",
            "Win condition",
            "End-of-round stats"
        ],
        "estimated_time": "4-5 hours",
    },
    {
        "n": 50,
        "title": "FINAL: Build Your Own Game",
        "phase": "Graduation",
        "keywords": ["game", "complete", "publish", "polish", "final"],
        "difficulty": "Graduation Project",
        "prerequisites": list(range(1, 50)),
        "learning_objectives": [
            "Apply everything learned",
            "Complete game development",
            "Polish and publish",
            "You are now a Roblox developer!",
        ],
        "subtopics": [
            {"name": "Game concept", "description": "Design your game", "examples": 0},
            {"name": "Core mechanics", "description": "Main gameplay", "examples": 0},
            {"name": "All systems", "description": "UI, Data, Combat, etc.", "examples": 0},
            {"name": "Polish", "description": "Effects, sounds, feel", "examples": 0},
            {"name": "Testing", "description": "Bug fixing", "examples": 0},
            {"name": "Publish", "description": "Release to Roblox", "examples": 0},
        ],
        "is_project": True,
        "is_final": True,
        "project_requirements": [
            "Original game concept",
            "At least 3 core systems",
            "Complete UI",
            "Data persistence",
            "Multiplayer support",
            "Published to Roblox"
        ],
        "estimated_time": "1-2 weeks",
    },
]

# -----------------------------
# Helper Functions
# -----------------------------
def get_lesson(n: int) -> Optional[dict]:
    for l in LESSONS:
        if l["n"] == n:
            return l
    return None


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def looks_like_coding_request(text: str) -> bool:
    t = (text or "").lower()
    if "```" in t:
        return True
    coding_keywords = [
        "lua", "luau", "script", "code", "function", "local", "table",
        "error", "bug", "fix", "debug", "refactor", "optimize",
    ]
    return any(k in t for k in coding_keywords)


def extract_json(text: str) -> Optional[dict]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except:
        return None


# List of ALL text commands - bypass AI relevance check
TEXT_COMMANDS = {
    "start", "start lesson", "repeat", "repeat lesson", "next", "next lesson",
    "hint", "get hint", "help", "cheat sheet", "cheatsheet", "reference",
    "my progress", "progress", "stats", "bookmark", "save", "bookmarks",
    "my bookmarks", "practice", "exercises", "skip", "next question",
    "refresh panel", "panel", "switch to coder", "model coder",
    "switch to explain", "model explain", "switch to auto", "model auto",
    "no", "nope", "nah", "n", "quiz", "start quiz", "final test",
    "weakness analysis", "analyze", "my weaknesses"
}


# -----------------------------
# OpenRouter Chat with Model Pool Support
# -----------------------------
async def openrouter_chat(
    messages: list,
    *,
    model_pool: Optional[List[str]] = None,
    max_tokens: int = 1500,
    temperature: float = 0.6,
    retries: int = 4,
) -> str:
    """
    OpenRouter chat with model pool support.
    model_pool: which models to try (CODER_MODELS, EXPLAIN_MODELS, or ALL_MODELS)
    """
    if not OPENROUTER_API_KEY:
        return "OpenRouter API key is missing."

    # Default to all models
    model_pool = model_pool or ALL_MODELS

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Studio-bot Learn Tutor",
    }

    backoff = 2
    last_err = "Unknown error"
    tried_models = set()

    async with aiohttp.ClientSession() as session:
        for attempt in range(1, retries + 1):
            # Pick a model we haven't tried yet
            available = [m for m in model_pool if m not in tried_models]
            if not available:
                tried_models.clear()
                available = model_pool

            model = random.choice(available)
            tried_models.add(model)

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            try:
                async with session.post(url, headers=headers, json=payload, timeout=90) as resp:
                    data = await resp.json()

                    if resp.status == 200:
                        return data["choices"][0]["message"]["content"]

                    if resp.status == 429:
                        last_err = f"Rate limited on {model}"
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, 15)
                        continue

                    last_err = f"Error {resp.status}: {str(data)[:200]}"

            except asyncio.TimeoutError:
                last_err = f"Timeout on {model}"
            except Exception as e:
                last_err = f"Exception: {str(e)[:200]}"

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 15)

    return f"⚠️ AI temporarily unavailable. Try again.\n_(Debug: {last_err})_"


def get_model_pool(mode: str, text: str = "") -> List[str]:
    """Get appropriate model pool based on mode and content"""
    if mode == "coder":
        return CODER_MODELS
    elif mode == "explain":
        return EXPLAIN_MODELS
    elif mode == "auto":
        if looks_like_coding_request(text):
            return CODER_MODELS
        return EXPLAIN_MODELS
    return ALL_MODELS


# -----------------------------
# Persistent Storage Helpers
# -----------------------------
def _safe_int(x, default=1) -> int:
    try:
        return int(x)
    except:
        return default


async def ensure_learn_fields(user_id: int, username: str):
    user = await UserProfile.get_user(user_id)
    if not user:
        await UserProfile.create_user(user_id, username)
        user = await UserProfile.get_user(user_id)

    defaults = {}
    default_fields = {
        "learn_lesson": 1,
        "learn_phase": "menu",
        "learn_model_mode": "auto",
        "learn_quiz_data": {},
        "learn_conversation": [],
        "learn_panel_message_id": None,
        "learn_channel_id": None,
        "learn_completed_lessons": [],
        "learn_quiz_scores": {},
        "learn_hints_used": 0,
        "learn_total_questions": 0,
        "learn_correct_answers": 0,
        "learn_bookmarks": [],
        "learn_notes": {},
        "learn_streak": 0,
        "learn_last_activity": None,
        "learn_quiz_attempts": 0,
        "learn_weak_topics": {},
        "learn_strong_topics": {},
        "learn_question_history": [],
        # NEW: Full quiz state fields
        "learn_quiz_questions": [],
        "learn_current_quiz_index": 0,
        "learn_hints_remaining": 3,
        "learn_lesson_part": 0,
    }

    for key, val in default_fields.items():
        if key not in user:
            defaults[key] = val

    if defaults:
        await UserProfile.update_user(user_id, defaults)
        user.update(defaults)

    return user


# =====================================================
# CRITICAL: SAVE ALL SESSION STATE FUNCTION
# =====================================================
async def save_session_state(session: "LearnSession"):
    """
    Save ALL session state to database.
    MUST be called whenever session.* is changed!
    """
    await UserProfile.update_user(session.user_id, {
        "learn_lesson": session.lesson_number,
        "learn_phase": session.phase,
        "learn_model_mode": session.model_mode,
        "learn_quiz_data": session.quiz_data,
        "learn_quiz_questions": session.quiz_questions,
        "learn_current_quiz_index": session.current_quiz_index,
        "learn_hints_remaining": session.hints_remaining,
        "learn_lesson_part": session.lesson_part,
    })


async def append_conversation(user_id: int, role: str, content: str):
    user = await UserProfile.get_user(user_id)
    if not user:
        return
    conv = user.get("learn_conversation", [])
    conv.append({
        "ts": discord.utils.utcnow().isoformat(),
        "role": role,
        "content": content[:2000],
    })
    if len(conv) > MAX_CONVERSATION_MESSAGES:
        conv = conv[-MAX_CONVERSATION_MESSAGES:]
    await UserProfile.update_user(user_id, {"learn_conversation": conv})


async def track_weakness(user_id: int, keywords: List[str], is_correct: bool):
    """Track topics user is weak/strong at"""
    user = await UserProfile.get_user(user_id)
    if not user:
        return

    weak = user.get("learn_weak_topics", {})
    strong = user.get("learn_strong_topics", {})

    for kw in keywords:
        kw = kw.lower()
        if is_correct:
            strong[kw] = strong.get(kw, 0) + 1
            if kw in weak and weak[kw] > 0:
                weak[kw] -= 1
        else:
            weak[kw] = weak.get(kw, 0) + 1

    await UserProfile.update_user(user_id, {
        "learn_weak_topics": weak,
        "learn_strong_topics": strong,
    })


async def get_weakness_analysis(user_id: int) -> dict:
    user = await UserProfile.get_user(user_id)
    if not user:
        return {"weaknesses": [], "strengths": []}

    weak = user.get("learn_weak_topics", {})
    strong = user.get("learn_strong_topics", {})

    weaknesses = sorted(weak.items(), key=lambda x: x[1], reverse=True)[:10]
    strengths = sorted(strong.items(), key=lambda x: x[1], reverse=True)[:10]

    return {"weaknesses": weaknesses, "strengths": strengths}


async def update_streak(user_id: int):
    user = await UserProfile.get_user(user_id)
    if not user:
        return

    last_activity = user.get("learn_last_activity")
    streak = user.get("learn_streak", 0)
    now = datetime.utcnow()

    if last_activity:
        try:
            last_date = datetime.fromisoformat(last_activity).date()
            today = now.date()
            diff = (today - last_date).days

            if diff == 1:
                streak += 1
            elif diff > 1:
                streak = 1
        except:
            streak = 1
    else:
        streak = 1

    await UserProfile.update_user(user_id, {
        "learn_streak": streak,
        "learn_last_activity": now.isoformat()
    })


async def get_progress_stats(user_id: int) -> dict:
    user = await UserProfile.get_user(user_id)
    if not user:
        return {}

    completed = user.get("learn_completed_lessons", [])
    total_q = user.get("learn_total_questions", 0)
    correct = user.get("learn_correct_answers", 0)
    hints = user.get("learn_hints_used", 0)
    streak = user.get("learn_streak", 0)
    current_lesson = user.get("learn_lesson", 1)

    accuracy = (correct / total_q * 100) if total_q > 0 else 0
    progress_pct = len(completed) / max(len(LESSONS), 1) * 100

    current = get_lesson(current_lesson)
    phase = current.get("phase", "Fundamentals") if current else "Fundamentals"

    return {
        "current_lesson": current_lesson,
        "current_phase": phase,
        "completed_count": len(completed),
        "total_lessons": len(LESSONS),
        "progress_percent": round(progress_pct, 1),
        "total_questions": total_q,
        "correct_answers": correct,
        "accuracy": round(accuracy, 1),
        "hints_used": hints,
        "streak": streak
    }


# -----------------------------
# Session Dataclass
# -----------------------------
@dataclass
class LearnSession:
    guild_id: int
    channel_id: int
    user_id: int
    lesson_number: int = 1
    phase: str = "menu"
    quiz_data: dict = field(default_factory=dict)
    model_mode: str = "auto"
    quiz_questions: List[dict] = field(default_factory=list)
    current_quiz_index: int = 0
    hints_remaining: int = 3
    lesson_part: int = 0


SESSIONS: Dict[int, LearnSession] = {}


async def rebuild_session_from_db(channel: discord.TextChannel, user_id: int) -> LearnSession:
    """Rebuild session from database - critical for persistence!"""
    user = await ensure_learn_fields(user_id, "Unknown")

    lesson = max(1, min(_safe_int(user.get("learn_lesson", 1)), len(LESSONS) or 50))

    phase = str(user.get("learn_phase", "menu"))
    if phase not in {"menu", "qna", "quiz", "practice", "final_test"}:
        phase = "menu"

    mode = str(user.get("learn_model_mode", "auto"))
    if mode not in {"auto", "coder", "explain"}:
        mode = "auto"

    quiz_data = user.get("learn_quiz_data", {}) or {}
    quiz_questions = user.get("learn_quiz_questions", []) or []
    current_quiz_index = _safe_int(user.get("learn_current_quiz_index", 0), 0)
    hints_remaining = _safe_int(user.get("learn_hints_remaining", 3), 3)
    lesson_part = _safe_int(user.get("learn_lesson_part", 0), 0)

    session = LearnSession(
        guild_id=channel.guild.id,
        channel_id=channel.id,
        user_id=user_id,
        lesson_number=lesson,
        phase=phase,
        quiz_data=quiz_data,
        model_mode=mode,
        quiz_questions=quiz_questions,
        current_quiz_index=current_quiz_index,
        hints_remaining=hints_remaining,
        lesson_part=lesson_part,
    )
    SESSIONS[channel.id] = session
    return session


# -----------------------------
# PERSISTENT VIEWS (timeout=None + rebuild from DB)
# -----------------------------

class LearnPersistentPanel(discord.ui.View):
    """Main control panel - persists across restarts"""

    def __init__(self, cog: "LearnCog"):
        super().__init__(timeout=None)
        self.cog = cog

    def _is_controller(self, interaction: discord.Interaction, session: LearnSession) -> bool:
        return interaction.user.id == session.user_id or interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Start Lesson", style=discord.ButtonStyle.success, emoji="▶️", custom_id="learn:start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("Not allowed.", ephemeral=True)
        await self.cog.send_lesson(interaction.channel, session, repeat=False)

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="learn:repeat")
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("Not allowed.", ephemeral=True)
        await self.cog.send_lesson(interaction.channel, session, repeat=True)

    @discord.ui.button(label="Next Lesson", style=discord.ButtonStyle.blurple, emoji="⏭️", custom_id="learn:next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("Not allowed.", ephemeral=True)

        if session.lesson_number >= len(LESSONS):
            return await interaction.followup.send("🎉 All done! Type `final test`!")

        session.lesson_number += 1
        session.phase = "menu"
        session.quiz_data = {}
        session.quiz_questions = []
        session.current_quiz_index = 0
        session.hints_remaining = 3

        await save_session_state(session)

        lesson = get_lesson(session.lesson_number)
        await interaction.followup.send(
            f"📖 **Lesson {session.lesson_number}: {lesson['title']}**\n"
            f"Click **Start Lesson** to begin!"
        )

    @discord.ui.button(label="Progress", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="learn:progress")
    async def progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        session = await self.cog.get_or_rebuild_session(interaction)
        stats = await get_progress_stats(session.user_id)
        weakness = await get_weakness_analysis(session.user_id)

        filled = int(stats.get("progress_percent", 0) / 10)
        bar = "█" * filled + "░" * (10 - filled)

        weak_text = ", ".join([f"{k}({v})" for k, v in weakness["weaknesses"][:5]]) or "None"
        strong_text = ", ".join([f"{k}({v})" for k, v in weakness["strengths"][:5]]) or "None"

        embed = discord.Embed(title="📊 Progress", color=BOT_COLOR)
        embed.add_field(name="Progress", value=f"[{bar}] {stats['progress_percent']}%", inline=False)
        embed.add_field(name="Lessons", value=f"{stats['completed_count']}/{stats['total_lessons']}", inline=True)
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} days", inline=True)
        embed.add_field(name="Accuracy", value=f"{stats['accuracy']}%", inline=True)
        embed.add_field(name="⚠️ Weak", value=weak_text, inline=False)
        embed.add_field(name="💪 Strong", value=strong_text, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="End", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="learn:end")
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("Not allowed.", ephemeral=True)

        SESSIONS.pop(session.channel_id, None)
        session.phase = "menu"
        await save_session_state(session)
        await interaction.followup.send("Session ended.", ephemeral=True)


class QuizControlView(discord.ui.View):
    """
    Quiz control buttons - PERSISTENT across restarts.
    Always rebuilds session from DB, doesn't rely on RAM.
    """

    def __init__(self, cog: "LearnCog", session: LearnSession = None):
        super().__init__(timeout=None)  # CRITICAL: timeout=None for persistence
        self.cog = cog
        self.session = session  # Optional, only for same-runtime convenience

    @discord.ui.button(label="Hint", style=discord.ButtonStyle.secondary, emoji="💡", custom_id="quiz:hint_btn")
    async def get_hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # ALWAYS rebuild session from DB
        session = await self.cog.get_or_rebuild_session(interaction)

        if session.phase not in {"quiz", "final_test"}:
            return await interaction.followup.send("💡 Hints only available during quizzes.", ephemeral=True)

        if session.hints_remaining <= 0:
            return await interaction.followup.send("❌ No hints remaining!", ephemeral=True)

        session.hints_remaining -= 1

        # Update hints used in profile
        user = await UserProfile.get_user(session.user_id)
        await UserProfile.update_user(session.user_id, {
            "learn_hints_used": user.get("learn_hints_used", 0) + 1
        })

        # Save session state
        await save_session_state(session)

        lesson = get_lesson(session.lesson_number)
        hint = await self.cog.generate_hint(lesson, session.quiz_data)

        embed = discord.Embed(title="💡 Hint", description=hint, color=discord.Color.gold())
        embed.set_footer(text=f"Hints remaining: {session.hints_remaining}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="quiz:skip_btn")
    async def skip_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        # ALWAYS rebuild session from DB
        session = await self.cog.get_or_rebuild_session(interaction)

        if session.phase not in {"quiz", "final_test"}:
            return await interaction.followup.send("⏭️ Skip only available during quizzes.", ephemeral=True)

        await self.cog.handle_quiz_skip(interaction.channel, session)


# -----------------------------
# Learn Cog
# -----------------------------
class LearnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_or_rebuild_session(self, interaction: discord.Interaction) -> LearnSession:
        """Get session from RAM or rebuild from DB"""
        ch = interaction.channel
        if not isinstance(ch, discord.TextChannel):
            raise RuntimeError("Learn only works in text channels.")

        if ch.id in SESSIONS:
            return SESSIONS[ch.id]

        if not ch.name.startswith("learn-"):
            session = LearnSession(guild_id=ch.guild.id, channel_id=ch.id, user_id=interaction.user.id)
            SESSIONS[ch.id] = session
            return session

        try:
            owner_id = int(ch.name.split("learn-", 1)[1])
        except:
            owner_id = interaction.user.id

        return await rebuild_session_from_db(ch, owner_id)

    async def send_panel(self, channel: discord.TextChannel, user_id: int):
        user = await ensure_learn_fields(user_id, "Unknown")
        lesson_number = _safe_int(user.get("learn_lesson", 1))
        lesson_number = max(1, min(lesson_number, len(LESSONS) or 50))

        lesson = get_lesson(lesson_number)
        stats = await get_progress_stats(user_id)

        bar = "█" * int(stats['progress_percent'] / 10) + "░" * (10 - int(stats['progress_percent'] / 10))

        embed = discord.Embed(
            title="📚 Learning Control Panel",
            description=(
                f"**Progress:** [{bar}] {stats['progress_percent']}%\n"
                f"**Streak:** 🔥 {stats['streak']} days | **Accuracy:** {stats['accuracy']}%\n\n"
                "**Commands:**\n"
                "• `start lesson` / `next lesson` / `repeat lesson`\n"
                "• `hint` - Get quiz hint\n"
                "• `my progress` / `my weaknesses`\n"
                "• `review <number>` - Review specific lesson\n"
                "• `cheat sheet` / `practice`\n"
                "• `final test` - Graduation exam (45+ lessons)\n"
            ),
            color=BOT_COLOR
        )
        if lesson:
            embed.add_field(
                name=f"📖 Lesson {lesson_number}/{len(LESSONS)}",
                value=f"**{lesson['title']}**\n{lesson.get('phase', '')} | {lesson.get('difficulty', '')}",
                inline=False
            )

        msg = await channel.send(embed=embed, view=LearnPersistentPanel(self))
        await UserProfile.update_user(user_id, {"learn_panel_message_id": msg.id})

    # =====================================================
    # LESSON SENDING - MULTI-PART
    # =====================================================

    async def send_lesson(self, channel: discord.TextChannel, session: LearnSession, repeat: bool = False):
        """Send comprehensive multi-part lesson"""
        lesson = get_lesson(session.lesson_number)
        if not lesson:
            return await channel.send("Lesson not found.")

        # Reset session state
        session.phase = "qna"
        session.quiz_data = {}
        session.quiz_questions = []
        session.current_quiz_index = 0
        session.hints_remaining = 3
        session.lesson_part = 0

        # SAVE STATE
        await save_session_state(session)
        await update_streak(session.user_id)

        # Project lesson?
        if lesson.get("is_project"):
            await self.send_project_lesson(channel, session, lesson)
            return

        # Header
        title = f"📖 Lesson {lesson['n']}: {lesson['title']}"
        if repeat:
            title = f"🔁 {title}"

        header_embed = discord.Embed(
            title=title,
            description=(
                f"**Phase:** {lesson.get('phase', 'N/A')} | "
                f"**Difficulty:** {lesson.get('difficulty', 'N/A')} | "
                f"**Time:** {lesson.get('estimated_time', 'N/A')}\n\n"
                f"**🎯 What You'll Learn:**\n" +
                "\n".join([f"✓ {obj}" for obj in lesson.get('learning_objectives', [])[:6]])
            ),
            color=BOT_COLOR
        )
        await channel.send(embed=header_embed)
        await channel.send("📚 **Loading lesson...**")

        # Part 1: Introduction
        await self._send_lesson_introduction(channel, session, lesson)
        await asyncio.sleep(1)

        # Part 2+: Subtopics
        subtopics = lesson.get("subtopics", [])
        chunk_size = 2
        for i in range(0, len(subtopics), chunk_size):
            chunk = subtopics[i:i + chunk_size]
            part_num = (i // chunk_size) + 2
            await self._send_lesson_subtopics(channel, session, lesson, chunk, part_num)
            await asyncio.sleep(1)

        # Final: Conclusion
        await self._send_lesson_conclusion(channel, session, lesson)

        await append_conversation(session.user_id, "assistant", f"{title} - Lesson delivered")

        # Q&A Prompt
        qna_embed = discord.Embed(
            title="🤔 Questions?",
            description=(
                "**Ask anything about this lesson or previous lessons!**\n\n"
                "• Type your question\n"
                "• Type `no` or `quiz` to start the quiz\n"
                "• Type `cheat sheet` for quick reference\n"
            ),
            color=discord.Color.blue()
        )
        await channel.send(embed=qna_embed)

    async def _send_lesson_introduction(self, channel: discord.TextChannel, session: LearnSession, lesson: dict):
        """Part 1: Introduction"""
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        system = """You are an expert Roblox Lua/Luau teacher.
Write a COMPREHENSIVE introduction:

## 🎯 HOOK
Engaging question or scenario

## 📚 WHAT IS IT? (3-4 paragraphs)
Define for complete beginners with analogies

## 🤔 WHY IMPORTANT? (2 paragraphs)
Why every developer needs this

## 🎮 REAL GAME EXAMPLES
How do popular games use this?

## ✨ AFTER THIS LESSON YOU CAN:
4-5 things they can build

Make it EXCITING!"""

        user = f"""Introduction for Lesson {lesson['n']}: {lesson['title']}
Keywords: {', '.join(lesson['keywords'])}
Real-world: {lesson.get('real_world', '')}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                model_pool=model_pool,
                max_tokens=1800,
            )

        await append_conversation(session.user_id, "assistant", f"INTRO: {content[:1500]}")

        parts = self._split_content(content, 3900)
        for i, part in enumerate(parts):
            embed = discord.Embed(
                title="📚 Part 1: Introduction" if i == 0 else "📚 Part 1 (continued)",
                description=part,
                color=discord.Color.dark_blue()
            )
            await channel.send(embed=embed)

    async def _send_lesson_subtopics(self, channel: discord.TextChannel, session: LearnSession, lesson: dict, subtopics: list, part_num: int):
        """Part 2+: Subtopics"""
        if not subtopics:
            return

        model_pool = get_model_pool(session.model_mode, lesson['title'])

        subtopics_text = ""
        for st in subtopics:
            subtopics_text += f"""
### SUBTOPIC: {st['name']}
Description: {st['description']}
Required examples: {st['examples']}

MUST include:
1. Detailed explanation (6-8 sentences)
2. {st['examples']} code examples with comments on EVERY line
3. When to use this
4. Common mistakes
"""

        system = """You are an expert Roblox Lua/Luau teacher.
Explain each subtopic thoroughly:
- Beginner-friendly with analogies
- EVERY code line needs a comment
- Real Roblox game examples
- Use ```lua blocks"""

        user = f"""Subtopics from Lesson {lesson['n']}: {lesson['title']}
{subtopics_text}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                model_pool=model_pool,
                max_tokens=2500,
            )

        await append_conversation(session.user_id, "assistant", f"SUBTOPICS Part {part_num}: {content[:1500]}")

        parts = self._split_content(content, 3900)
        for i, part in enumerate(parts):
            embed = discord.Embed(
                title=f"📖 Part {part_num}: Core Concepts" if i == 0 else f"📖 Part {part_num} (continued)",
                description=part,
                color=BOT_COLOR
            )
            await channel.send(embed=embed)

    async def _send_lesson_conclusion(self, channel: discord.TextChannel, session: LearnSession, lesson: dict):
        """Final Part: Mistakes, Tips, Project, Summary"""
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        mistakes = lesson.get("common_mistakes", [])
        mistakes_text = "\n".join([f"• {m}" for m in mistakes])

        system = """You are an expert teacher finishing a lesson.

## ⚠️ COMMON MISTAKES
For each: show WRONG code, explain, show CORRECT code

## 💡 PRO TIPS (5-6)
Each with short code example

## 🔧 MINI PROJECT
Uses all concepts. Include starter code.

## 📝 SUMMARY
6-8 bullet points + quick reference"""

        user = f"""Finish Lesson {lesson['n']}: {lesson['title']}
Mistakes: {mistakes_text}
Mini project: {lesson.get('mini_project', 'Practice exercise')}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                model_pool=model_pool,
                max_tokens=2500,
            )

        await append_conversation(session.user_id, "assistant", f"CONCLUSION: {content[:1500]}")

        parts = self._split_content(content, 3900)
        for i, part in enumerate(parts):
            embed = discord.Embed(
                title="⚠️ Mistakes, Tips & Practice" if i == 0 else "⚠️ (continued)",
                description=part,
                color=discord.Color.orange()
            )
            await channel.send(embed=embed)

    async def send_project_lesson(self, channel: discord.TextChannel, session: LearnSession, lesson: dict):
        """Project-based lesson"""
        requirements = "\n".join([f"✅ {req}" for req in lesson.get("project_requirements", [])])

        is_final = lesson.get("is_final", False)
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        if is_final:
            weakness = await get_weakness_analysis(session.user_id)
            stats = await get_progress_stats(session.user_id)
            weak_text = ", ".join([k for k, v in weakness["weaknesses"][:5]]) or "None"

            system = """Guide student through FINAL GRADUATION PROJECT.
Include: celebration, personalized analysis, game design guide, code architecture, publishing tips."""

            user = f"""Final project for student:
Stats: {stats['completed_count']} lessons, {stats['accuracy']}% accuracy
Weak areas: {weak_text}
Requirements: {requirements}"""
        else:
            system = """Guide through practical project with step-by-step code."""
            user = f"""Project: {lesson['title']}\nRequirements: {requirements}"""

        await channel.send("🔨 **Generating project guide...**")

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                model_pool=model_pool,
                max_tokens=3500,
            )

        await append_conversation(session.user_id, "assistant", f"PROJECT: {content[:1500]}")

        parts = self._split_content(content, 3900)
        for part in parts:
            embed = discord.Embed(
                title=f"🔨 {'🎓 GRADUATION ' if is_final else ''}Project",
                description=part,
                color=discord.Color.gold() if is_final else BOT_COLOR
            )
            await channel.send(embed=embed)

        session.phase = "quiz"
        await save_session_state(session)

        await channel.send("📋 **When done, describe what you built!**\nType `skip` to continue.")

    def _split_content(self, content: str, max_length: int) -> List[str]:
        """Split content preserving code blocks"""
        if len(content) <= max_length:
            return [content]

        parts = []
        current = ""
        in_code = False

        for line in content.split("\n"):
            if line.strip().startswith("```"):
                in_code = not in_code

            if len(current) + len(line) + 1 > max_length:
                if in_code:
                    current += "\n```"
                parts.append(current.strip())
                current = "```lua\n" if in_code else ""

            current += line + "\n"

        if current.strip():
            parts.append(current.strip())

        return parts or [content[:max_length]]

    # =====================================================
    # AI METHODS
    # =====================================================

    async def generate_hint(self, lesson: dict, quiz: dict) -> str:
        system = "Give a helpful hint WITHOUT revealing answer. 2-3 sentences."
        user = f"Quiz: {quiz.get('question', '')}\nAnswer: {quiz.get('answer', '')}"

        return await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=200,
        )

    async def generate_quiz(self, session: LearnSession, num_questions: int = 3) -> List[dict]:
        lesson = get_lesson(session.lesson_number)
        weakness = await get_weakness_analysis(session.user_id)
        weak_topics = [k for k, v in weakness["weaknesses"][:5]]

        system = "Create quiz. Return ONLY valid JSON array."
        user = f"""Create {num_questions} questions for Lesson {lesson['n']}: {lesson['title']}
Keywords: {', '.join(lesson['keywords'])}
{"Weak areas: " + ', '.join(weak_topics) if weak_topics else ""}

Return: [{{"question": "...", "type": "output/fix/concept/choice", "options": null or [...], "answer": "...", "explanation": "...", "difficulty": "easy/medium/hard", "related_keywords": [...]}}]"""

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=2000,
        )

        try:
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                questions = json.loads(match.group(0))
                if isinstance(questions, list) and questions:
                    return questions
        except:
            pass

        return [{"question": f"Explain {lesson['title']}.", "type": "concept", "answer": "", "difficulty": "medium", "related_keywords": lesson['keywords'][:3]}]

    async def grade_quiz_answer(self, session: LearnSession, quiz: dict, user_answer: str) -> dict:
        lesson = get_lesson(session.lesson_number)
        model_pool = get_model_pool(session.model_mode, user_answer)

        system = "Grade fairly. Return JSON: {\"correct\": bool, \"partial\": bool, \"score\": 0-100, \"feedback\": \"...\", \"correct_answer\": \"...\"}"
        user = f"Question: {quiz.get('question', '')}\nExpected: {quiz.get('answer', '')}\nStudent: {user_answer}"

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model_pool=model_pool,
            max_tokens=400,
        )

        try:
            data = extract_json(raw)
            if data and "correct" in data:
                return data
        except:
            pass

        return {"correct": False, "partial": False, "score": 0, "feedback": "Couldn't grade.", "correct_answer": quiz.get("answer", "")}

    async def ai_answer_question(self, session: LearnSession, question: str) -> str:
        current = get_lesson(session.lesson_number)
        model_pool = get_model_pool(session.model_mode, question)

        context = []
        for i in range(1, min(session.lesson_number + 5, len(LESSONS) + 1)):
            l = get_lesson(i)
            if l:
                context.append(f"Lesson {l['n']}: {l['title']}")

        system = f"""Helpful Roblox Lua/Luau tutor.
Student on Lesson {session.lesson_number}: {current['title'] if current else 'Unknown'}
Covered: {', '.join(context[:15])}

Answer ANY question with code examples. Be helpful!"""

        response = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": question}],
            model_pool=model_pool,
            max_tokens=1200,
        )

        await append_conversation(session.user_id, "assistant", response[:2000])
        return response

    async def generate_final_test(self, session: LearnSession) -> List[dict]:
        weakness = await get_weakness_analysis(session.user_id)
        weak_topics = [k for k, v in weakness["weaknesses"][:10]]

        system = "Create 10-question final exam. Return ONLY JSON array."
        user = f"Focus on weak areas: {', '.join(weak_topics) if weak_topics else 'general review'}"

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=3000,
        )

        try:
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                return json.loads(match.group(0))
        except:
            pass

        return [{"question": "Explain client-server security.", "type": "concept", "answer": "", "points": 10}]

    # =====================================================
    # QUIZ HANDLING
    # =====================================================

    async def handle_quiz_skip(self, channel: discord.TextChannel, session: LearnSession):
        quiz = session.quiz_data
        lesson = get_lesson(session.lesson_number)

        keywords = quiz.get("related_keywords", lesson.get("keywords", []) if lesson else [])
        await track_weakness(session.user_id, keywords, False)

        embed = discord.Embed(
            title="⏭️ Skipped",
            description=f"**Answer:** {quiz.get('answer', 'N/A')}",
            color=discord.Color.orange()
        )
        if quiz.get("explanation"):
            embed.add_field(name="Explanation", value=quiz['explanation'][:1000], inline=False)
        await channel.send(embed=embed)

        await append_conversation(session.user_id, "assistant", f"SKIPPED: {quiz.get('answer', '')}")

        await self._advance_quiz(channel, session)

    async def _advance_quiz(self, channel: discord.TextChannel, session: LearnSession):
        if session.quiz_questions and session.current_quiz_index < len(session.quiz_questions) - 1:
            session.current_quiz_index += 1
            session.quiz_data = session.quiz_questions[session.current_quiz_index]
            session.hints_remaining = 3

            # SAVE STATE
            await save_session_state(session)

            await asyncio.sleep(1.5)

            total = len(session.quiz_questions)
            q = session.quiz_data

            embed = discord.Embed(
                title=f"🧩 Question {session.current_quiz_index + 1}/{total}",
                description=q.get("question", ""),
                color=BOT_COLOR
            )
            embed.add_field(name="Type", value=q.get("type", "").title(), inline=True)
            embed.add_field(name="💡 Hints", value=str(session.hints_remaining), inline=True)

            if q.get("options"):
                embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

            await channel.send(embed=embed, view=QuizControlView(self, session))
        else:
            await self._complete_quiz(channel, session)

    async def _complete_quiz(self, channel: discord.TextChannel, session: LearnSession):
        lesson = get_lesson(session.lesson_number)

        # Update completed lessons
        user = await UserProfile.get_user(session.user_id)
        completed = user.get("learn_completed_lessons", [])
        if session.lesson_number not in completed:
            completed.append(session.lesson_number)
            await UserProfile.update_user(session.user_id, {"learn_completed_lessons": completed})

        # Reset session
        session.phase = "menu"
        session.quiz_data = {}
        session.quiz_questions = []
        session.current_quiz_index = 0
        session.hints_remaining = 3

        # SAVE STATE
        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)
        bar = "█" * int(stats['progress_percent'] / 10) + "░" * (10 - int(stats['progress_percent'] / 10))

        embed = discord.Embed(
            title="🎉 Lesson Complete!",
            description=f"**Lesson {session.lesson_number}: {lesson['title'] if lesson else 'Unknown'}** ✓",
            color=discord.Color.green()
        )
        embed.add_field(name="Progress", value=f"[{bar}] {stats['progress_percent']}%", inline=False)
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} days", inline=True)
        embed.add_field(name="Accuracy", value=f"{stats['accuracy']}%", inline=True)

        if session.lesson_number < len(LESSONS):
            next_l = get_lesson(session.lesson_number + 1)
            if next_l:
                embed.add_field(name="📖 Next", value=f"Lesson {next_l['n']}: {next_l['title']}", inline=False)
        else:
            embed.add_field(name="🎓", value="ALL DONE! Type `final test`!", inline=False)

        await channel.send(embed=embed)

    async def _start_quiz(self, channel: discord.TextChannel, session: LearnSession):
        lesson = get_lesson(session.lesson_number)

        session.phase = "quiz"
        session.hints_remaining = 3

        await channel.send("🧩 **Generating quiz...**")

        async with channel.typing():
            questions = await self.generate_quiz(session, 3)

        session.quiz_questions = questions
        session.current_quiz_index = 0
        session.quiz_data = questions[0] if questions else {}

        # SAVE STATE
        await save_session_state(session)

        await asyncio.sleep(1)

        q = session.quiz_data
        embed = discord.Embed(
            title=f"🧩 Quiz 1/{len(questions)}",
            description=q.get("question", ""),
            color=BOT_COLOR
        )
        embed.add_field(name="Type", value=q.get("type", "").title(), inline=True)
        embed.add_field(name="💡", value=str(session.hints_remaining), inline=True)

        if q.get("options"):
            embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

        await channel.send(embed=embed, view=QuizControlView(self, session))

    # =====================================================
    # FINAL TEST
    # =====================================================

    async def _start_final_test(self, channel: discord.TextChannel, session: LearnSession):
        session.phase = "final_test"
        session.hints_remaining = 5

        await channel.send("🎓 **Generating FINAL EXAM...**")

        async with channel.typing():
            questions = await self.generate_final_test(session)

        session.quiz_questions = questions
        session.current_quiz_index = 0
        session.quiz_data = questions[0] if questions else {}

        # SAVE STATE
        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)

        embed = discord.Embed(
            title="🎓 FINAL EXAM",
            description=f"{len(questions)} questions • 5 hints • Based on YOUR weak areas",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)

        await asyncio.sleep(2)

        q = session.quiz_data
        q_embed = discord.Embed(
            title=f"📝 Q1/{len(questions)}",
            description=q.get("question", ""),
            color=BOT_COLOR
        )
        if q.get("options"):
            q_embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

        await channel.send(embed=q_embed, view=QuizControlView(self, session))

    async def _handle_final_test_answer(self, channel: discord.TextChannel, session: LearnSession, answer: str):
        quiz = session.quiz_data
        grade = await self.grade_quiz_answer(session, quiz, answer)
        is_correct = grade.get("correct", False)

        await track_weakness(session.user_id, quiz.get("related_keywords", []), is_correct)

        user = await UserProfile.get_user(session.user_id)
        await UserProfile.update_user(session.user_id, {
            "learn_total_questions": user.get("learn_total_questions", 0) + 1,
            "learn_correct_answers": user.get("learn_correct_answers", 0) + (1 if is_correct else 0),
        })

        await append_conversation(session.user_id, "assistant", f"FINAL GRADE: {json.dumps(grade)[:500]}")

        if is_correct:
            embed = discord.Embed(title="✅ Correct!", color=discord.Color.green())
        else:
            embed = discord.Embed(
                title="❌ Incorrect",
                description=f"Answer: {grade.get('correct_answer', quiz.get('answer', ''))}",
                color=discord.Color.red()
            )
        await channel.send(embed=embed)

        if session.current_quiz_index < len(session.quiz_questions) - 1:
            session.current_quiz_index += 1
            session.quiz_data = session.quiz_questions[session.current_quiz_index]

            # SAVE STATE
            await save_session_state(session)

            await asyncio.sleep(2)

            q = session.quiz_data
            embed = discord.Embed(
                title=f"📝 Q{session.current_quiz_index + 1}/{len(session.quiz_questions)}",
                description=q.get("question", ""),
                color=BOT_COLOR
            )
            if q.get("options"):
                embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

            await channel.send(embed=embed, view=QuizControlView(self, session))
        else:
            await self._graduate_user(channel, session)

    async def _graduate_user(self, channel: discord.TextChannel, session: LearnSession):
        # Update completed
        user = await UserProfile.get_user(session.user_id)
        completed = user.get("learn_completed_lessons", [])
        if 50 not in completed and len(LESSONS) >= 50:
            completed.append(50)
            await UserProfile.update_user(session.user_id, {"learn_completed_lessons": completed})

        # Reset session
        session.phase = "menu"
        session.quiz_data = {}
        session.quiz_questions = []
        session.current_quiz_index = 0
        session.hints_remaining = 3

        # SAVE STATE
        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)

        await channel.send("🎆" * 10)

        embed = discord.Embed(
            title="🎓🎉 CONGRATULATIONS! 🎉🎓",
            description=(
                "# YOU GRADUATED!\n\n"
                f"• {stats['completed_count']} lessons\n"
                f"• {stats['accuracy']}% accuracy\n"
                f"• {stats['streak']} day streak\n\n"
                "**You are now a Roblox Developer!**"
            ),
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)

        await append_conversation(session.user_id, "assistant", "🎓 GRADUATED!")

        await channel.send("🎊 **GO BUILD AMAZING GAMES!** 🎊")

    # =====================================================
    # MESSAGE LISTENER
    # =====================================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return
        if not message.channel.name.startswith("learn-"):
            return

        try:
            owner_id = int(message.channel.name.split("learn-", 1)[1])
        except:
            return

        if message.author.id != owner_id:
            return

        session = SESSIONS.get(message.channel.id) or await rebuild_session_from_db(message.channel, owner_id)

        raw = message.content.strip()
        content = norm(raw)

        await append_conversation(owner_id, "user", raw)

        # ===== COMMANDS FIRST =====
        if content in TEXT_COMMANDS:
            await self._handle_text_command(message.channel, session, content)
            return

        if content.startswith("review "):
            try:
                num = int(content.split("review ", 1)[1])
                if 1 <= num <= len(LESSONS):
                    old = session.lesson_number
                    session.lesson_number = num
                    await self.send_lesson(message.channel, session, repeat=True)
                    session.lesson_number = old
                    await save_session_state(session)
            except:
                await message.channel.send("Usage: `review 5`")
            return

        # ===== PHASE HANDLING =====
        lesson = get_lesson(session.lesson_number)

        if session.phase == "qna":
            if content in {"no", "nope", "nah", "n", "quiz", "start quiz"}:
                await self._start_quiz(message.channel, session)
                return

            async with message.channel.typing():
                answer = await self.ai_answer_question(session, raw)

            if len(answer) > 1900:
                for part in self._split_content(answer, 1900):
                    await message.channel.send(part)
            else:
                await message.channel.send(answer)

            await message.channel.send("_More questions? Type `no` for quiz._")
            return

        if session.phase == "quiz":
            quiz = session.quiz_data

            if raw.endswith("?") or content.startswith(("what", "why", "how", "explain")):
                answer = await self.ai_answer_question(session, raw)
                await message.channel.send(answer[:1900])
                await message.channel.send("_Now answer the quiz!_")
                return

            grade = await self.grade_quiz_answer(session, quiz, raw)
            keywords = quiz.get("related_keywords", lesson.get("keywords", []) if lesson else [])
            is_correct = grade.get("correct", False)

            await track_weakness(session.user_id, keywords, is_correct)

            user = await UserProfile.get_user(session.user_id)
            await UserProfile.update_user(session.user_id, {
                "learn_total_questions": user.get("learn_total_questions", 0) + 1,
                "learn_correct_answers": user.get("learn_correct_answers", 0) + (1 if is_correct else 0),
            })

            await append_conversation(session.user_id, "assistant", f"GRADING: {json.dumps(grade)[:500]}")

            if is_correct:
                embed = discord.Embed(title="✅ Correct!", description=grade.get("feedback", ""), color=discord.Color.green())
                await message.channel.send(embed=embed)
                await self._advance_quiz(message.channel, session)
            elif grade.get("partial"):
                embed = discord.Embed(title="🟡 Partial", description=grade.get("feedback", ""), color=discord.Color.gold())
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(title="❌ Wrong", description=grade.get("feedback", ""), color=discord.Color.red())
                embed.set_footer(text="Try again • 'hint' • 'skip'")
                await message.channel.send(embed=embed)
            return

        if session.phase == "final_test":
            if raw.endswith("?"):
                answer = await self.ai_answer_question(session, raw)
                await message.channel.send(answer[:1900])
                return
            await self._handle_final_test_answer(message.channel, session, raw)
            return

        if session.phase == "menu":
            await message.channel.send("Type `start lesson` to begin!")

    async def _handle_text_command(self, channel: discord.TextChannel, session: LearnSession, content: str):
        owner_id = session.user_id
        lesson = get_lesson(session.lesson_number)

        # Model switching
        if content in {"switch to coder", "model coder"}:
            session.model_mode = "coder"
            await save_session_state(session)
            await channel.send("✅ **CODER** mode (code-focused models)")
            return

        if content in {"switch to explain", "model explain"}:
            session.model_mode = "explain"
            await save_session_state(session)
            await channel.send("✅ **EXPLAIN** mode (explanation-focused models)")
            return

        if content in {"switch to auto", "model auto"}:
            session.model_mode = "auto"
            await save_session_state(session)
            await channel.send("✅ **AUTO** mode (switches based on content)")
            return

        if content in {"refresh panel", "panel"}:
            await self.send_panel(channel, owner_id)
            return

        if content in {"start lesson", "start"} and session.phase == "menu":
            await self.send_lesson(channel, session)
            return

        if content in {"repeat lesson", "repeat"}:
            await self.send_lesson(channel, session, repeat=True)
            return

        if content in {"next lesson", "next"} and session.phase == "menu":
            if session.lesson_number >= len(LESSONS):
                await channel.send("🎉 All done! Type `final test`!")
                return
            session.lesson_number += 1
            session.phase = "menu"
            await save_session_state(session)
            next_l = get_lesson(session.lesson_number)
            await channel.send(f"📖 **Lesson {session.lesson_number}: {next_l['title'] if next_l else 'Unknown'}**\nType `start lesson`!")
            return

        if content in {"my progress", "progress", "stats"}:
            stats = await get_progress_stats(owner_id)
            weakness = await get_weakness_analysis(owner_id)
            bar = "█" * int(stats['progress_percent'] / 10) + "░" * (10 - int(stats['progress_percent'] / 10))

            embed = discord.Embed(title="📊 Progress", color=BOT_COLOR)
            embed.add_field(name="Progress", value=f"[{bar}] {stats['progress_percent']}%", inline=False)
            embed.add_field(name="🔥", value=f"{stats['streak']} days", inline=True)
            embed.add_field(name="Accuracy", value=f"{stats['accuracy']}%", inline=True)

            if weakness["weaknesses"]:
                embed.add_field(name="⚠️ Weak", value=", ".join([k for k, v in weakness["weaknesses"][:5]]), inline=False)

            await channel.send(embed=embed)
            return

        if content in {"my weaknesses", "weakness analysis", "analyze"}:
            weakness = await get_weakness_analysis(owner_id)
            embed = discord.Embed(title="⚠️ Weakness Analysis", color=discord.Color.orange())
            if weakness["weaknesses"]:
                embed.description = "\n".join([f"• **{k}**: {v}" for k, v in weakness["weaknesses"][:10]])
            else:
                embed.description = "No weaknesses yet!"
            await channel.send(embed=embed)
            return

        if content in {"hint", "get hint", "help"}:
            if session.phase not in {"quiz", "final_test"}:
                await channel.send("💡 Hints only in quizzes!")
                return
            if session.hints_remaining <= 0:
                await channel.send("❌ No hints left!")
                return

            session.hints_remaining -= 1
            user = await UserProfile.get_user(owner_id)
            await UserProfile.update_user(owner_id, {"learn_hints_used": user.get("learn_hints_used", 0) + 1})
            await save_session_state(session)

            hint = await self.generate_hint(lesson, session.quiz_data)
            embed = discord.Embed(title="💡 Hint", description=hint, color=discord.Color.gold())
            embed.set_footer(text=f"Hints: {session.hints_remaining}")
            await channel.send(embed=embed)
            return

        if content in {"cheat sheet", "cheatsheet", "reference"}:
            model_pool = get_model_pool(session.model_mode, "")
            async with channel.typing():
                cheat = await openrouter_chat(
                    [{"role": "system", "content": "Quick cheat sheet with code snippets."},
                     {"role": "user", "content": f"Cheat sheet for {lesson['title'] if lesson else 'current topic'}"}],
                    model_pool=model_pool,
                    max_tokens=800
                )
            embed = discord.Embed(title="📋 Cheat Sheet", description=cheat[:4000], color=discord.Color.gold())
            await channel.send(embed=embed)
            await append_conversation(owner_id, "assistant", f"CHEAT SHEET: {cheat[:1000]}")
            return

        if content in {"bookmark", "save"}:
            user = await UserProfile.get_user(owner_id)
            bookmarks = user.get("learn_bookmarks", [])
            if session.lesson_number not in bookmarks:
                bookmarks.append(session.lesson_number)
                await UserProfile.update_user(owner_id, {"learn_bookmarks": bookmarks})
                await channel.send("🔖 Bookmarked!")
            else:
                await channel.send("Already bookmarked!")
            return

        if content in {"bookmarks", "my bookmarks"}:
            user = await UserProfile.get_user(owner_id)
            bookmarks = user.get("learn_bookmarks", [])
            if bookmarks:
                text = "\n".join([f"• Lesson {n}: {get_lesson(n)['title']}" for n in bookmarks if get_lesson(n)])
                await channel.send(f"🔖 **Bookmarks:**\n{text}")
            else:
                await channel.send("No bookmarks.")
            return

        if content in {"practice", "exercises"}:
            model_pool = get_model_pool(session.model_mode, "")
            async with channel.typing():
                ex = await openrouter_chat(
                    [{"role": "system", "content": "Create hands-on coding exercise."},
                     {"role": "user", "content": f"Exercise for {lesson['title'] if lesson else 'current topic'}"}],
                    model_pool=model_pool,
                    max_tokens=1000
                )
            embed = discord.Embed(title="💪 Practice", description=ex[:4000], color=discord.Color.green())
            await channel.send(embed=embed)
            await append_conversation(owner_id, "assistant", f"PRACTICE: {ex[:1000]}")
            return

        if content in {"skip", "next question"} and session.phase in {"quiz", "final_test"}:
            await self.handle_quiz_skip(channel, session)
            return

        if content in {"final test"}:
            user = await UserProfile.get_user(owner_id)
            if len(user.get("learn_completed_lessons", [])) < 45:
                await channel.send(f"Need 45+ lessons. You have {len(user.get('learn_completed_lessons', []))}.")
                return
            await self._start_final_test(channel, session)
            return

        if content in {"no", "nope", "nah", "n", "quiz", "start quiz"} and session.phase == "qna":
            await self._start_quiz(channel, session)
            return


# =====================================================
# SETUP - Register BOTH persistent views
# =====================================================
async def setup(bot: commands.Bot):
    try:
        bot.tree.remove_command("learn")
    except:
        pass

    cog = LearnCog(bot)
    await bot.add_cog(cog)

    # CRITICAL: Register BOTH persistent views
    bot.add_view(LearnPersistentPanel(cog))
    bot.add_view(QuizControlView(cog))  # ✅ This fixes quiz buttons after restart

    @bot.tree.command(name="learn", description="Learn Roblox Lua/Luau (50 lessons)")
    async def learn_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            return await interaction.followup.send("Use in server.", ephemeral=True)

        if not interaction.guild.me.guild_permissions.manage_channels:
            return await interaction.followup.send("❌ Need Manage Channels.", ephemeral=True)

        await ensure_learn_fields(interaction.user.id, interaction.user.name)

        channel_name = f"learn-{interaction.user.id}"
        existing = discord.utils.get(interaction.guild.text_channels, name=channel_name)

        if existing:
            await cog.send_panel(existing, interaction.user.id)
            return await interaction.followup.send(f"✅ {existing.mention}", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        channel = await interaction.guild.create_text_channel(name=channel_name, overwrites=overwrites)
        await UserProfile.update_user(interaction.user.id, {"learn_channel_id": channel.id})

        session = await rebuild_session_from_db(channel, interaction.user.id)
        SESSIONS[channel.id] = session

        welcome = discord.Embed(
            title="🎮 Roblox Lua/Luau Learning!",
            description="**50 comprehensive lessons!**\nClick Start Lesson to begin.",
            color=BOT_COLOR
        )
        await channel.send(embed=welcome)
        await cog.send_panel(channel, interaction.user.id)
        await interaction.followup.send(f"✅ {channel.mention}", ephemeral=True)