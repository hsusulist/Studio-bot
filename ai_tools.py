import re
import asyncio
import json
import os
from datetime import datetime


class SplitMessageTool:
    def __init__(self):
        self.max_length = 1950

    def needs_split(self, content):
        return len(content) > self.max_length

    def split_content(self, content):
        if not self.needs_split(content):
            return [content]

        chunks = []
        remaining = content
        is_first = True
        safety = 0

        while remaining and safety < 50:
            safety += 1

            if len(remaining) <= self.max_length:
                prefix = "" if is_first else "*(continued...)*\n"
                final = prefix + remaining
                if len(final) <= self.max_length:
                    chunks.append(final)
                    break

            effective_max = self.max_length
            if not is_first:
                effective_max -= 20

            split_at = self._find_split(remaining, effective_max)
            chunk = remaining[:split_at].rstrip()
            remaining = remaining[split_at:].lstrip()

            if not is_first:
                chunk = "*(continued...)*\n" + chunk

            chunks.append(chunk)
            is_first = False

        return chunks

    def _find_split(self, text, max_len):
        if len(text) <= max_len:
            return len(text)
        for sep in ["\n\n", "\n", ". ", ", ", " "]:
            idx = text[:max_len].rfind(sep)
            if idx > max_len * 0.3:
                return idx + len(sep)
        return max_len

    async def send_split(self, message, content, reply=True):
        chunks = self.split_content(content)
        sent = []
        for i, chunk in enumerate(chunks):
            try:
                if i == 0 and reply:
                    msg = await message.reply(chunk)
                else:
                    msg = await message.channel.send(chunk)
                sent.append(msg)
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
            except Exception as e:
                if "2000" in str(e):
                    half = len(chunk) // 2
                    try:
                        msg = await message.channel.send(chunk[:half])
                        sent.append(msg)
                        await asyncio.sleep(0.5)
                        msg = await message.channel.send(chunk[half:])
                        sent.append(msg)
                    except Exception:
                        pass
                else:
                    raise e
        return sent


class CodeThreadTool:
    def __init__(self):
        self.min_code_length = 50
        self.max_msg_length = 1900

    def detect_code_blocks(self, content):
        blocks = []
        pattern = r"```(\w*)\n([\s\S]*?)```"
        for match in re.finditer(pattern, content):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            if len(code) >= self.min_code_length:
                blocks.append({
                    "full_match": match.group(0),
                    "language": lang,
                    "code": code,
                    "start": match.start(),
                    "end": match.end()
                })
        return blocks

    def has_significant_code(self, content):
        return len(self.detect_code_blocks(content)) > 0

    def extract_code_and_text(self, content):
        blocks = self.detect_code_blocks(content)
        if not blocks:
            return content, []
        text = content
        tag = "*(Code in thread below)*"
        for block in reversed(blocks):
            text = text[:block["start"]] + tag + text[block["end"]:]
        while tag + "\n" + tag in text:
            text = text.replace(tag + "\n" + tag, tag)
        while tag + "\n\n" + tag in text:
            text = text.replace(tag + "\n\n" + tag, tag)
        return text.strip(), blocks

    async def create_code_thread(self, bot_message, code_blocks, user_name):
        try:
            ts = datetime.now().strftime("%H:%M")
            name = "Code | " + user_name[:20] + " | " + ts
            thread = await bot_message.create_thread(name=name, auto_archive_duration=60)
            for i, block in enumerate(code_blocks):
                header = ""
                if i == 0:
                    header = "**Here's the code:**\n"
                if len(code_blocks) > 1:
                    header += "**Block " + str(i + 1) + "/" + str(len(code_blocks)) + "** (`" + block["language"] + "`):\n"
                full = header + "```" + block["language"] + "\n" + block["code"] + "\n```"
                if len(full) > self.max_msg_length:
                    if header:
                        await thread.send(header)
                        await asyncio.sleep(0.3)
                    lines = block["code"].split("\n")
                    current = []
                    current_len = 0
                    for line in lines:
                        if current_len + len(line) + 20 > self.max_msg_length and current:
                            await thread.send("```" + block["language"] + "\n" + "\n".join(current) + "\n```")
                            await asyncio.sleep(0.3)
                            current = [line]
                            current_len = len(line)
                        else:
                            current.append(line)
                            current_len += len(line) + 1
                    if current:
                        await thread.send("```" + block["language"] + "\n" + "\n".join(current) + "\n```")
                else:
                    await thread.send(full)
                if i < len(code_blocks) - 1:
                    await asyncio.sleep(0.3)
            return thread
        except Exception as e:
            print("[CodeThread] Error: " + str(e))
            return None


