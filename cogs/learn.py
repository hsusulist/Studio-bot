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

from google import genai
from google.genai import types

from config import BOT_COLOR, AI_MODEL
from database import UserProfile

# -----------------------------
# Gemini AI Configuration (Replit AI Integrations)
# -----------------------------
AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

# Replit's AI Integrations provides Gemini-compatible API access
client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL   
    }
)

async def openrouter_chat(messages, model_pool=None, max_tokens=1000):
    """Compatibility wrapper for Gemini AI Integrations"""
    # Convert message list to a single prompt for Gemini
    prompt = ""
    for msg in messages:
        role = "Assistant" if msg["role"] == "assistant" else msg["role"].capitalize()
        prompt += f"{role}: {msg['content']}\n"
    
    try:
        # Use asyncio to run the synchronous client call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=AI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens)
            )
        )
        return response.text or "No response generated."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"❌ AI Error: {str(e)}"

# Model pools for different purposes
CODER_MODELS = [
    "gemini-3-flash",
]

EXPLAIN_MODELS = [
    "gemini-3-pro",
]

ALL_MODELS = CODER_MODELS + EXPLAIN_MODELS

def get_model_pool(mode: str, text: str = "") -> List[str]:
    """Compatibility helper to return model pools based on mode."""
    if mode == "coder":
        return CODER_MODELS
    return EXPLAIN_MODELS