class ReadMessagesTool:
    def __init__(self):
        self.default_count = 15
        self.max_count = 50
        self.max_chars = 4000

    async def read_messages(self, channel, count=None, before=None, user_id=None):
        count = min(count or self.default_count, self.max_count)
        try:
            messages = []
            kwargs = {"limit": count * 2 if user_id else count}
            if before:
                kwargs["before"] = before
            async for msg in channel.history(**kwargs):
                if user_id:
                    is_user_msg = (msg.author.id == user_id)
                    is_bot_reply = (msg.author.bot and msg.reference and hasattr(msg.reference, 'resolved') and msg.reference.resolved and hasattr(msg.reference.resolved, 'author') and msg.reference.resolved.author.id == user_id)
                    if not is_user_msg and not is_bot_reply:
                        continue
                data = {
                    "author": msg.author.display_name,
                    "content": msg.content or "",
                    "is_bot": msg.author.bot,
                    "timestamp": msg.created_at.strftime("%H:%M:%S"),
                }
                if msg.embeds:
                    info = []
                    for embed in msg.embeds[:2]:
                        parts = []
                        if embed.title:
                            parts.append(embed.title)
                        if embed.description:
                            parts.append(embed.description[:150])
                        if parts:
                            info.append(" - ".join(parts))
                    if info:
                        data["embeds"] = info
                if msg.attachments:
                    data["files"] = [a.filename for a in msg.attachments]
                messages.append(data)
                if len(messages) >= (count or self.default_count):
                    break
            messages.reverse()
            return messages
        except Exception as e:
            print("[ReadMessages] Error: " + str(e))
            return []

    def format_context(self, messages):
        if not messages:
            return "[No recent messages]"
        lines = []
        total = 0
        for msg in messages:
            bot_tag = " (Bot)" if msg["is_bot"] else ""
            line = "[" + msg["timestamp"] + "] " + msg["author"] + bot_tag + ": " + msg["content"]
            if "embeds" in msg:
                line += " [Embed: " + "; ".join(msg["embeds"]) + "]"
            if "files" in msg:
                line += " [Files: " + ", ".join(msg["files"]) + "]"
            if total + len(line) > self.max_chars:
                lines.insert(0, "...(earlier messages truncated)...")
                break
            lines.append(line)
            total += len(line)
        return "\n".join(lines)

    async def get_context(self, channel, before=None, user_id=None):
        msgs = await self.read_messages(channel, before=before, user_id=user_id)
        return self.format_context(msgs)


# ============================================================
# COMMAND BAR TOOL
# ============================================================