# -----------------------------
# 50 LESSONS - Complete Roblox Lua/Luau Curriculum
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
            "Differentiate between print(), warn(), and error()",
            "Print multiple values at once",
            "Use string formatting inside print",
        ],
        "subtopics": [
            {"name": "Basic print()", "description": "How to use print() to display text", "examples": 2},
            {"name": "Printing variables", "description": "How to print variable values", "examples": 2},
            {"name": "Printing multiple values", "description": "print(a, b, c) with commas", "examples": 2},
            {"name": "warn() for warnings", "description": "When to use warn()", "examples": 1},
            {"name": "error() for errors", "description": "When to use error()", "examples": 1},
            {"name": "Debugging with print", "description": "Basic debugging techniques", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting parentheses: print 'hello' instead of print('hello')",
            "Confusing print with return",
            "Not knowing where output appears in Roblox Studio",
        ],
        "real_world": "Debug scripts, log player actions, test code",
        "estimated_time": "15-20 minutes",
        "mini_project": "Create a script that prints player info when they join the game"
    },
    {
        "n": 2,
        "title": "Variables - Local and Global",
        "phase": "Fundamentals",
        "keywords": ["local", "global", "variable", "scope", "assignment", "declare"],
        "difficulty": "Beginner",
        "prerequisites": [1],
        "learning_objectives": [
            "Understand what a variable is and why you need them",
            "Declare local variables correctly",
            "Understand why you should AVOID global variables",
            "Name variables following conventions",
            "Assign and change variable values",
        ],
        "subtopics": [
            {"name": "What is a variable?", "description": "The concept of a container that stores data", "examples": 2},
            {"name": "Declaring local variables", "description": "local variableName = value", "examples": 3},
            {"name": "Global variables", "description": "Why you should NOT use them", "examples": 2},
            {"name": "Naming conventions", "description": "camelCase, UPPER_CASE for constants", "examples": 2},
            {"name": "Reassignment", "description": "Changing variable values", "examples": 2},
            {"name": "Multiple assignment", "description": "local a, b, c = 1, 2, 3", "examples": 1},
        ],
        "common_mistakes": [
            "Not using local → creates a global variable",
            "Naming variables unclearly: x, temp, data",
            "Using a variable before declaring it",
        ],
        "real_world": "Store player health, game settings, counters",
        "estimated_time": "20-25 minutes",
        "mini_project": "Create a system that stores player info using variables"
    },
    {
        "n": 3,
        "title": "Data Types - The Building Blocks",
        "phase": "Fundamentals",
        "keywords": ["number", "string", "boolean", "nil", "table", "typeof", "type"],
        "difficulty": "Beginner",
        "prerequisites": [2],
        "learning_objectives": [
            "Identify the 6 basic data types in Lua",
            "Use typeof() to check types",
            "Know when to use which type",
            "Convert between types",
        ],
        "subtopics": [
            {"name": "Numbers", "description": "Integers and decimals, no distinction", "examples": 2},
            {"name": "Strings", "description": "Text inside quotes", "examples": 2},
            {"name": "Booleans", "description": "true and false", "examples": 2},
            {"name": "nil", "description": "The value of 'nothing'", "examples": 2},
            {"name": "Tables", "description": "Basic introduction to tables", "examples": 1},
            {"name": "typeof()", "description": "Check the type of a value", "examples": 2},
            {"name": "Type conversion", "description": "tonumber(), tostring()", "examples": 2},
        ],
        "common_mistakes": [
            "Confusing '5' (string) with 5 (number)",
            "Forgetting nil is not 'nil' (string)",
            "Not checking type before performing operations",
        ],
        "real_world": "Player health (number), name (string), isAlive (boolean)",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a player data table using all types"
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
            "Concatenate strings with the .. operator",
            "Use string methods",
            "String interpolation with backticks",
        ],
        "subtopics": [
            {"name": "Creating strings", "description": "Single, double quotes, [[multiline]]", "examples": 2},
            {"name": "Concatenation", "description": "Joining strings with ..", "examples": 2},
            {"name": "String length", "description": "#string or string.len()", "examples": 1},
            {"name": "string.sub()", "description": "Extract part of a string", "examples": 2},
            {"name": "string.find()", "description": "Find substring position", "examples": 2},
            {"name": "string.upper/lower", "description": "Convert to upper/lowercase", "examples": 1},
            {"name": "string.format()", "description": "Format strings with placeholders", "examples": 2},
            {"name": "String interpolation", "description": "`Hello {name}`", "examples": 2},
        ],
        "common_mistakes": [
            "Concatenating number with string without conversion: 'Score: ' .. 100",
            "Confusing # with .len()",
            "String indexing starts at 1, not 0",
        ],
        "real_world": "Chat messages, UI text, formatted output",
        "estimated_time": "20-25 minutes",
        "mini_project": "Create a chat formatting system with colors and prefixes"
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
            {"name": "math.floor/ceil", "description": "Round down/up", "examples": 2},
            {"name": "math.abs", "description": "Absolute value", "examples": 1},
            {"name": "math.random", "description": "Random numbers", "examples": 3},
            {"name": "math.clamp", "description": "Constrain a value within a range", "examples": 2},
            {"name": "math.min/max", "description": "Find min/max", "examples": 1},
        ],
        "common_mistakes": [
            "Dividing by zero",
            "Forgetting math.random() needs a seed",
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
            {"name": "Logical OR", "description": "Either one is true", "examples": 2},
            {"name": "Logical NOT", "description": "Invert a boolean", "examples": 2},
            {"name": "Truthy/Falsy", "description": "nil and false are falsy", "examples": 2},
            {"name": "Short-circuit", "description": "and/or return values", "examples": 2},
        ],
        "common_mistakes": [
            "Using = instead of == for comparison",
            "Using != instead of ~=",
            "Not understanding truthy/falsy",
        ],
        "real_world": "Check player conditions, game state logic",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a permission system with multiple conditions"
    },
    {
        "n": 7,
        "title": "if/elseif/else - Conditionals",
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
            {"name": "Nested if", "description": "If inside if", "examples": 2},
            {"name": "Guard clauses", "description": "Early return pattern", "examples": 2},
            {"name": "Ternary-like", "description": "condition and a or b", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting 'then' after condition",
            "Forgetting 'end'",
            "Using too many nested ifs (pyramid of doom)",
        ],
        "real_world": "Permission checks, level requirements, game state",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a rank system based on player level"
    },
    {
        "n": 8,
        "title": "Functions - The Basics",
        "phase": "Fundamentals",
        "keywords": ["function", "end", "call", "invoke", "define", "declaration"],
        "difficulty": "Beginner",
        "prerequisites": [7],
        "learning_objectives": [
            "Understand what a function is and why you need them",
            "Define and call functions",
            "DRY principle",
            "Local vs global functions",
        ],
        "subtopics": [
            {"name": "What is a function?", "description": "Reusable code blocks", "examples": 2},
            {"name": "Defining a function", "description": "local function name() end", "examples": 2},
            {"name": "Calling a function", "description": "functionName()", "examples": 2},
            {"name": "Anonymous functions", "description": "function() end without a name", "examples": 2},
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
            "Pass data into functions with parameters",
            "Return data with return",
            "Multiple return values",
            "Default parameter pattern",
        ],
        "subtopics": [
            {"name": "Parameters", "description": "Receiving input into a function", "examples": 2},
            {"name": "Arguments", "description": "Values passed when calling", "examples": 2},
            {"name": "Return statement", "description": "Returning a value", "examples": 2},
            {"name": "Multiple returns", "description": "return a, b, c", "examples": 2},
            {"name": "Default values", "description": "param = param or default", "examples": 2},
            {"name": "Variadic (...)", "description": "Accept unlimited arguments", "examples": 2},
        ],
        "common_mistakes": [
            "Not returning anything (nil by default)",
            "Forgetting to capture multiple returns",
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
            "Create and manipulate arrays",
            "Index starting from 1 (not 0)",
            "Add/remove elements",
            "Get length with #",
        ],
        "subtopics": [
            {"name": "Creating an array", "description": "local arr = {1, 2, 3}", "examples": 2},
            {"name": "Accessing elements", "description": "arr[1], arr[2]", "examples": 2},
            {"name": "Changing elements", "description": "arr[1] = newValue", "examples": 2},
            {"name": "table.insert", "description": "Adding an element", "examples": 2},
            {"name": "table.remove", "description": "Removing an element", "examples": 2},
            {"name": "Array length", "description": "#array", "examples": 2},
            {"name": "Nested arrays", "description": "Arrays inside arrays", "examples": 1},
        ],
        "common_mistakes": [
            "Indexing from 0 (Lua starts at 1)",
            "Using table.insert incorrectly",
            "Forgetting # only works with sequential indices",
        ],
        "real_world": "Inventory systems, player lists",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a simple inventory system"
    },
    {
        "n": 11,
        "title": "Tables - Dictionaries",
        "phase": "Fundamentals",
        "keywords": ["dictionary", "key", "value", "pairs", "hash"],
        "difficulty": "Intermediate",
        "prerequisites": [10],
        "learning_objectives": [
            "Create key-value pairs",
            "Access with dot and bracket notation",
            "Add/remove keys",
            "Check if a key exists",
        ],
        "subtopics": [
            {"name": "Creating a dictionary", "description": "{key = value}", "examples": 2},
            {"name": "Dot notation", "description": "dict.key", "examples": 2},
            {"name": "Bracket notation", "description": "dict['key'] and dict[variable]", "examples": 2},
            {"name": "Adding a new key", "description": "dict.newKey = value", "examples": 2},
            {"name": "Removing a key", "description": "dict.key = nil", "examples": 1},
            {"name": "Check if exists", "description": "if dict.key then", "examples": 2},
            {"name": "Mixed tables", "description": "Array + dictionary", "examples": 2},
        ],
        "common_mistakes": [
            "Using dot when the key is a variable",
            "Not checking for nil before accessing nested values",
            "Confusing arrays and dictionaries",
        ],
        "real_world": "Player stats, game config, data storage",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a player stats system"
    },
    {
        "n": 12,
        "title": "Loops - for and ipairs",
        "phase": "Fundamentals",
        "keywords": ["for", "ipairs", "loop", "iterate", "numeric", "break", "continue"],
        "difficulty": "Intermediate",
        "prerequisites": [10],
        "learning_objectives": [
            "Numeric for loop",
            "ipairs() for arrays",
            "break and continue patterns",
            "Nested loops",
        ],
        "subtopics": [
            {"name": "Numeric for", "description": "for i = 1, 10 do", "examples": 2},
            {"name": "Step value", "description": "for i = 1, 10, 2 do", "examples": 2},
            {"name": "Counting backwards", "description": "for i = 10, 1, -1 do", "examples": 1},
            {"name": "ipairs()", "description": "Iterate over arrays", "examples": 2},
            {"name": "break", "description": "Exit a loop early", "examples": 2},
            {"name": "continue pattern", "description": "Using if to skip iterations", "examples": 2},
            {"name": "Nested loops", "description": "Loops inside loops", "examples": 2},
        ],
        "common_mistakes": [
            "Modifying the loop variable inside the loop",
            "Infinite loops",
            "Off-by-one errors",
        ],
        "real_world": "Process all players, spawn items",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a spawn system for multiple objects"
    },

    # ===== PHASE 2: INTERMEDIATE (13-24) =====
    {
        "n": 13,
        "title": "Loops - pairs and while",
        "phase": "Intermediate",
        "keywords": ["pairs", "while", "do", "repeat", "until"],
        "difficulty": "Intermediate",
        "prerequisites": [11, 12],
        "learning_objectives": [
            "pairs() for dictionaries",
            "while loops",
            "repeat...until",
            "Choosing the right loop",
        ],
        "subtopics": [
            {"name": "pairs()", "description": "Iterate over dictionaries", "examples": 2},
            {"name": "pairs vs ipairs", "description": "When to use which", "examples": 2},
            {"name": "while loop", "description": "while condition do", "examples": 2},
            {"name": "Infinite while", "description": "while true do (with break)", "examples": 2},
            {"name": "repeat until", "description": "Runs at least once", "examples": 2},
            {"name": "Loop comparison", "description": "for vs while vs repeat", "examples": 2},
        ],
        "common_mistakes": [
            "pairs() order is not guaranteed",
            "Infinite loop without break/condition update",
            "Modifying a table while iterating over it",
        ],
        "real_world": "Game loops, waiting for conditions",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a game loop with countdown"
    },
    {
        "n": 14,
        "title": "Colon Syntax and Methods",
        "phase": "Intermediate",
        "keywords": [":", "self", "method", "colon", "dot", "object"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 11],
        "learning_objectives": [
            "Understand : vs . syntax",
            "self parameter",
            "Define methods",
            "Roblox API uses colon",
        ],
        "subtopics": [
            {"name": "Dot vs colon", "description": "The critical difference", "examples": 3},
            {"name": "What is self?", "description": "Reference to the object", "examples": 2},
            {"name": "Colon auto-passes self", "description": "obj:method() = obj.method(obj)", "examples": 2},
            {"name": "Defining methods", "description": "function obj:methodName()", "examples": 2},
            {"name": "Roblox uses colon", "description": "part:Destroy(), player:Kick()", "examples": 2},
        ],
        "common_mistakes": [
            "Using . when you need :",
            "Using : when you need .",
            "Forgetting self in the method body",
        ],
        "real_world": "All Roblox methods use colon",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create an object with methods"
    },
    {
        "n": 15,
        "title": "Scope and Closures",
        "phase": "Intermediate",
        "keywords": ["scope", "local", "block", "lifetime", "closure", "upvalue"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 13],
        "learning_objectives": [
            "Block scope in Lua",
            "Variable lifetime",
            "What closures are",
            "Practical closure uses",
        ],
        "subtopics": [
            {"name": "Block scope", "description": "Variables inside do...end", "examples": 2},
            {"name": "Function scope", "description": "Local variables inside functions", "examples": 2},
            {"name": "Variable shadowing", "description": "Same name in different scopes", "examples": 2},
            {"name": "Closures", "description": "Functions that remember their scope", "examples": 3},
            {"name": "Upvalues", "description": "Variables from an outer scope", "examples": 2},
            {"name": "Practical closures", "description": "Factories, callbacks", "examples": 2},
        ],
        "common_mistakes": [
            "Not understanding that a variable is being shadowed",
            "Closures hold a reference, not a copy",
            "Memory leaks from closures",
        ],
        "real_world": "Event handlers, factory functions",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a counter factory using closures"
    },
    {
        "n": 16,
        "title": "Error Handling - pcall and xpcall",
        "phase": "Intermediate",
        "keywords": ["pcall", "xpcall", "error", "assert", "debug", "protected"],
        "difficulty": "Intermediate",
        "prerequisites": [9],
        "learning_objectives": [
            "Why error handling is needed",
            "pcall() protected calls",
            "xpcall() with an error handler",
            "assert() for validation",
        ],
        "subtopics": [
            {"name": "error()", "description": "Throwing errors", "examples": 2},
            {"name": "pcall()", "description": "Protected call", "examples": 3},
            {"name": "pcall returns", "description": "success, result/error", "examples": 2},
            {"name": "xpcall()", "description": "Custom error handler", "examples": 2},
            {"name": "assert()", "description": "Condition or error", "examples": 2},
            {"name": "Error patterns", "description": "Try-catch style", "examples": 2},
        ],
        "common_mistakes": [
            "Not checking pcall success",
            "Swallowing errors without logging",
            "Using pcall for everything",
        ],
        "real_world": "API calls, user input validation",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create a safe function wrapper"
    },
    {
        "n": 17,
        "title": "ModuleScripts and require()",
        "phase": "Intermediate",
        "keywords": ["modulescript", "module", "require", "return", "reusable", "organize"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 11],
        "learning_objectives": [
            "Why ModuleScripts are needed",
            "How to create a module correctly",
            "require() and caching",
            "Organize code with modules",
        ],
        "subtopics": [
            {"name": "What is a ModuleScript?", "description": "Reusable code container", "examples": 1},
            {"name": "Module structure", "description": "local M = {} ... return M", "examples": 2},
            {"name": "require()", "description": "Importing a module", "examples": 2},
            {"name": "Caching behavior", "description": "require() only runs once", "examples": 2},
            {"name": "Return table vs function", "description": "Common patterns", "examples": 2},
            {"name": "Module organization", "description": "Best practices", "examples": 2},
        ],
        "common_mistakes": [
            "Not returning anything",
            "Returning before defining",
            "Circular dependencies",
        ],
        "real_world": "Shared utilities, config, game systems",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a module for utility functions"
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
            "Instance.new() the right way",
            "Parent and Children",
            "Find instances with Find methods",
        ],
        "subtopics": [
            {"name": "What is an Instance?", "description": "Objects in Roblox", "examples": 2},
            {"name": "Instance.new()", "description": "Creating a new instance", "examples": 2},
            {"name": "Parent property", "description": "Set Parent LAST for performance", "examples": 2},
            {"name": "FindFirstChild", "description": "Safely find a child", "examples": 2},
            {"name": "WaitForChild", "description": "Wait for a child to load", "examples": 2},
            {"name": "Clone()", "description": "Copy an instance", "examples": 2},
            {"name": "Destroy()", "description": "Remove an instance", "examples": 2},
        ],
        "common_mistakes": [
            "Setting Parent before Properties (performance hit)",
            "Using . instead of FindFirstChild",
            "Not nil-checking after Find",
        ],
        "real_world": "Spawning objects, creating effects",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create an object spawner"
    },
    {
        "n": 19,
        "title": "Properties and CFrame Basics",
        "phase": "Intermediate",
        "keywords": ["property", "position", "size", "cframe", "vector3", "color3"],
        "difficulty": "Intermediate",
        "prerequisites": [18],
        "learning_objectives": [
            "Read and set properties",
            "Vector3 for positions/sizes",
            "CFrame basics",
            "Color3 for colors",
        ],
        "subtopics": [
            {"name": "Reading properties", "description": "part.Position, part.Size", "examples": 2},
            {"name": "Setting properties", "description": "part.Transparency = 0.5", "examples": 2},
            {"name": "Vector3", "description": "Vector3.new(x, y, z)", "examples": 2},
            {"name": "CFrame basics", "description": "Position + Rotation", "examples": 3},
            {"name": "CFrame.new()", "description": "Creating a CFrame", "examples": 2},
            {"name": "Color3", "description": "RGB and fromRGB", "examples": 2},
        ],
        "common_mistakes": [
            "Trying to modify Vector3 directly (it's immutable)",
            "Confusing Position with CFrame",
            "Color values 0-255 vs 0-1",
        ],
        "real_world": "Moving objects, changing appearance",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create a part mover with color change"
    },
    {
        "n": 20,
        "title": "Events and Connections",
        "phase": "Intermediate",
        "keywords": ["event", "connect", "disconnect", "touched", "signal", "callback", "rbxScriptSignal"],
        "difficulty": "Intermediate",
        "prerequisites": [8, 18],
        "learning_objectives": [
            "Event-driven programming",
            ":Connect() method",
            "Event parameters",
            "Disconnect and cleanup",
        ],
        "subtopics": [
            {"name": "What are Events?", "description": "Signals when something happens", "examples": 2},
            {"name": ":Connect()", "description": "Listen to events", "examples": 2},
            {"name": "Callback functions", "description": "Function that runs when event fires", "examples": 2},
            {"name": "Event parameters", "description": "Data passed to the callback", "examples": 2},
            {"name": "Storing connections", "description": "local conn = event:Connect()", "examples": 2},
            {"name": ":Disconnect()", "description": "Stop listening", "examples": 2},
            {"name": ":Once()", "description": "Listen only once", "examples": 1},
            {"name": ":Wait()", "description": "Yield until event fires", "examples": 1},
        ],
        "common_mistakes": [
            "Not disconnecting → memory leak",
            "Connecting inside a loop → multiple connections",
            "Forgetting that events have parameters",
        ],
        "real_world": "Collision detection, player input, UI",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create a touch-activated door"
    },
    {
        "n": 21,
        "title": "Player and Character",
        "phase": "Intermediate",
        "keywords": ["player", "character", "humanoid", "playerAdded", "characterAdded"],
        "difficulty": "Intermediate",
        "prerequisites": [20],
        "learning_objectives": [
            "Player vs Character",
            "Access the Players service",
            "PlayerAdded event",
            "CharacterAdded event",
        ],
        "subtopics": [
            {"name": "Player object", "description": "Account/data container", "examples": 2},
            {"name": "Character object", "description": "The avatar in-game", "examples": 2},
            {"name": "Players service", "description": "game:GetService('Players')", "examples": 2},
            {"name": "PlayerAdded", "description": "When a player joins", "examples": 2},
            {"name": "PlayerRemoving", "description": "When a player leaves", "examples": 2},
            {"name": "CharacterAdded", "description": "When a character spawns", "examples": 2},
            {"name": "Humanoid", "description": "Controls the character", "examples": 2},
        ],
        "common_mistakes": [
            "Accessing character when it's nil",
            "Not handling CharacterAdded",
            "Confusing Player with Character",
        ],
        "real_world": "Player join handling, respawn logic",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create a welcome system with player data"
    },
    {
        "n": 22,
        "title": "Services in Roblox",
        "phase": "Intermediate",
        "keywords": ["service", "getService", "workspace", "replicatedStorage", "serverStorage"],
        "difficulty": "Intermediate",
        "prerequisites": [18],
        "learning_objectives": [
            "What Services are",
            "GetService() the right way",
            "Common services",
            "Server vs Client services",
        ],
        "subtopics": [
            {"name": "What are Services?", "description": "Singletons that provide functionality", "examples": 1},
            {"name": "GetService()", "description": "game:GetService('Name')", "examples": 2},
            {"name": "Workspace", "description": "Contains 3D objects", "examples": 2},
            {"name": "Players", "description": "All players", "examples": 1},
            {"name": "ReplicatedStorage", "description": "Shared assets", "examples": 2},
            {"name": "ServerStorage", "description": "Server-only assets", "examples": 2},
            {"name": "RunService", "description": "Game loop events", "examples": 2},
        ],
        "common_mistakes": [
            "Accessing ServerStorage from the client",
            "Not caching service references",
            "Using game.Workspace instead of workspace",
        ],
        "real_world": "Access game components properly",
        "estimated_time": "25-30 minutes",
        "mini_project": "Set up proper service references"
    },
    {
        "n": 23,
        "title": "task Library and Timing",
        "phase": "Intermediate",
        "keywords": ["task.wait", "task.spawn", "task.defer", "task.delay", "runservice", "heartbeat"],
        "difficulty": "Intermediate",
        "prerequisites": [13, 20],
        "learning_objectives": [
            "task vs wait()",
            "Parallel execution with spawn",
            "Frame-based timing",
            "Delta time",
        ],
        "subtopics": [
            {"name": "task.wait()", "description": "Better than wait()", "examples": 2},
            {"name": "task.spawn()", "description": "Run in parallel", "examples": 2},
            {"name": "task.defer()", "description": "Run next frame", "examples": 2},
            {"name": "task.delay()", "description": "Run after a delay", "examples": 2},
            {"name": "task.cancel()", "description": "Cancel a scheduled task", "examples": 1},
            {"name": "RunService.Heartbeat", "description": "Every frame", "examples": 2},
            {"name": "Delta time", "description": "Time since last frame", "examples": 2},
        ],
        "common_mistakes": [
            "Using wait() instead of task.wait()",
            "Not handling task cancellation",
            "Not using dt for smooth movement",
        ],
        "real_world": "Smooth animations, cooldowns, timers",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a cooldown system"
    },
    {
        "n": 24,
        "title": "Attributes and Tags",
        "phase": "Intermediate",
        "keywords": ["attribute", "tag", "collectionService", "setAttribute", "getAttribute"],
        "difficulty": "Intermediate",
        "prerequisites": [18, 22],
        "learning_objectives": [
            "Attributes for custom data",
            "Tags for categorization",
            "CollectionService",
            "When to use attributes vs values",
        ],
        "subtopics": [
            {"name": "What are Attributes?", "description": "Custom properties on instances", "examples": 2},
            {"name": "SetAttribute()", "description": "Set an attribute value", "examples": 2},
            {"name": "GetAttribute()", "description": "Get an attribute value", "examples": 2},
            {"name": "GetAttributeChangedSignal", "description": "Listen for changes", "examples": 2},
            {"name": "What are Tags?", "description": "Labels for instances", "examples": 2},
            {"name": "CollectionService", "description": "Get tagged instances", "examples": 2},
        ],
        "common_mistakes": [
            "Attribute types are limited",
            "Tag name typos",
            "Not handling nil attributes",
        ],
        "real_world": "Enemy types, item rarity, game states",
        "estimated_time": "25-30 minutes",
        "mini_project": "Create an enemy tagging system"
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
            "Client vs Server in Roblox",
            "Script types",
            "Filtering Enabled",
            "Trust boundary",
        ],
        "subtopics": [
            {"name": "What is the Client?", "description": "The player's computer", "examples": 2},
            {"name": "What is the Server?", "description": "Roblox's computer", "examples": 2},
            {"name": "Script (Server)", "description": "Runs on the server", "examples": 2},
            {"name": "LocalScript (Client)", "description": "Runs on the client", "examples": 2},
            {"name": "Filtering Enabled", "description": "Client changes don't replicate", "examples": 2},
            {"name": "Trust boundary", "description": "NEVER trust the client", "examples": 3},
        ],
        "common_mistakes": [
            "Trusting client data",
            "Putting game logic on the client",
            "Sending sensitive data to the client",
        ],
        "real_world": "Multiplayer game architecture",
        "estimated_time": "35-40 minutes",
        "mini_project": "Design a secure game system"
    },
    {
        "n": 26,
        "title": "RemoteEvents Basics",
        "phase": "Advanced",
        "keywords": ["remoteEvent", "fireServer", "onServerEvent", "fireClient", "onClientEvent"],
        "difficulty": "Advanced",
        "prerequisites": [25],
        "learning_objectives": [
            "What RemoteEvents are",
            "Client → Server communication",
            "Server → Client communication",
            "Setting them up correctly",
        ],
        "subtopics": [
            {"name": "What is a RemoteEvent?", "description": "Cross-boundary communication", "examples": 1},
            {"name": "Create a RemoteEvent", "description": "In ReplicatedStorage", "examples": 2},
            {"name": "FireServer()", "description": "Client sends to server", "examples": 2},
            {"name": "OnServerEvent", "description": "Server receives", "examples": 2},
            {"name": "FireClient()", "description": "Server sends to client", "examples": 2},
            {"name": "FireAllClients()", "description": "Broadcast to all", "examples": 2},
            {"name": "OnClientEvent", "description": "Client receives", "examples": 2},
        ],
        "common_mistakes": [
            "Calling FireServer from the server",
            "Listening to OnServerEvent on the client",
            "Not passing the player argument",
        ],
        "real_world": "Multiplayer actions, UI updates",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create a simple chat system"
    },
    {
        "n": 27,
        "title": "RemoteEvents Security",
        "phase": "Advanced",
        "keywords": ["validate", "sanity", "exploit", "hack", "secure", "sanitize"],
        "difficulty": "Advanced",
        "prerequisites": [26],
        "learning_objectives": [
            "Why security is critical",
            "Validate ALL inputs",
            "Sanity checks",
            "Common exploits",
        ],
        "subtopics": [
            {"name": "Never trust the client", "description": "Rule #1", "examples": 2},
            {"name": "Type validation", "description": "typeof() checks", "examples": 2},
            {"name": "Range validation", "description": "Are values reasonable?", "examples": 2},
            {"name": "Permission checks", "description": "Can the player do this?", "examples": 2},
            {"name": "Rate limiting", "description": "Prevent spam", "examples": 2},
            {"name": "Common exploits", "description": "Examples of hacks", "examples": 3},
        ],
        "common_mistakes": [
            "Trusting client-sent data",
            "Only validating on the client",
            "Exposing sensitive endpoints",
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
            "When to use RemoteFunctions",
            "Risks of InvokeClient",
        ],
        "subtopics": [
            {"name": "What is a RemoteFunction?", "description": "Returns a value", "examples": 2},
            {"name": "InvokeServer()", "description": "Client requests, gets response", "examples": 2},
            {"name": "OnServerInvoke", "description": "Server handles and returns", "examples": 2},
            {"name": "InvokeClient risks", "description": "NEVER use in production", "examples": 2},
            {"name": "Event vs Function", "description": "When to use which", "examples": 2},
            {"name": "Timeout handling", "description": "Handle no response", "examples": 2},
        ],
        "common_mistakes": [
            "Using InvokeClient",
            "No timeout handling",
            "Returning sensitive data",
        ],
        "real_world": "Shop purchases, data requests",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create a shop system with RemoteFunction"
    },
    {
        "n": 29,
        "title": "DataStoreService Basics",
        "phase": "Advanced",
        "keywords": ["dataStore", "save", "load", "getAsync", "setAsync", "persist"],
        "difficulty": "Advanced",
        "prerequisites": [16, 21],
        "learning_objectives": [
            "What DataStores are",
            "GetAsync/SetAsync",
            "Error handling for DataStores",
            "Rate limits",
        ],
        "subtopics": [
            {"name": "DataStoreService", "description": "Persistent storage", "examples": 1},
            {"name": "GetDataStore()", "description": "Get a data store", "examples": 2},
            {"name": "GetAsync()", "description": "Load data", "examples": 2},
            {"name": "SetAsync()", "description": "Save data", "examples": 2},
            {"name": "Error handling", "description": "pcall is required", "examples": 3},
            {"name": "Rate limits", "description": "Request budgets", "examples": 2},
        ],
        "common_mistakes": [
            "Not wrapping DataStore calls in pcall",
            "Spamming SetAsync",
            "Saving on every single change",
        ],
        "real_world": "Player data persistence",
        "estimated_time": "40-45 minutes",
        "mini_project": "Build a basic data save system"
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
            {"name": "Session locking", "description": "Prevent multi-server issues", "examples": 2},
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
        "mini_project": "Complete save system with autosave"
    },
    {
        "n": 31,
        "title": "UI Basics with ScreenGui",
        "phase": "Advanced",
        "keywords": ["screenGui", "frame", "textLabel", "textButton", "imageLabel"],
        "difficulty": "Advanced",
        "prerequisites": [20, 25],
        "learning_objectives": [
            "ScreenGui structure",
            "Common UI elements",
            "Positioning with UDim2",
            "UI events",
        ],
        "subtopics": [
            {"name": "ScreenGui", "description": "UI container", "examples": 2},
            {"name": "Frame", "description": "Container/background", "examples": 2},
            {"name": "TextLabel", "description": "Display text", "examples": 2},
            {"name": "TextButton", "description": "Clickable button", "examples": 2},
            {"name": "UDim2 positioning", "description": "Scale and Offset", "examples": 3},
            {"name": "AnchorPoint", "description": "Origin point", "examples": 2},
            {"name": "MouseButton1Click", "description": "Button event", "examples": 2},
        ],
        "common_mistakes": [
            "Wrong parent for ScreenGui",
            "Mixing Scale and Offset badly",
            "Not considering AnchorPoint",
        ],
        "real_world": "Game menus, HUDs",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create a simple menu UI"
    },
    {
        "n": 32,
        "title": "UI Layouts and Constraints",
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
            {"name": "UIAspectRatioConstraint", "description": "Keep aspect ratio", "examples": 2},
            {"name": "UISizeConstraint", "description": "Min/max size", "examples": 1},
        ],
        "common_mistakes": [
            "Conflicts with manual positioning",
            "Wrong layout order",
            "Forgetting SortOrder",
        ],
        "real_world": "Inventory grids, menus",
        "estimated_time": "30-35 minutes",
        "mini_project": "Create an inventory grid UI"
    },
    {
        "n": 33,
        "title": "TweenService and Animations",
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
            {"name": "Create a tween", "description": ":Create(instance, info, goals)", "examples": 2},
            {"name": "Easing styles", "description": "Linear, Quad, Bounce...", "examples": 2},
            {"name": "Easing direction", "description": "In, Out, InOut", "examples": 2},
            {"name": "Tween:Play()", "description": "Start animation", "examples": 2},
            {"name": "Tween.Completed", "description": "Wait for finish", "examples": 2},
        ],
        "common_mistakes": [
            "Tweening a destroyed instance",
            "Conflicting tweens on the same property",
            "Wrong property type for tween goal",
        ],
        "real_world": "UI animations, door opening",
        "estimated_time": "35-40 minutes",
        "mini_project": "Create animated UI with TweenService"
    },
    {
        "n": 34,
        "title": "Object-Oriented Programming",
        "phase": "Advanced",
        "keywords": ["oop", "class", "object", "metatable", "inheritance", "__index"],
        "difficulty": "Advanced",
        "prerequisites": [14, 15],
        "learning_objectives": [
            "OOP concepts in Lua",
            "Metatables for classes",
            "__index metamethod",
            "Inheritance patterns",
        ],
        "subtopics": [
            {"name": "What is OOP?", "description": "Objects with data and methods", "examples": 2},
            {"name": "Metatables", "description": "Change table behavior", "examples": 2},
            {"name": "__index", "description": "Property lookup fallback", "examples": 3},
            {"name": "Class pattern", "description": "Standard Lua class", "examples": 3},
            {"name": ".new() constructor", "description": "Create instances", "examples": 2},
            {"name": "Inheritance", "description": "Extending classes", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting setmetatable",
            "Wrong self reference in methods",
            "Shallow copy issues",
        ],
        "real_world": "Game entities, systems",
        "estimated_time": "45-50 minutes",
        "mini_project": "Create an Entity class system"
    },
    {
        "n": 35,
        "title": "Raycasting",
        "phase": "Advanced",
        "keywords": ["raycast", "ray", "hit", "normal", "raycastParams", "filter"],
        "difficulty": "Advanced",
        "prerequisites": [19, 22],
        "learning_objectives": [
            "What raycasting is",
            "workspace:Raycast()",
            "RaycastParams",
            "Practical uses",
        ],
        "subtopics": [
            {"name": "What is raycasting?", "description": "Invisible line detection", "examples": 2},
            {"name": "workspace:Raycast()", "description": "Cast a ray", "examples": 2},
            {"name": "RaycastParams", "description": "Filter objects", "examples": 2},
            {"name": "RaycastResult", "description": "Instance, Position, Normal", "examples": 2},
            {"name": "FilterType", "description": "Include/Exclude", "examples": 2},
            {"name": "Multiple raycasts", "description": "Pattern examples", "examples": 2},
        ],
        "common_mistakes": [
            "Wrong direction vector",
            "Forgetting FilterDescendantsInstances",
            "Ray too short or too long",
        ],
        "real_world": "Shooting, ground detection, line of sight",
        "estimated_time": "40-45 minutes",
        "mini_project": "Build a simple gun raycast system"
    },
    {
        "n": 36,
        "title": "Physics and BodyMovers",
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
            "Fighting the physics engine",
            "Wrong attachment setup",
            "Performance issues with too many physics objects",
        ],
        "real_world": "Flying, knockback, vehicles",
        "estimated_time": "40-45 minutes",
        "mini_project": "Build a simple flying system"
    },

    # ===== PHASE 4: EXPERT (37-45) =====
    {
        "n": 37,
        "title": "BindableEvents and Custom Signals",
        "phase": "Expert",
        "keywords": ["bindableEvent", "bindableFunction", "signal", "observer", "pubsub"],
        "difficulty": "Expert",
        "prerequisites": [20, 17],
        "learning_objectives": [
            "BindableEvents for same-boundary communication",
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
            "Using for cross-boundary communication",
            "Memory leaks in signals",
            "Circular dependencies",
        ],
        "real_world": "Game event system, modular code",
        "estimated_time": "35-40 minutes",
        "mini_project": "Build a custom signal class"
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
            "Create and compute paths",
            "Follow waypoints",
            "Handle blocked paths",
        ],
        "subtopics": [
            {"name": "PathfindingService", "description": "NPC navigation", "examples": 1},
            {"name": "CreatePath()", "description": "Path configuration", "examples": 2},
            {"name": "ComputeAsync()", "description": "Calculate a path", "examples": 2},
            {"name": "GetWaypoints()", "description": "Path points", "examples": 2},
            {"name": "Move along path", "description": "Humanoid:MoveTo", "examples": 2},
            {"name": "Blocked event", "description": "Recompute path", "examples": 2},
        ],
        "common_mistakes": [
            "No blocked path handling",
            "Computing paths on the client",
            "Ignoring path status",
        ],
        "real_world": "NPC AI, enemy following",
        "estimated_time": "45-50 minutes",
        "mini_project": "Build an NPC that follows the player"
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
            "Implement FSM in Lua",
            "State transitions",
            "Use cases",
        ],
        "subtopics": [
            {"name": "What is a FSM?", "description": "Finite State Machine", "examples": 2},
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
        "mini_project": "Build enemy AI with a state machine"
    },
    {
        "n": 40,
        "title": "Promise Pattern",
        "phase": "Expert",
        "keywords": ["promise", "async", "await", "then", "catch", "chain"],
        "difficulty": "Expert",
        "prerequisites": [16, 23],
        "learning_objectives": [
            "What Promises are",
            "Roblox Promise library",
            "Chaining promises",
            "Error handling",
        ],
        "subtopics": [
            {"name": "What are Promises?", "description": "Async value container", "examples": 2},
            {"name": "Promise.new()", "description": "Create a promise", "examples": 2},
            {"name": ":andThen()", "description": "Chain operations", "examples": 2},
            {"name": ":catch()", "description": "Handle errors", "examples": 2},
            {"name": ":finally()", "description": "Always runs", "examples": 2},
            {"name": "Promise.all()", "description": "Wait for multiple", "examples": 2},
        ],
        "common_mistakes": [
            "Forgetting error handling",
            "Nesting promises instead of chaining",
            "Promise hell",
        ],
        "real_world": "Complex async flows",
        "estimated_time": "40-45 minutes",
        "mini_project": "Async data loading with promises"
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
            {"name": "What are Components?", "description": "Reusable behaviors", "examples": 2},
            {"name": "Composition", "description": "Combine behaviors", "examples": 2},
            {"name": "Component lifecycle", "description": "Init/Start/Destroy", "examples": 2},
            {"name": "Tag-based components", "description": "Using CollectionService", "examples": 2},
            {"name": "Component framework", "description": "Build your own", "examples": 3},
        ],
        "common_mistakes": [
            "Components too tightly coupled",
            "No cleanup on destroy",
            "Heavy initialization",
        ],
        "real_world": "Modular game objects",
        "estimated_time": "45-50 minutes",
        "mini_project": "Build a component system"
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
            {"name": "Spatial optimization", "description": "Only update nearby objects", "examples": 2},
            {"name": "Common mistakes", "description": "Performance killers", "examples": 2},
        ],
        "common_mistakes": [
            "Premature optimization",
            "Not profiling first",
            "Optimizing the wrong things",
        ],
        "real_world": "Smooth gameplay at scale",
        "estimated_time": "45-50 minutes",
        "mini_project": "Optimize a slow system"
    },
    {
        "n": 43,
        "title": "Testing and Debugging",
        "phase": "Expert",
        "keywords": ["test", "debug", "unit test", "integration", "mock"],
        "difficulty": "Expert",
        "prerequisites": [16, 17],
        "learning_objectives": [
            "Why testing matters",
            "Unit tests in Lua",
            "Debug strategies",
            "Logging best practices",
        ],
        "subtopics": [
            {"name": "Why test?", "description": "Catch bugs early", "examples": 1},
            {"name": "Unit testing", "description": "Test individual functions", "examples": 2},
            {"name": "Test framework", "description": "Simple test runner", "examples": 2},
            {"name": "Mocking", "description": "Fake dependencies", "examples": 2},
            {"name": "Debug strategies", "description": "Find bugs efficiently", "examples": 2},
            {"name": "Logging", "description": "Good log practices", "examples": 2},
        ],
        "common_mistakes": [
            "No tests at all",
            "Testing implementation, not behavior",
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
            "Trusting client timing",
        ],
        "real_world": "Hack-proof games",
        "estimated_time": "50-55 minutes",
        "mini_project": "Security audit a game system"
    },
    {
        "n": 45,
        "title": "Architecture and Clean Code",
        "phase": "Expert",
        "keywords": ["architecture", "clean code", "solid", "patterns", "maintainable"],
        "difficulty": "Expert",
        "prerequisites": [17, 34, 41],
        "learning_objectives": [
            "Game architecture patterns",
            "Clean code principles",
            "SOLID in Lua",
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
        "mini_project": "Refactor a codebase with patterns"
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
            {"name": "Effects/Feedback", "description": "Visual/audio feedback", "examples": 2},
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
            {"name": "Difficulty scaling", "description": "Adjust AI difficulty", "examples": 1},
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
            "Apply everything you've learned",
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
    for lesson in LESSONS:
        if lesson["n"] == n:
            return lesson
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
    except Exception:
        return None


# List of ALL text commands - bypass AI relevance check
TEXT_COMMANDS = {
    "start", "start lesson", "repeat", "repeat lesson", "next", "next lesson",
    "hint", "get hint", "help", "cheat sheet", "cheatsheet", "reference",
    "my progress", "progress", "stats", "bookmark", "save", "bookmarks",
    "my bookmarks", "practice", "exercises", "skip", "next question",
    "refresh panel", "panel", "switch to coder", "model coder",
}
# Persistent Storage Helpers
# -----------------------------
def _safe_int(x, default=1) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
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
# SAVE ALL SESSION STATE
# =====================================================
async def save_session_state(session: "LearnSession"):
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
            # diff == 0: same day, keep streak unchanged
        except (ValueError, TypeError):
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
    total_lessons = len(LESSONS) if LESSONS else 1
    progress_pct = len(completed) / total_lessons * 100

    current = get_lesson(current_lesson)
    phase = current.get("phase", "Fundamentals") if current else "Fundamentals"

    return {
        "current_lesson": current_lesson,
        "current_phase": phase,
        "completed_count": len(completed),
        "total_lessons": total_lessons,
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
    user = await ensure_learn_fields(user_id, "Unknown")

    total = len(LESSONS) if LESSONS else 50
    lesson = max(1, min(_safe_int(user.get("learn_lesson", 1)), total))

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
# PERSISTENT VIEWS (timeout=None)
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
        
        # Admin bypass for learn controls
        is_admin = interaction.user.guild_permissions.administrator
        if not (interaction.user.id == session.user_id or is_admin):
            return await interaction.followup.send("❌ Not allowed.", ephemeral=True)
            
        await self.cog.send_lesson(interaction.channel, session, repeat=False)

    @discord.ui.button(label="Repeat", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="learn:repeat")
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("❌ Not allowed.", ephemeral=True)
        await self.cog.send_lesson(interaction.channel, session, repeat=True)

    @discord.ui.button(label="Next Lesson", style=discord.ButtonStyle.blurple, emoji="⏭️", custom_id="learn:next")
    async def next_lesson(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("❌ Not allowed.", ephemeral=True)

        if session.lesson_number >= len(LESSONS):
            return await interaction.followup.send("🎉 All lessons complete! Type `final test` to graduate!")

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

        weak_text = ", ".join([f"`{k}` ({v})" for k, v in weakness["weaknesses"][:5]]) or "None yet"
        strong_text = ", ".join([f"`{k}` ({v})" for k, v in weakness["strengths"][:5]]) or "None yet"

        embed = discord.Embed(title="📊 Your Progress", color=BOT_COLOR)
        embed.add_field(name="Overall", value=f"`[{bar}]` {stats['progress_percent']}%", inline=False)
        embed.add_field(name="📚 Lessons", value=f"{stats['completed_count']}/{stats['total_lessons']}", inline=True)
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} days", inline=True)
        embed.add_field(name="🎯 Accuracy", value=f"{stats['accuracy']}%", inline=True)
        embed.add_field(name="⚠️ Weak Topics", value=weak_text, inline=False)
        embed.add_field(name="💪 Strong Topics", value=strong_text, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="End Session", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="learn:end")
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        session = await self.cog.get_or_rebuild_session(interaction)
        if not self._is_controller(interaction, session):
            return await interaction.followup.send("❌ Not allowed.", ephemeral=True)

        SESSIONS.pop(session.channel_id, None)
        session.phase = "menu"
        await save_session_state(session)
        await interaction.followup.send("✅ Session ended. Your progress is saved.", ephemeral=True)


class QuizControlView(discord.ui.View):
    """Quiz control buttons - persistent across restarts"""

    def __init__(self, cog: "LearnCog", session: LearnSession = None):
        super().__init__(timeout=None)
        self.cog = cog
        self.session = session

    @discord.ui.button(label="Hint", style=discord.ButtonStyle.secondary, emoji="💡", custom_id="quiz:hint_btn")
    async def get_hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        session = await self.cog.get_or_rebuild_session(interaction)

        if session.phase not in {"quiz", "final_test"}:
            return await interaction.followup.send("💡 Hints are only available during quizzes.", ephemeral=True)

        if session.hints_remaining <= 0:
            return await interaction.followup.send("❌ No hints remaining!", ephemeral=True)

        session.hints_remaining -= 1

        user = await UserProfile.get_user(session.user_id)
        await UserProfile.update_user(session.user_id, {
            "learn_hints_used": user.get("learn_hints_used", 0) + 1
        })

        await save_session_state(session)

        lesson = get_lesson(session.lesson_number)
        hint = await self.cog.generate_hint(lesson, session.quiz_data)

        embed = discord.Embed(title="💡 Hint", description=hint, color=discord.Color.gold())
        embed.set_footer(text=f"Hints remaining: {session.hints_remaining}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="quiz:skip_btn")
    async def skip_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        session = await self.cog.get_or_rebuild_session(interaction)

        if session.phase not in {"quiz", "final_test"}:
            return await interaction.followup.send("⏭️ Skip is only available during quizzes.", ephemeral=True)

        await self.cog.handle_quiz_skip(interaction.channel, session)


# -----------------------------
# Learn Cog
# -----------------------------
class LearnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_or_rebuild_session(self, interaction: discord.Interaction) -> LearnSession:
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
        except (ValueError, IndexError):
            owner_id = interaction.user.id

        return await rebuild_session_from_db(ch, owner_id)

    async def send_panel(self, channel: discord.TextChannel, user_id: int):
        user = await ensure_learn_fields(user_id, "Unknown")
        total = len(LESSONS) if LESSONS else 50
        lesson_number = max(1, min(_safe_int(user.get("learn_lesson", 1)), total))

        lesson = get_lesson(lesson_number)
        stats = await get_progress_stats(user_id)

        filled = int(stats['progress_percent'] / 10)
        bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title="📚 Learning Control Panel",
            description=(
                f"**Progress:** `[{bar}]` {stats['progress_percent']}%\n"
                f"**Streak:** 🔥 {stats['streak']} days • **Accuracy:** 🎯 {stats['accuracy']}%\n\n"
                "**📝 Text Commands:**\n"
                "• `start lesson` / `next lesson` / `repeat lesson`\n"
                "• `hint` — Get a quiz hint\n"
                "• `my progress` / `my weaknesses`\n"
                "• `review <number>` — Review a specific lesson\n"
                "• `cheat sheet` / `practice`\n"
                "• `final test` — Graduation exam (45+ lessons required)\n"
                "• `switch to coder` / `switch to explain` / `switch to auto`"
            ),
            color=BOT_COLOR
        )
        if lesson:
            prereqs = lesson.get('prerequisites', [])
            prereq_text = ", ".join([str(p) for p in prereqs]) if prereqs else "None"
            embed.add_field(
                name=f"📖 Lesson {lesson_number}/{total}",
                value=(
                    f"**{lesson['title']}**\n"
                    f"Phase: {lesson.get('phase', '')} • Difficulty: {lesson.get('difficulty', '')}\n"
                    f"Prerequisites: {prereq_text}"
                ),
                inline=False
            )

        msg = await channel.send(embed=embed, view=LearnPersistentPanel(self))
        await UserProfile.update_user(user_id, {"learn_panel_message_id": msg.id})

    # =====================================================
    # LESSON SENDING - MULTI-PART
    # =====================================================

    async def send_lesson(self, channel: discord.TextChannel, session: LearnSession, repeat: bool = False):
        lesson = get_lesson(session.lesson_number)
        if not lesson:
            return await channel.send("❌ Lesson not found.")

        # Reset session state
        session.phase = "qna"
        session.quiz_data = {}
        session.quiz_questions = []
        session.current_quiz_index = 0
        session.hints_remaining = 3
        session.lesson_part = 0

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

        objectives_text = "\n".join([f"✓ {obj}" for obj in lesson.get('learning_objectives', [])[:6]])

        header_embed = discord.Embed(
            title=title,
            description=(
                f"**Phase:** {lesson.get('phase', 'N/A')} • "
                f"**Difficulty:** {lesson.get('difficulty', 'N/A')} • "
                f"**Time:** {lesson.get('estimated_time', 'N/A')}\n\n"
                f"**🎯 What You'll Learn:**\n{objectives_text}"
            ),
            color=BOT_COLOR
        )
        await channel.send(embed=header_embed)
        await channel.send("📚 **Loading lesson content...**")

        # Part 1: Introduction
        await self._send_lesson_introduction(channel, session, lesson)
        await asyncio.sleep(1)

        # Part 2+: Subtopics in chunks
        subtopics = lesson.get("subtopics", [])
        chunk_size = 2
        for i in range(0, len(subtopics), chunk_size):
            chunk = subtopics[i:i + chunk_size]
            part_num = (i // chunk_size) + 2
            await self._send_lesson_subtopics(channel, session, lesson, chunk, part_num)
            await asyncio.sleep(1)

        # Final: Conclusion
        await self._send_lesson_conclusion(channel, session, lesson)

        await append_conversation(session.user_id, "assistant", f"{title} — Lesson delivered")

        # Q&A Prompt
        qna_embed = discord.Embed(
            title="🤔 Any Questions?",
            description=(
                "**Ask anything about this lesson or previous ones!**\n\n"
                "• Type your question naturally\n"
                "• Type `no` or `quiz` to start the quiz\n"
                "• Type `cheat sheet` for a quick reference\n"
            ),
            color=discord.Color.blue()
        )
        await channel.send(embed=qna_embed)

    async def _send_lesson_introduction(self, channel: discord.TextChannel, session: LearnSession, lesson: dict):
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        system = """You are an expert Roblox Lua/Luau teacher.
Write a COMPREHENSIVE introduction for the lesson:

## 🎯 HOOK
Start with an engaging question or scenario to grab attention.

## 📚 WHAT IS IT? (3-4 paragraphs)
Define the concept for complete beginners using real-world analogies.

## 🤔 WHY IS THIS IMPORTANT? (2 paragraphs)
Explain why every Roblox developer needs to know this.

## 🎮 REAL GAME EXAMPLES
Show how popular Roblox games use this concept.

## ✨ AFTER THIS LESSON YOU CAN:
List 4-5 concrete things the student will be able to build.

Make it EXCITING and beginner-friendly! Use Roblox-specific examples."""

        user_msg = f"""Write an introduction for Lesson {lesson['n']}: {lesson['title']}
Keywords: {', '.join(lesson['keywords'])}
Real-world application: {lesson.get('real_world', '')}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                model_pool=model_pool,
                max_tokens=1000,
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
        if not subtopics:
            return

        model_pool = get_model_pool(session.model_mode, lesson['title'])

        subtopics_text = ""
        for st in subtopics:
            subtopics_text += f"""
### SUBTOPIC: {st['name']}
Description: {st['description']}
Required examples: {st['examples']}

You MUST include:
1. Detailed explanation (6-8 sentences minimum)
2. {st['examples']} code examples with comments on EVERY line
3. When and why to use this
4. Common mistakes to avoid
"""

        system = """You are an expert Roblox Lua/Luau teacher.
Explain each subtopic thoroughly:
- Beginner-friendly language with real-world analogies
- EVERY code line needs a descriptive comment
- Use real Roblox game examples
- Use ```lua code blocks
- Be detailed and comprehensive"""

        user_msg = f"""Explain these subtopics from Lesson {lesson['n']}: {lesson['title']}
{subtopics_text}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                model_pool=model_pool,
                max_tokens=1500,
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
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        mistakes = lesson.get("common_mistakes", [])
        mistakes_text = "\n".join([f"• {m}" for m in mistakes])

        system = """You are an expert teacher finishing a lesson.

Write the following sections:

## ⚠️ COMMON MISTAKES
For each mistake: show the WRONG code, explain why it's wrong, then show the CORRECT code.

## 💡 PRO TIPS (5-6 tips)
Each with a short code example showing best practices.

## 🔧 MINI PROJECT
A hands-on project that uses all concepts from this lesson. Include complete starter code with comments.

## 📝 SUMMARY
6-8 bullet points summarizing the key takeaways, plus a quick reference table."""

        user_msg = f"""Finish Lesson {lesson['n']}: {lesson['title']}
Common mistakes to cover: {mistakes_text}
Mini project idea: {lesson.get('mini_project', 'Practice exercise')}"""

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                model_pool=model_pool,
                max_tokens=1500,
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
        requirements = "\n".join([f"✅ {req}" for req in lesson.get("project_requirements", [])])

        is_final = lesson.get("is_final", False)
        model_pool = get_model_pool(session.model_mode, lesson['title'])

        if is_final:
            weakness = await get_weakness_analysis(session.user_id)
            stats = await get_progress_stats(session.user_id)
            weak_text = ", ".join([k for k, v in weakness["weaknesses"][:5]]) or "None"

            system = """You are guiding a student through their FINAL GRADUATION PROJECT.
Include:
- A celebration of how far they've come
- Personalized analysis based on their stats
- A complete game design guide
- Code architecture recommendations
- Publishing tips and best practices
- Encouragement to keep learning"""

            user_msg = f"""Final graduation project for student:
Stats: {stats['completed_count']} lessons completed, {stats['accuracy']}% accuracy
Weak areas to focus on: {weak_text}
Requirements:\n{requirements}"""
        else:
            system = """You are guiding a student through a practical project.
Provide step-by-step instructions with complete, well-commented code.
Break the project into clear phases."""

            user_msg = f"""Project: {lesson['title']}\nRequirements:\n{requirements}"""

        await channel.send("🔨 **Generating project guide...**")

        async with channel.typing():
            content = await openrouter_chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                model_pool=model_pool,
                max_tokens=3500,
            )

        await append_conversation(session.user_id, "assistant", f"PROJECT: {content[:1500]}")

        parts = self._split_content(content, 3900)
        for part in parts:
            embed = discord.Embed(
                title=f"{'🎓 GRADUATION ' if is_final else '🔨 '}Project: {lesson['title']}",
                description=part,
                color=discord.Color.gold() if is_final else BOT_COLOR
            )
            await channel.send(embed=embed)

        session.phase = "quiz"
        await save_session_state(session)

        await channel.send(
            "📋 **When you're done, describe what you built!**\n"
            "Type `skip` to move on to the quiz."
        )

    def _split_content(self, content: str, max_length: int) -> List[str]:
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
        system = (
            "You are a helpful tutor. Give a useful hint that guides the student "
            "toward the answer WITHOUT revealing it directly. Keep it to 2-3 sentences."
        )
        user_msg = (
            f"Quiz question: {quiz.get('question', '')}\n"
            f"Correct answer: {quiz.get('answer', '')}\n"
            f"Topic: {lesson['title'] if lesson else 'Unknown'}"
        )

        return await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=200,
        )

    async def generate_quiz(self, session: LearnSession, num_questions: int = 3) -> List[dict]:
        lesson = get_lesson(session.lesson_number)
        if not lesson:
            return [{"question": "Explain what you learned.", "type": "concept", "answer": "", "difficulty": "medium", "related_keywords": []}]

        weakness = await get_weakness_analysis(session.user_id)
        weak_topics = [k for k, v in weakness["weaknesses"][:5]]

        system = (
            "You are a quiz generator for Roblox Lua/Luau lessons. "
            "Create quiz questions. Return ONLY a valid JSON array, nothing else."
        )
        user_msg = f"""Create {num_questions} questions for Lesson {lesson['n']}: {lesson['title']}
Keywords: {', '.join(lesson['keywords'])}
{"Focus on weak areas: " + ', '.join(weak_topics) if weak_topics else "General coverage"}

Return format: [{{"question": "...", "type": "output|fix|concept|choice", "options": null or ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "...", "explanation": "...", "difficulty": "easy|medium|hard", "related_keywords": [...]}}]"""

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=2000,
        )

        try:
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                questions = json.loads(match.group(0))
                if isinstance(questions, list) and questions:
                    return questions
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback question
        return [{
            "question": f"Explain the key concepts of {lesson['title']} with a code example.",
            "type": "concept",
            "answer": "",
            "explanation": "",
            "difficulty": "medium",
            "related_keywords": lesson['keywords'][:3]
        }]

    async def grade_quiz_answer(self, session: LearnSession, quiz: dict, user_answer: str) -> dict:
        model_pool = get_model_pool(session.model_mode, user_answer)

        system = (
            "You are a fair quiz grader. Grade the student's answer. "
            'Return ONLY valid JSON: {"correct": bool, "partial": bool, "score": 0-100, '
            '"feedback": "encouraging feedback", "correct_answer": "the correct answer"}'
        )
        user_msg = (
            f"Question: {quiz.get('question', '')}\n"
            f"Expected answer: {quiz.get('answer', '')}\n"
            f"Student's answer: {user_answer}"
        )

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            model_pool=model_pool,
            max_tokens=400,
        )

        try:
            data = extract_json(raw)
            if data and "correct" in data:
                return data
        except (TypeError, KeyError):
            pass

        return {
            "correct": False,
            "partial": False,
            "score": 0,
            "feedback": "Could not grade automatically. Please try rephrasing your answer.",
            "correct_answer": quiz.get("answer", "")
        }

    async def ai_answer_question(self, session: LearnSession, question: str) -> str:
        current = get_lesson(session.lesson_number)
        model_pool = get_model_pool(session.model_mode, question)

        context = []
        for i in range(1, min(session.lesson_number + 5, len(LESSONS) + 1)):
            l = get_lesson(i)
            if l:
                context.append(f"Lesson {l['n']}: {l['title']}")

        current_title = current['title'] if current else 'Unknown'
        system = f"""You are a helpful Roblox Lua/Luau tutor.
The student is currently on Lesson {session.lesson_number}: {current_title}
Lessons covered so far: {', '.join(context[:15])}

Answer ANY question about Lua/Luau or Roblox development.
Include code examples when relevant. Use ```lua blocks.
Be encouraging and thorough!"""

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

        system = (
            "Create a comprehensive 10-question final exam covering all Roblox Lua/Luau topics. "
            "Return ONLY a valid JSON array."
        )
        user_msg = (
            f"Focus especially on weak areas: {', '.join(weak_topics) if weak_topics else 'general review of all topics'}\n"
            "Include mix of: output prediction, bug fixing, concept explanation, and multiple choice.\n"
            'Format: [{{"question": "...", "type": "...", "options": null or [...], "answer": "...", '
            '"explanation": "...", "points": 10, "related_keywords": [...]}}]'
        )

        raw = await openrouter_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            model_pool=EXPLAIN_MODELS,
            max_tokens=3000,
        )

        try:
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                questions = json.loads(match.group(0))
                if isinstance(questions, list) and questions:
                    return questions
        except (json.JSONDecodeError, TypeError):
            pass

        return [{
            "question": "Explain client-server architecture and why you should never trust the client.",
            "type": "concept",
            "answer": "",
            "points": 10,
            "related_keywords": ["client", "server", "security"]
        }]

    # =====================================================
    # QUIZ HANDLING
    # =====================================================

    async def handle_quiz_skip(self, channel: discord.TextChannel, session: LearnSession):
        quiz = session.quiz_data
        lesson = get_lesson(session.lesson_number)

        keywords = quiz.get("related_keywords", lesson.get("keywords", []) if lesson else [])
        await track_weakness(session.user_id, keywords, False)

        embed = discord.Embed(
            title="⏭️ Question Skipped",
            description=f"**Correct Answer:** {quiz.get('answer', 'N/A')}",
            color=discord.Color.orange()
        )
        if quiz.get("explanation"):
            embed.add_field(name="📝 Explanation", value=quiz['explanation'][:1000], inline=False)
        await channel.send(embed=embed)

        await append_conversation(session.user_id, "assistant", f"SKIPPED — Answer: {quiz.get('answer', '')}")

        await self._advance_quiz(channel, session)

    async def _advance_quiz(self, channel: discord.TextChannel, session: LearnSession):
        if session.quiz_questions and session.current_quiz_index < len(session.quiz_questions) - 1:
            session.current_quiz_index += 1
            session.quiz_data = session.quiz_questions[session.current_quiz_index]
            session.hints_remaining = 3

            await save_session_state(session)

            await asyncio.sleep(1.5)

            total = len(session.quiz_questions)
            q = session.quiz_data

            embed = discord.Embed(
                title=f"🧩 Question {session.current_quiz_index + 1}/{total}",
                description=q.get("question", ""),
                color=BOT_COLOR
            )
            embed.add_field(name="Type", value=q.get("type", "concept").title(), inline=True)
            embed.add_field(name="Difficulty", value=q.get("difficulty", "medium").title(), inline=True)
            embed.add_field(name="💡 Hints", value=str(session.hints_remaining), inline=True)

            if q.get("options"):
                embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

            await channel.send(embed=embed, view=QuizControlView(self, session))
        else:
            await self._complete_quiz(channel, session)

    async def _complete_quiz(self, channel: discord.TextChannel, session: LearnSession):
        lesson = get_lesson(session.lesson_number)

        # Mark lesson as completed
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

        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)
        filled = int(stats['progress_percent'] / 10)
        bar = "█" * filled + "░" * (10 - filled)

        lesson_title = lesson['title'] if lesson else 'Unknown'

        embed = discord.Embed(
            title="🎉 Lesson Complete!",
            description=f"**Lesson {session.lesson_number}: {lesson_title}** ✅",
            color=discord.Color.green()
        )
        embed.add_field(name="📈 Progress", value=f"`[{bar}]` {stats['progress_percent']}%", inline=False)
        embed.add_field(name="🔥 Streak", value=f"{stats['streak']} days", inline=True)
        embed.add_field(name="🎯 Accuracy", value=f"{stats['accuracy']}%", inline=True)
        embed.add_field(name="📚 Completed", value=f"{stats['completed_count']}/{stats['total_lessons']}", inline=True)

        if session.lesson_number < len(LESSONS):
            next_l = get_lesson(session.lesson_number + 1)
            if next_l:
                embed.add_field(
                    name="📖 Up Next",
                    value=f"Lesson {next_l['n']}: **{next_l['title']}**\nClick **Next Lesson** or type `next lesson`",
                    inline=False
                )
        else:
            embed.add_field(
                name="🎓 Congratulations!",
                value="All lessons complete! Type `final test` to take the graduation exam!",
                inline=False
            )

        await channel.send(embed=embed)

    async def _start_quiz(self, channel: discord.TextChannel, session: LearnSession):
        lesson = get_lesson(session.lesson_number)

        session.phase = "quiz"
        session.hints_remaining = 3

        await channel.send("🧩 **Generating quiz questions...**")

        async with channel.typing():
            questions = await self.generate_quiz(session, 3)

        session.quiz_questions = questions
        session.current_quiz_index = 0
        session.quiz_data = questions[0] if questions else {}

        await save_session_state(session)

        await asyncio.sleep(1)

        q = session.quiz_data
        total = len(questions)

        embed = discord.Embed(
            title=f"🧩 Quiz — Question 1/{total}",
            description=q.get("question", ""),
            color=BOT_COLOR
        )
        embed.add_field(name="Type", value=q.get("type", "concept").title(), inline=True)
        embed.add_field(name="Difficulty", value=q.get("difficulty", "medium").title(), inline=True)
        embed.add_field(name="💡 Hints", value=str(session.hints_remaining), inline=True)

        if q.get("options"):
            embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

        embed.set_footer(text="Type your answer • Use hint/skip buttons • Ask questions with ?")
        await channel.send(embed=embed, view=QuizControlView(self, session))

    # =====================================================
    # FINAL TEST
    # =====================================================

    async def _start_final_test(self, channel: discord.TextChannel, session: LearnSession):
        session.phase = "final_test"
        session.hints_remaining = 5

        await channel.send("🎓 **Generating your FINAL EXAM...**")

        async with channel.typing():
            questions = await self.generate_final_test(session)

        session.quiz_questions = questions
        session.current_quiz_index = 0
        session.quiz_data = questions[0] if questions else {}

        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)

        embed = discord.Embed(
            title="🎓 FINAL GRADUATION EXAM",
            description=(
                f"**{len(questions)} questions** • **5 hints** • Based on YOUR weak areas\n\n"
                f"📚 Lessons completed: {stats['completed_count']}\n"
                f"🎯 Current accuracy: {stats['accuracy']}%\n\n"
                "**Good luck! You've got this! 💪**"
            ),
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)

        await asyncio.sleep(2)

        q = session.quiz_data
        q_embed = discord.Embed(
            title=f"📝 Question 1/{len(questions)}",
            description=q.get("question", ""),
            color=BOT_COLOR
        )
        q_embed.add_field(name="Type", value=q.get("type", "concept").title(), inline=True)
        q_embed.add_field(name="💡 Hints", value=str(session.hints_remaining), inline=True)

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
            embed = discord.Embed(
                title="✅ Correct!",
                description=grade.get("feedback", "Great job!"),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Incorrect",
                description=grade.get("feedback", ""),
                color=discord.Color.red()
            )
            embed.add_field(
                name="Correct Answer",
                value=grade.get('correct_answer', quiz.get('answer', 'N/A')),
                inline=False
            )
        await channel.send(embed=embed)

        # Next question or graduate
        if session.current_quiz_index < len(session.quiz_questions) - 1:
            session.current_quiz_index += 1
            session.quiz_data = session.quiz_questions[session.current_quiz_index]

            await save_session_state(session)

            await asyncio.sleep(2)

            q = session.quiz_data
            total = len(session.quiz_questions)
            q_embed = discord.Embed(
                title=f"📝 Question {session.current_quiz_index + 1}/{total}",
                description=q.get("question", ""),
                color=BOT_COLOR
            )
            q_embed.add_field(name="Type", value=q.get("type", "concept").title(), inline=True)
            q_embed.add_field(name="💡 Hints", value=str(session.hints_remaining), inline=True)

            if q.get("options"):
                q_embed.add_field(name="Options", value="\n".join(q["options"]), inline=False)

            await channel.send(embed=q_embed, view=QuizControlView(self, session))
        else:
            await self._graduate_user(channel, session)

    async def _graduate_user(self, channel: discord.TextChannel, session: LearnSession):
        # Mark lesson 50 as completed
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

        await save_session_state(session)

        stats = await get_progress_stats(session.user_id)

        # Celebration!
        await channel.send("🎆" * 10)

        embed = discord.Embed(
            title="🎓🎉 CONGRATULATIONS! YOU GRADUATED! 🎉🎓",
            description=(
                "# 🏆 You Did It!\n\n"
                f"📚 **{stats['completed_count']}** lessons completed\n"
                f"🎯 **{stats['accuracy']}%** overall accuracy\n"
                f"🔥 **{stats['streak']}** day learning streak\n"
                f"💡 **{stats.get('hints_used', 0)}** hints used\n\n"
                "**You are now a Roblox Lua/Luau Developer!**\n\n"
                "Keep building, keep learning, and most importantly — have fun creating amazing games! 🎮✨"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Thank you for learning with us! 💙")
        await channel.send(embed=embed)

        await append_conversation(session.user_id, "assistant", "🎓 GRADUATED! Congratulations!")

        await channel.send("🎊 **NOW GO BUILD AMAZING GAMES!** 🎊")

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
        except (ValueError, IndexError):
            return

        if message.author.id != owner_id:
            return

        session = SESSIONS.get(message.channel.id) or await rebuild_session_from_db(message.channel, owner_id)

        raw = message.content.strip()
        content = norm(raw)

        await append_conversation(owner_id, "user", raw)

        # ===== TEXT COMMANDS FIRST =====
        if content in TEXT_COMMANDS:
            await self._handle_text_command(message.channel, session, content)
            return

        # ===== REVIEW COMMAND =====
        if content.startswith("review "):
            try:
                num = int(content.split("review ", 1)[1])
                if 1 <= num <= len(LESSONS):
                    old = session.lesson_number
                    session.lesson_number = num
                    await self.send_lesson(message.channel, session, repeat=True)
                    session.lesson_number = old
                    await save_session_state(session)
                else:
                    await message.channel.send(f"❌ Lesson number must be between 1 and {len(LESSONS)}.")
            except (ValueError, IndexError):
                await message.channel.send("Usage: `review 5`")
            return

        # ===== PHASE-BASED HANDLING =====
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

            await message.channel.send("_Have more questions? Type `no` or `quiz` to start the quiz._")
            return

        if session.phase == "quiz":
            quiz = session.quiz_data

            # Allow questions during quiz
            if raw.endswith("?") or content.startswith(("what", "why", "how", "explain", "can you")):
                answer = await self.ai_answer_question(session, raw)
                await message.channel.send(answer[:1900])
                await message.channel.send("_Now answer the quiz question above!_")
                return

            # Grade the answer
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
                embed = discord.Embed(
                    title="✅ Correct!",
                    description=grade.get("feedback", "Well done!"),
                    color=discord.Color.green()
                )
                if grade.get("score", 0) == 100:
                    embed.set_footer(text="⭐ Perfect answer!")
                await message.channel.send(embed=embed)
                await self._advance_quiz(message.channel, session)
            elif grade.get("partial"):
                embed = discord.Embed(
                    title="🟡 Partially Correct",
                    description=grade.get("feedback", "You're on the right track!"),
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Try again for full marks • Use 'hint' for help")
                await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Not Quite",
                    description=grade.get("feedback", "Keep trying!"),
                    color=discord.Color.red()
                )
                embed.set_footer(text="Try again • Type 'hint' for help • Type 'skip' to see the answer")
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
            await message.channel.send(
                "📚 Type `start lesson` to begin, or use the buttons on the control panel above!"
            )

    async def _handle_text_command(self, channel: discord.TextChannel, session: LearnSession, content: str):
        owner_id = session.user_id
        lesson = get_lesson(session.lesson_number)

        # ===== MODEL SWITCHING =====
        if content in {"switch to coder", "model coder"}:
            session.model_mode = "coder"
            await save_session_state(session)
            await channel.send("✅ Switched to **CODER** mode — optimized for code generation and debugging.")
            return

        if content in {"switch to explain", "model explain"}:
            session.model_mode = "explain"
            await save_session_state(session)
            await channel.send("✅ Switched to **EXPLAIN** mode — optimized for explanations and concepts.")
            return

        if content in {"switch to auto", "model auto"}:
            session.model_mode = "auto"
            await save_session_state(session)
            await channel.send("✅ Switched to **AUTO** mode — automatically picks the best model for each request.")
            return

        # ===== PANEL =====
        if content in {"refresh panel", "panel"}:
            await self.send_panel(channel, owner_id)
            return

        # ===== LESSON CONTROL =====
        if content in {"start lesson", "start"} and session.phase == "menu":
            await self.send_lesson(channel, session)
            return

        if content in {"repeat lesson", "repeat"}:
            await self.send_lesson(channel, session, repeat=True)
            return

        if content in {"next lesson", "next"} and session.phase == "menu":
            if session.lesson_number >= len(LESSONS):
                await channel.send("🎉 All lessons complete! Type `final test` to take the graduation exam!")
                return
            session.lesson_number += 1
            session.phase = "menu"
            await save_session_state(session)
            next_l = get_lesson(session.lesson_number)
            next_title = next_l['title'] if next_l else 'Unknown'
            await channel.send(
                f"📖 **Lesson {session.lesson_number}: {next_title}**\n"
                f"Type `start lesson` or click **Start Lesson** to begin!"
            )
            return

        # ===== PROGRESS =====
        if content in {"my progress", "progress", "stats"}:
            stats = await get_progress_stats(owner_id)
            weakness = await get_weakness_analysis(owner_id)

            filled = int(stats['progress_percent'] / 10)
            bar = "█" * filled + "░" * (10 - filled)

            embed = discord.Embed(title="📊 Your Progress", color=BOT_COLOR)
            embed.add_field(name="Overall", value=f"`[{bar}]` {stats['progress_percent']}%", inline=False)
            embed.add_field(name="📚 Lessons", value=f"{stats['completed_count']}/{stats['total_lessons']}", inline=True)
            embed.add_field(name="🔥 Streak", value=f"{stats['streak']} days", inline=True)
            embed.add_field(name="🎯 Accuracy", value=f"{stats['accuracy']}%", inline=True)

            if weakness["weaknesses"]:
                weak_text = ", ".join([f"`{k}`" for k, v in weakness["weaknesses"][:5]])
                embed.add_field(name="⚠️ Weak Topics", value=weak_text, inline=False)
            if weakness["strengths"]:
                strong_text = ", ".join([f"`{k}`" for k, v in weakness["strengths"][:5]])
                embed.add_field(name="💪 Strong Topics", value=strong_text, inline=False)

            await channel.send(embed=embed)
            return

        # ===== WEAKNESS ANALYSIS =====
        if content in {"my weaknesses", "weakness analysis", "analyze"}:
            weakness = await get_weakness_analysis(owner_id)
            embed = discord.Embed(title="⚠️ Weakness Analysis", color=discord.Color.orange())
            if weakness["weaknesses"]:
                desc_lines = []
                for k, v in weakness["weaknesses"][:10]:
                    bar_len = min(v, 10)
                    desc_lines.append(f"• **{k}**: {'🟥' * bar_len} ({v} mistakes)")
                embed.description = "\n".join(desc_lines)
            else:
                embed.description = "No weaknesses detected yet! Keep taking quizzes."

            if weakness["strengths"]:
                strong_lines = [f"• **{k}**: ✅ ({v} correct)" for k, v in weakness["strengths"][:5]]
                embed.add_field(name="💪 Your Strengths", value="\n".join(strong_lines), inline=False)

            await channel.send(embed=embed)
            return

        # ===== HINTS =====
        if content in {"hint", "get hint", "help"}:
            if session.phase not in {"quiz", "final_test"}:
                await channel.send("💡 Hints are only available during quizzes! Start a quiz first.")
                return
            if session.hints_remaining <= 0:
                await channel.send("❌ No hints remaining for this question!")
                return

            session.hints_remaining -= 1
            user = await UserProfile.get_user(owner_id)
            await UserProfile.update_user(owner_id, {"learn_hints_used": user.get("learn_hints_used", 0) + 1})
            await save_session_state(session)

            hint = await self.generate_hint(lesson, session.quiz_data)
            embed = discord.Embed(title="💡 Hint", description=hint, color=discord.Color.gold())
            embed.set_footer(text=f"Hints remaining: {session.hints_remaining}")
            await channel.send(embed=embed)
            return

        # ===== CHEAT SHEET =====
        if content in {"cheat sheet", "cheatsheet", "reference"}:
            model_pool = get_model_pool(session.model_mode, "")
            lesson_title = lesson['title'] if lesson else 'current topic'

            async with channel.typing():
                cheat = await openrouter_chat(
                    [
                        {"role": "system", "content": "Create a concise cheat sheet with key syntax and code snippets. Use ```lua blocks."},
                        {"role": "user", "content": f"Quick reference cheat sheet for: {lesson_title}"}
                    ],
                    model_pool=model_pool,
                    max_tokens=800
                )

            embed = discord.Embed(
                title=f"📋 Cheat Sheet: {lesson_title}",
                description=cheat[:4000],
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            await append_conversation(owner_id, "assistant", f"CHEAT SHEET: {cheat[:1000]}")
            return

        # ===== BOOKMARKS =====
        if content in {"bookmark", "save"}:
            user = await UserProfile.get_user(owner_id)
            bookmarks = user.get("learn_bookmarks", [])
            if session.lesson_number not in bookmarks:
                bookmarks.append(session.lesson_number)
                await UserProfile.update_user(owner_id, {"learn_bookmarks": bookmarks})
                lesson_title = lesson['title'] if lesson else 'Unknown'
                await channel.send(f"🔖 Bookmarked **Lesson {session.lesson_number}: {lesson_title}**!")
            else:
                await channel.send("🔖 This lesson is already bookmarked!")
            return

        if content in {"bookmarks", "my bookmarks"}:
            user = await UserProfile.get_user(owner_id)
            bookmarks = user.get("learn_bookmarks", [])
            if bookmarks:
                lines = []
                for n in sorted(bookmarks):
                    l = get_lesson(n)
                    if l:
                        lines.append(f"• **Lesson {n}:** {l['title']}")
                embed = discord.Embed(
                    title="🔖 Your Bookmarks",
                    description="\n".join(lines),
                    color=BOT_COLOR
                )
                embed.set_footer(text="Type 'review <number>' to revisit a lesson")
                await channel.send(embed=embed)
            else:
                await channel.send("🔖 No bookmarks yet! Type `bookmark` during a lesson to save it.")
            return

        # ===== PRACTICE =====
        if content in {"practice", "exercises"}:
            model_pool = get_model_pool(session.model_mode, "")
            lesson_title = lesson['title'] if lesson else 'current topic'

            async with channel.typing():
                exercise = await openrouter_chat(
                    [
                        {"role": "system", "content": "Create a hands-on coding exercise with clear requirements and starter code. Use ```lua blocks."},
                        {"role": "user", "content": f"Practice exercise for: {lesson_title}"}
                    ],
                    model_pool=model_pool,
                    max_tokens=1000
                )

            embed = discord.Embed(
                title=f"💪 Practice: {lesson_title}",
                description=exercise[:4000],
                color=discord.Color.green()
            )
            embed.set_footer(text="Try it in Roblox Studio!")
            await channel.send(embed=embed)
            await append_conversation(owner_id, "assistant", f"PRACTICE: {exercise[:1000]}")
            return

        # ===== SKIP (during quiz) =====
        if content in {"skip", "next question"} and session.phase in {"quiz", "final_test"}:
            await self.handle_quiz_skip(channel, session)
            return

        # ===== FINAL TEST =====
        if content in {"final test"}:
            user = await UserProfile.get_user(owner_id)
            completed_count = len(user.get("learn_completed_lessons", []))
            if completed_count < 45:
                await channel.send(
                    f"📚 You need at least **45** completed lessons to take the final test.\n"
                    f"You currently have **{completed_count}** completed. Keep going!"
                )
                return
            await self._start_final_test(channel, session)
            return

        # ===== QUIZ START FROM QNA =====
        if content in {"no", "nope", "nah", "n", "quiz", "start quiz"} and session.phase == "qna":
            await self._start_quiz(channel, session)
            return


# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    # Remove old command if exists
    try:
        bot.tree.remove_command("learn")
    except Exception:
        pass

    cog = LearnCog(bot)
    await bot.add_cog(cog)

    # Register persistent views (survive bot restarts)
    bot.add_view(LearnPersistentPanel(cog))
    bot.add_view(QuizControlView(cog))

    @bot.tree.command(name="learn", description="Start learning Roblox Lua/Luau — 50 comprehensive lessons!")
    async def learn_cmd(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            return await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)

        if not interaction.guild.me.guild_permissions.manage_channels:
            return await interaction.followup.send(
                "❌ I need the **Manage Channels** permission to create your learning channel.",
                ephemeral=True
            )

        await ensure_learn_fields(interaction.user.id, interaction.user.name)

        channel_name = f"learn-{interaction.user.id}"
        existing = discord.utils.get(interaction.guild.text_channels, name=channel_name)

        if existing:
            await cog.send_panel(existing, interaction.user.id)
            return await interaction.followup.send(
                f"✅ Your learning channel: {existing.mention}\nPanel refreshed!",
                ephemeral=True
            )

        # Create private learning channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
        }

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
        await UserProfile.update_user(interaction.user.id, {"learn_channel_id": channel.id})

        session = await rebuild_session_from_db(channel, interaction.user.id)
        SESSIONS[channel.id] = session

        # Welcome message
        welcome = discord.Embed(
            title="🎮 Welcome to Roblox Lua/Luau Learning!",
            description=(
                "**50 comprehensive lessons** from beginner to expert!\n\n"
                "📚 **5 Phases:**\n"
                "1️⃣ Fundamentals (Lessons 1-12)\n"
                "2️⃣ Intermediate (Lessons 13-24)\n"
                "3️⃣ Advanced (Lessons 25-36)\n"
                "4️⃣ Expert (Lessons 37-45)\n"
                "5️⃣ Mastery Projects (Lessons 46-50)\n\n"
                "Click **Start Lesson** below to begin! 🚀"
            ),
            color=BOT_COLOR
        )
        welcome.set_footer(text="Your progress is saved automatically. Have fun learning!")
        await channel.send(embed=welcome)
        await cog.send_panel(channel, interaction.user.id)

        await interaction.followup.send(
            f"✅ Created your learning channel: {channel.mention}\nHappy learning! 🎉",
            ephemeral=True
        )