class CommandBarTool:
    """
    Generates Roblox Studio Command Bar scripts.

    Produces TWO scripts:
    1. The main code (ModuleScript/Script/LocalScript to insert)
    2. An auto-setup command bar script that creates the proper
       hierarchy and inserts everything automatically.

    SAFETY: NEVER uses :Destroy() in any generated code.
    All removals use .Parent = nil or :Remove() with confirmation.
    """

    # Banned patterns that must NEVER appear in output
    BANNED_PATTERNS = [
        ":Destroy()",
        ":destroy()",
        ".Destroy(",
        "Destroy()",
        ":ClearAllChildren()",
        "game:ClearAllChildren",
    ]

    # Safe alternatives mapping
    SAFE_ALTERNATIVES = {
        ":Destroy()": ".Parent = nil  -- Safely removed (not destroyed)",
        ":destroy()": ".Parent = nil  -- Safely removed (not destroyed)",
        ":ClearAllChildren()": "-- Children moved to nil individually (safe removal)",
    }

    def __init__(self, genai_client=None, model_name=None):
        self.genai_client = genai_client
        self.model_name = model_name

    def sanitize_code(self, code: str) -> str:
        """Remove ALL dangerous patterns from generated code"""
        sanitized = code
        for banned in self.BANNED_PATTERNS:
            if banned.lower() in sanitized.lower():
                # Find and replace case-insensitively
                pattern = re.compile(re.escape(banned), re.IGNORECASE)
                replacement = self.SAFE_ALTERNATIVES.get(banned, ".Parent = nil  -- Safe removal")
                sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    def validate_code(self, code: str) -> dict:
        """Check code for dangerous patterns and return report"""
        issues = []
        for banned in self.BANNED_PATTERNS:
            if banned.lower() in code.lower():
                issues.append({
                    "pattern": banned,
                    "safe_alternative": self.SAFE_ALTERNATIVES.get(banned, ".Parent = nil"),
                    "severity": "CRITICAL"
                })

        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues)
        }

    def generate_setup_script(self, files: dict, project_name: str = "Project") -> str:
        """
        Generate a Command Bar auto-setup script that:
        - Creates all necessary folders/services structure
        - Inserts all scripts into correct locations
        - Sets up proper script types (Server/Local/Module)
        - NEVER uses :Destroy()
        """
        setup_lines = []
        setup_lines.append("-- ╔══════════════════════════════════════════════╗")
        setup_lines.append(f"-- ║  AUTO-SETUP: {project_name[:35]:<35} ║")
        setup_lines.append("-- ║  Paste this in Studio Command Bar            ║")
        setup_lines.append("-- ║  ⚠️  SAFE: No :Destroy() calls used          ║")
        setup_lines.append("-- ╚══════════════════════════════════════════════╝")
        setup_lines.append("")
        setup_lines.append("local function safeCreate(className, name, parent)")
        setup_lines.append("    local existing = parent:FindFirstChild(name)")
        setup_lines.append("    if existing then")
        setup_lines.append('        print("[Setup] Found existing: " .. name .. " — Updating source")')
        setup_lines.append("        return existing")
        setup_lines.append("    end")
        setup_lines.append("    local obj = Instance.new(className)")
        setup_lines.append("    obj.Name = name")
        setup_lines.append("    obj.Parent = parent")
        setup_lines.append('    print("[Setup] Created: " .. className .. " — " .. name)')
        setup_lines.append("    return obj")
        setup_lines.append("end")
        setup_lines.append("")
        setup_lines.append("local function ensureFolder(name, parent)")
        setup_lines.append("    local folder = parent:FindFirstChild(name)")
        setup_lines.append("    if folder then return folder end")
        setup_lines.append('    folder = Instance.new("Folder")')
        setup_lines.append("    folder.Name = name")
        setup_lines.append("    folder.Parent = parent")
        setup_lines.append('    print("[Setup] Created folder: " .. name)')
        setup_lines.append("    return folder")
        setup_lines.append("end")
        setup_lines.append("")
        setup_lines.append('print("\\n══════════════════════════════════════")')
        setup_lines.append(f'print("  Setting up: {project_name}")')
        setup_lines.append('print("══════════════════════════════════════\\n")')
        setup_lines.append("")

        for filename, code in files.items():
            sanitized_code = self.sanitize_code(code)

            # Determine script type and location from filename
            script_type, parent_path = self._detect_script_info(filename)
            safe_name = filename.replace(".lua", "").replace(".luau", "")
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', safe_name)

            # Escape the code for embedding in a string
            escaped_code = sanitized_code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

            setup_lines.append(f"-- ── {filename} ──")
            setup_lines.append(f"do")

            # Create parent folders if needed
            if "/" in filename or "\\" in filename:
                parts = filename.replace("\\", "/").split("/")
                if len(parts) > 1:
                    folder_parts = parts[:-1]
                    current_var = "game:GetService(\"ServerScriptService\")"
                    for i, folder in enumerate(folder_parts):
                        var_name = f"folder_{safe_name}_{i}"
                        setup_lines.append(f'    local {var_name} = ensureFolder("{folder}", {current_var})')
                        current_var = var_name
                    setup_lines.append(f'    local script_{safe_name} = safeCreate("{script_type}", "{parts[-1].replace(".lua", "").replace(".luau", "")}", {current_var})')
                else:
                    setup_lines.append(f'    local parent_{safe_name} = {parent_path}')
                    setup_lines.append(f'    local script_{safe_name} = safeCreate("{script_type}", "{safe_name}", parent_{safe_name})')
            else:
                setup_lines.append(f'    local parent_{safe_name} = {parent_path}')
                setup_lines.append(f'    local script_{safe_name} = safeCreate("{script_type}", "{safe_name}", parent_{safe_name})')

            setup_lines.append(f'    script_{safe_name}.Source = "{escaped_code}"')
            setup_lines.append(f'    print("[Setup] ✓ {filename} — inserted")')
            setup_lines.append(f"end")
            setup_lines.append("")

        setup_lines.append('print("\\n══════════════════════════════════════")')
        setup_lines.append(f'print("  ✅ {project_name} — Setup Complete!")')
        setup_lines.append(f'print("  📁 {len(files)} files inserted")')
        setup_lines.append('print("══════════════════════════════════════\\n")')
        setup_lines.append("")
        setup_lines.append("-- ⚠️ SAFETY NOTE: This script does NOT use :Destroy()")
        setup_lines.append("-- Existing scripts are updated in-place, not deleted.")

        return "\n".join(setup_lines)

    def _detect_script_info(self, filename: str) -> tuple:
        """Detect script type and parent service from filename patterns"""
        name_lower = filename.lower()

        # Client-side patterns
        if any(p in name_lower for p in ["client", "local", "gui", "ui", "hud", "menu", "button", "input"]):
            return "LocalScript", 'game:GetService("StarterPlayerScripts")'

        # Module patterns
        if any(p in name_lower for p in ["module", "lib", "util", "helper", "class", "config", "shared", "types"]):
            return "ModuleScript", 'game:GetService("ReplicatedStorage")'

        # Replicated patterns
        if any(p in name_lower for p in ["replicated", "shared", "common", "remote"]):
            return "ModuleScript", 'game:GetService("ReplicatedStorage")'

        # Server patterns (default)
        return "Script", 'game:GetService("ServerScriptService")'

    async def generate_command_scripts(self, description: str, existing_code: str = None) -> dict:
        """
        Generate both the main script AND the command bar setup script.
        Uses AI if available, otherwise returns a template.
        """
        if not self.genai_client or not self.model_name:
            return {
                "error": "AI client not configured for command bar generation.",
                "main_code": None,
                "setup_code": None
            }

        prompt = (
            "You are a Roblox Luau code generator for Studio Command Bar scripts.\n\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║  ⚠️  CRITICAL SAFETY RULES — MUST FOLLOW               ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            "║  1. NEVER use :Destroy() — EVER. Not once.             ║\n"
            "║  2. NEVER use :ClearAllChildren()                       ║\n"
            "║  3. NEVER use game:ClearAllChildren()                   ║\n"
            "║  4. To remove something: use .Parent = nil              ║\n"
            "║  5. To replace: update in-place, don't delete           ║\n"
            "║  6. Always use FindFirstChild before accessing          ║\n"
            "║  7. Wrap risky operations in pcall()                    ║\n"
            "╚══════════════════════════════════════════════════════════╝\n\n"
        )

        if existing_code:
            prompt += f"EXISTING CODE TO CREATE SETUP FOR:\n```lua\n{existing_code[:3000]}\n```\n\n"
            prompt += (
                "Generate a Command Bar script that sets up this code in Studio.\n"
                "The script should:\n"
                "1. Create the proper Instance type (Script/LocalScript/ModuleScript)\n"
                "2. Place it in the correct service\n"
                "3. Set the Source property to the code\n"
                "4. Print progress messages\n"
                "5. NEVER use :Destroy()\n\n"
            )
        else:
            prompt += (
                f"USER REQUEST: {description}\n\n"
                "Generate TWO things:\n"
                "1. MAIN CODE — The actual Luau script that does what the user wants\n"
                "2. SETUP CODE — A Command Bar script that auto-inserts the main code into Studio\n\n"
                "Format your response EXACTLY like this:\n"
                "===MAIN_CODE===\n"
                "FILENAME: YourScript.lua\n"
                "SCRIPT_TYPE: Script/LocalScript/ModuleScript\n"
                "LOCATION: ServerScriptService/ReplicatedStorage/StarterPlayerScripts\n"
                "```lua\n-- your main code here\n```\n\n"
                "===SETUP_CODE===\n"
                "```lua\n-- command bar setup script here\n```\n\n"
            )

        prompt += (
            "SETUP SCRIPT REQUIREMENTS:\n"
            "- Must work when pasted into Studio Command Bar\n"
            "- Must create proper folders/hierarchy\n"
            "- Must check if instances already exist (update, don't duplicate)\n"
            "- Must print clear progress messages\n"
            "- Must have a completion summary at the end\n"
            "- ABSOLUTELY NO :Destroy() calls — use .Parent = nil if removing\n"
            "- Add safety header comment block\n"
        )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=90
            )
            result_text = response.text or ""

            # Parse the response
            main_code = ""
            setup_code = ""
            main_filename = "GeneratedScript.lua"
            script_type = "Script"
            location = "ServerScriptService"

            if "===MAIN_CODE===" in result_text and "===SETUP_CODE===" in result_text:
                parts = result_text.split("===SETUP_CODE===")
                main_part = parts[0].replace("===MAIN_CODE===", "").strip()
                setup_part = parts[1].strip() if len(parts) > 1 else ""

                # Extract filename
                for line in main_part.split("\n")[:5]:
                    if line.strip().upper().startswith("FILENAME:"):
                        main_filename = line.split(":", 1)[1].strip().replace("`", "")
                    elif line.strip().upper().startswith("SCRIPT_TYPE:"):
                        script_type = line.split(":", 1)[1].strip()
                    elif line.strip().upper().startswith("LOCATION:"):
                        location = line.split(":", 1)[1].strip()

                # Extract code blocks
                code_pattern = r"```\w*\n([\s\S]*?)```"
                main_match = re.search(code_pattern, main_part)
                if main_match:
                    main_code = main_match.group(1).strip()

                setup_match = re.search(code_pattern, setup_part)
                if setup_match:
                    setup_code = setup_match.group(1).strip()
            else:
                # Single code block — treat as main code, generate setup ourselves
                code_pattern = r"```\w*\n([\s\S]*?)```"
                match = re.search(code_pattern, result_text)
                if match:
                    main_code = match.group(1).strip()

            # SANITIZE — Remove any :Destroy() that slipped through
            main_code = self.sanitize_code(main_code)
            setup_code = self.sanitize_code(setup_code)

            # If no setup code was generated, create one ourselves
            if not setup_code and main_code:
                files = {main_filename: main_code}
                setup_code = self.generate_setup_script(files, project_name=main_filename.replace(".lua", ""))

            # Validate both
            main_validation = self.validate_code(main_code) if main_code else {"safe": True, "issues": []}
            setup_validation = self.validate_code(setup_code) if setup_code else {"safe": True, "issues": []}

            return {
                "main_code": main_code,
                "setup_code": setup_code,
                "filename": main_filename,
                "script_type": script_type,
                "location": location,
                "main_safe": main_validation["safe"],
                "setup_safe": setup_validation["safe"],
                "safety_issues": main_validation["issues"] + setup_validation["issues"],
                "error": None
            }

        except asyncio.TimeoutError:
            return {"error": "AI request timed out.", "main_code": None, "setup_code": None}
        except Exception as e:
            print(f"[CommandBarTool] Error: {e}")
            return {"error": str(e), "main_code": None, "setup_code": None}


# ============================================================
# CODE CONVERTER TOOL
# ============================================================

class CodeConverterTool:
    """
    Converts code between languages and patterns.

    Supported conversions:
    - Language: Python ↔ Lua, JavaScript ↔ Lua, TypeScript ↔ Lua, etc.
    - Pattern: OOP ↔ Module, Callback ↔ Promise, Procedural ↔ OOP
    - Framework: Standard Lua ↔ Roblox Luau specific
    """

    SUPPORTED_LANGUAGES = {
        "lua": {"name": "Lua/Luau", "ext": ".lua", "aliases": ["luau", "roblox"]},
        "python": {"name": "Python", "ext": ".py", "aliases": ["py"]},
        "javascript": {"name": "JavaScript", "ext": ".js", "aliases": ["js", "node"]},
        "typescript": {"name": "TypeScript", "ext": ".ts", "aliases": ["ts"]},
        "csharp": {"name": "C#", "ext": ".cs", "aliases": ["cs", "c#", "unity"]},
        "java": {"name": "Java", "ext": ".java", "aliases": []},
        "cpp": {"name": "C++", "ext": ".cpp", "aliases": ["c++"]},
        "gdscript": {"name": "GDScript", "ext": ".gd", "aliases": ["godot"]},
    }

    SUPPORTED_PATTERNS = {
        "oop": {"name": "Object-Oriented (OOP)", "description": "Class-based with metatables"},
        "module": {"name": "Module Pattern", "description": "ModuleScript with exported functions"},
        "procedural": {"name": "Procedural", "description": "Linear top-to-bottom scripts"},
        "functional": {"name": "Functional", "description": "Pure functions, no state mutation"},
        "callback": {"name": "Callback Pattern", "description": "Event-driven with callbacks"},
        "promise": {"name": "Promise/Async", "description": "Promise-based async flow"},
        "ecs": {"name": "Entity Component System", "description": "Data-driven ECS architecture"},
        "singleton": {"name": "Singleton", "description": "Single instance module pattern"},
        "observer": {"name": "Observer Pattern", "description": "Event/signal based communication"},
        "state_machine": {"name": "State Machine", "description": "FSM with states and transitions"},
    }

    def __init__(self, genai_client=None, model_name=None):
        self.genai_client = genai_client
        self.model_name = model_name

    def resolve_language(self, input_str: str) -> str:
        """Resolve a language name/alias to its canonical key"""
        input_lower = input_str.strip().lower()
        for key, info in self.SUPPORTED_LANGUAGES.items():
            if input_lower == key or input_lower in info["aliases"] or input_lower == info["name"].lower():
                return key
        return None

    def resolve_pattern(self, input_str: str) -> str:
        """Resolve a pattern name to its canonical key"""
        input_lower = input_str.strip().lower().replace(" ", "_").replace("-", "_")
        for key, info in self.SUPPORTED_PATTERNS.items():
            if input_lower == key or input_lower in info["name"].lower():
                return key
        # Fuzzy match
        for key in self.SUPPORTED_PATTERNS:
            if key in input_lower or input_lower in key:
                return key
        return None

    def detect_language(self, code: str) -> str:
        """Auto-detect the language of a code snippet"""
        indicators = {
            "lua": [
                r"\blocal\s+\w+\s*=", r"\bfunction\b.*\bend\b", r"\bthen\b",
                r"\bgame\b", r"\bInstance\.new\b", r"\bwait\b", r"\bspawn\b",
                r"\brepeat\b.*\buntil\b", r"--\[\[", r"\belseif\b"
            ],
            "python": [
                r"\bdef\s+\w+", r"\bimport\s+", r"\bclass\s+\w+.*:",
                r"\bself\.", r"\bprint\s*\(", r":\s*$", r"\bNone\b",
                r"\belif\b", r"#\s*\w+"
            ],
            "javascript": [
                r"\bconst\s+", r"\blet\s+", r"\bvar\s+", r"\bfunction\s*\(",
                r"=>", r"\bconsole\.log\b", r"\bdocument\.", r"\bwindow\.",
                r"\bnull\b", r"\bundefined\b"
            ],
            "typescript": [
                r":\s*(string|number|boolean|void|any)\b", r"\binterface\s+",
                r"\btype\s+\w+\s*=", r"<\w+>", r"\bas\s+\w+",
                r"\benum\s+"
            ],
            "csharp": [
                r"\busing\s+System", r"\bnamespace\s+", r"\bpublic\s+class\b",
                r"\bprivate\s+", r"\bvoid\s+", r"\bstring\s+",
                r"\bMonoBehaviour\b", r"\bGameObject\b"
            ],
            "gdscript": [
                r"\bextends\s+", r"\bfunc\s+", r"\bvar\s+\w+\s*:",
                r"\b@onready\b", r"\bpreload\b", r"\b\$\w+",
            ],
        }

        scores = {}
        for lang, patterns in indicators.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                score += len(matches)
            scores[lang] = score

        if not scores or max(scores.values()) == 0:
            return "lua"  # Default

        return max(scores, key=scores.get)

    def detect_pattern(self, code: str) -> str:
        """Auto-detect the coding pattern used"""
        indicators = {
            "oop": [r"\bsetmetatable\b", r"\b__index\b", r"\.new\s*=\s*function", r"\bself\b", r"\bclass\b"],
            "module": [r"\bmodule\b", r"\breturn\s+\w+\s*$", r"local\s+\w+\s*=\s*\{\}", r"\.Init\b"],
            "promise": [r"\bPromise\b", r"\.andThen\b", r"\.catch\b", r"\.await\b", r"\basync\b"],
            "callback": [r"\.Connect\b", r"\.Changed\b", r"\.Event\b", r"function\s*\(.*callback"],
            "ecs": [r"\bcomponent\b", r"\bentity\b", r"\bsystem\b", r"\bworld\b"],
            "singleton": [r"if\s+\w+\s+then\s+return\s+\w+", r"local\s+instance\b"],
            "state_machine": [r"\bstate\b", r"\btransition\b", r"\bcurrentState\b", r"\bChangeState\b"],
            "functional": [r"local\s+function\s+\w+\(.*\)\s*$", r"return\s+function"],
        }

        scores = {}
        for pattern_name, patterns in indicators.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE | re.IGNORECASE)
                score += len(matches)
            scores[pattern_name] = score

        if not scores or max(scores.values()) == 0:
            return "procedural"

        return max(scores, key=scores.get)

    def get_supported_list(self) -> str:
        """Get formatted list of supported languages and patterns"""
        lines = ["**Languages:**"]
        for key, info in self.SUPPORTED_LANGUAGES.items():
            aliases = ", ".join(info["aliases"]) if info["aliases"] else "none"
            lines.append(f"  `{key}` — {info['name']} (aliases: {aliases})")

        lines.append("\n**Patterns:**")
        for key, info in self.SUPPORTED_PATTERNS.items():
            lines.append(f"  `{key}` — {info['name']}: {info['description']}")

        return "\n".join(lines)

    async def convert_language(self, code: str, from_lang: str, to_lang: str) -> dict:
        """Convert code from one language to another"""
        if not self.genai_client or not self.model_name:
            return {"error": "AI client not configured.", "converted": None}

        from_info = self.SUPPORTED_LANGUAGES.get(from_lang, {"name": from_lang})
        to_info = self.SUPPORTED_LANGUAGES.get(to_lang, {"name": to_lang})

        prompt = (
            f"Convert this {from_info['name']} code to {to_info['name']}.\n\n"
            f"SOURCE CODE ({from_info['name']}):\n"
            f"```{from_lang}\n{code[:4000]}\n```\n\n"
            f"CONVERSION RULES:\n"
            f"1. Maintain the same logic and functionality\n"
            f"2. Use idiomatic {to_info['name']} patterns and conventions\n"
            f"3. Preserve comments (translate if needed)\n"
            f"4. Use proper naming conventions for {to_info['name']}\n"
            f"5. Add type annotations if {to_info['name']} supports them\n"
            f"6. Handle language-specific differences (e.g., 0-indexed vs 1-indexed)\n"
            f"7. Add a header comment noting the conversion\n"
        )

        if to_lang == "lua":
            prompt += (
                f"\nLUA/LUAU SPECIFIC:\n"
                f"- Use 'local' for all variables\n"
                f"- Arrays are 1-indexed\n"
                f"- Use string concatenation with ..\n"
                f"- No ternary operator (use 'and/or' pattern or if/else)\n"
                f"- NEVER use :Destroy()\n"
            )

        prompt += (
            f"\nRESPOND WITH:\n"
            f"CHANGES: List the key differences/adaptations made\n"
            f"WARNINGS: Any functionality that doesn't translate perfectly\n"
            f"Then the complete converted code in a code block.\n"
        )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=90
            )
            result = response.text or ""

            # Extract code
            code_pattern = r"```\w*\n([\s\S]*?)```"
            match = re.search(code_pattern, result)
            converted_code = match.group(1).strip() if match else ""

            # Extract changes and warnings
            changes = []
            warnings = []
            for line in result.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("- ") or line_stripped.startswith("• "):
                    if "WARN" in result[:result.find(line_stripped)].upper().split("\n")[-1] if "\n" in result[:result.find(line_stripped)] else "":
                        warnings.append(line_stripped[2:])
                    else:
                        changes.append(line_stripped[2:])

            # Extract sections more reliably
            changes_section = ""
            warnings_section = ""
            if "CHANGES:" in result.upper():
                idx = result.upper().find("CHANGES:")
                end_idx = result.upper().find("WARNINGS:", idx)
                if end_idx == -1:
                    end_idx = result.find("```", idx)
                if end_idx > idx:
                    changes_section = result[idx + 8:end_idx].strip()

            if "WARNINGS:" in result.upper():
                idx = result.upper().find("WARNINGS:")
                end_idx = result.find("```", idx)
                if end_idx > idx:
                    warnings_section = result[idx + 9:end_idx].strip()

            return {
                "converted": converted_code,
                "from_lang": from_info["name"],
                "to_lang": to_info["name"],
                "changes": changes_section or "\n".join(changes) if changes else "Standard conversion applied",
                "warnings": warnings_section or "\n".join(warnings) if warnings else "None",
                "original_lines": len(code.strip().split("\n")),
                "converted_lines": len(converted_code.split("\n")) if converted_code else 0,
                "error": None
            }

        except asyncio.TimeoutError:
            return {"error": "Conversion timed out.", "converted": None}
        except Exception as e:
            print(f"[CodeConverter] Language convert error: {e}")
            return {"error": str(e), "converted": None}

    async def convert_pattern(self, code: str, from_pattern: str, to_pattern: str, language: str = "lua") -> dict:
        """Convert code from one design pattern to another"""
        if not self.genai_client or not self.model_name:
            return {"error": "AI client not configured.", "converted": None}

        from_info = self.SUPPORTED_PATTERNS.get(from_pattern, {"name": from_pattern, "description": ""})
        to_info = self.SUPPORTED_PATTERNS.get(to_pattern, {"name": to_pattern, "description": ""})
        lang_info = self.SUPPORTED_LANGUAGES.get(language, {"name": language})

        prompt = (
            f"Convert this {lang_info['name']} code from {from_info['name']} pattern "
            f"to {to_info['name']} pattern.\n\n"
            f"FROM PATTERN: {from_info['name']} — {from_info.get('description', '')}\n"
            f"TO PATTERN: {to_info['name']} — {to_info.get('description', '')}\n\n"
            f"SOURCE CODE:\n```{language}\n{code[:4000]}\n```\n\n"
            f"CONVERSION RULES:\n"
            f"1. Maintain ALL original functionality\n"
            f"2. Apply the {to_info['name']} pattern properly\n"
            f"3. Restructure the code architecture, not just rename things\n"
            f"4. Add comments explaining the pattern structure\n"
            f"5. Use proper {lang_info['name']} conventions\n"
            f"6. NEVER use :Destroy() in Lua code\n\n"
        )

        # Pattern-specific instructions
        pattern_instructions = {
            "oop": "Use metatables with __index. Create .new() constructor. Use self: method syntax.",
            "module": "Create a module table. Export public functions. Keep internals local. Return the module.",
            "promise": "Use Promise library. Chain with :andThen(). Handle errors with :catch().",
            "callback": "Use event-driven callbacks. Connect to signals. Pass functions as parameters.",
            "ecs": "Separate entities (IDs), components (data), and systems (logic). Use composition over inheritance.",
            "singleton": "Ensure only one instance exists. Use a module-level variable. Return existing on subsequent requires.",
            "state_machine": "Define states as a table. Create transition functions. Track currentState. Use enter/exit/update per state.",
            "functional": "Use pure functions. Avoid mutation. Pass data through function chains. No side effects where possible.",
            "observer": "Create Signal/Event objects. Allow subscribe/unsubscribe. Fire events to notify observers.",
            "procedural": "Write linear top-to-bottom code. Use functions for reuse. Minimize abstraction.",
        }

        if to_pattern in pattern_instructions:
            prompt += f"PATTERN GUIDANCE:\n{pattern_instructions[to_pattern]}\n\n"

        prompt += (
            f"RESPOND WITH:\n"
            f"STRUCTURE: Brief explanation of the new architecture\n"
            f"CHANGES: What was restructured and why\n"
            f"Then the complete converted code in a code block.\n"
        )

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=90
            )
            result = response.text or ""

            # Extract code
            code_pattern_regex = r"```\w*\n([\s\S]*?)```"
            match = re.search(code_pattern_regex, result)
            converted_code = match.group(1).strip() if match else ""

            # Extract structure explanation
            structure = ""
            if "STRUCTURE:" in result.upper():
                idx = result.upper().find("STRUCTURE:")
                end_idx = result.upper().find("CHANGES:", idx)
                if end_idx == -1:
                    end_idx = result.find("```", idx)
                if end_idx > idx:
                    structure = result[idx + 10:end_idx].strip()

            changes = ""
            if "CHANGES:" in result.upper():
                idx = result.upper().find("CHANGES:")
                end_idx = result.find("```", idx)
                if end_idx > idx:
                    changes = result[idx + 8:end_idx].strip()

            return {
                "converted": converted_code,
                "from_pattern": from_info["name"],
                "to_pattern": to_info["name"],
                "language": lang_info["name"],
                "structure": structure or "Pattern conversion applied",
                "changes": changes or "Standard restructuring",
                "original_lines": len(code.strip().split("\n")),
                "converted_lines": len(converted_code.split("\n")) if converted_code else 0,
                "error": None
            }

        except asyncio.TimeoutError:
            return {"error": "Pattern conversion timed out.", "converted": None}
        except Exception as e:
            print(f"[CodeConverter] Pattern convert error: {e}")
            return {"error": str(e), "converted": None}

    async def auto_convert(self, code: str, target: str) -> dict:
        """
        Smart converter — auto-detects source language/pattern
        and converts to the specified target.
        Target can be a language or a pattern name.
        """
        # Try to resolve as language first
        target_lang = self.resolve_language(target)
        if target_lang:
            from_lang = self.detect_language(code)
            if from_lang == target_lang:
                return {
                    "error": f"Code is already in {self.SUPPORTED_LANGUAGES[target_lang]['name']}.",
                    "converted": None
                }
            return await self.convert_language(code, from_lang, target_lang)

        # Try to resolve as pattern
        target_pattern = self.resolve_pattern(target)
        if target_pattern:
            language = self.detect_language(code)
            from_pattern = self.detect_pattern(code)
            if from_pattern == target_pattern:
                return {
                    "error": f"Code already uses {self.SUPPORTED_PATTERNS[target_pattern]['name']} pattern.",
                    "converted": None
                }
            return await self.convert_pattern(code, from_pattern, target_pattern, language)

        return {
            "error": f"Unknown target '{target}'. Use a language name (lua, python, js) or pattern name (oop, module, promise).",
            "converted": None,
            "supported": self.get_supported_list()
        }


class AIResponseHandler:
    def __init__(self):
        self.splitter = SplitMessageTool()
        self.code_thread = CodeThreadTool()
        self.reader = ReadMessagesTool()

    async def get_context(self, channel, before=None, user_id=None):
        return await self.reader.get_context(channel, before=before, user_id=user_id)

    async def send_response(self, message, ai_text, user_name):
        sent = []
        if self.code_thread.has_significant_code(ai_text):
            text_part, code_blocks = self.code_thread.extract_code_and_text(ai_text)
            if text_part.strip():
                sent = await self.splitter.send_split(message, text_part, reply=True)
            else:
                msg = await message.reply("Here's the code you requested")
                sent.append(msg)
            if sent:
                thread = await self.code_thread.create_code_thread(sent[0], code_blocks, user_name)
                if thread:
                    print("[AI] Created code thread: " + thread.name)
        else:
            sent = await self.splitter.send_split(message, ai_text, reply=True)
        return sent


ai_handler = AIResponseHandler()