import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile, db
from config import (
    BOT_COLOR, CREDIT_TO_PCREDIT_RATE, PCREDIT_TO_AICREDIT_RATE,
    PCREDIT_SHOP, AI_NAME, AI_CHAT_COOLDOWN_HOURS, AI_CHAT_DURATION_MINUTES,
    AI_MODEL, AI_PERSONALITY
)
from datetime import datetime, timedelta
import asyncio
import os
import re
import json
from anthropic import Anthropic

from ai_tools import ai_handler, CommandBarTool, CodeConverterTool
from agent_core import AgentMode

# Anthropic Integration Setup
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

anthropic_client = Anthropic(
    api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
    base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
)


# ============================================================
# AGENT SWITCH VIEWS
# ============================================================

class AgentSwitchView(discord.ui.View):
    """Prompt user to switch to agent mode when request is complex"""

    def __init__(self, cog, user_id: int, original_message, difficulty: str, reason: str):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
        self.original_message = original_message
        self.difficulty = difficulty
        self.reason = reason
        self.responded = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the original user can respond.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if not self.responded:
            try:
                embed = discord.Embed(
                    title="⏰ Switch Prompt Expired",
                    description="No response received. Staying in normal chat mode.",
                    color=discord.Color.greyple()
                )
                for item in self.children:
                    item.disabled = True
                await self.original_message.edit(view=self)
            except Exception:
                pass

    @discord.ui.button(label="Accept — Switch to Agent", emoji="🤖", style=discord.ButtonStyle.success)
    async def accept_agent(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        user = await UserProfile.get_user(self.user_id)
        is_admin = False
        if interaction.guild and hasattr(interaction.user, 'guild_permissions'):
            is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            if current_ai < 3:
                await interaction.followup.send(
                    f"❌ Agent mode requires **3 AI Credits** per message. You have **{current_ai}**.\n"
                    f"Use `/convert_ai` to get more.",
                    ephemeral=True
                )
                return

        user_rank = user.get("rank", "Beginner") if user else "Beginner"
        self.cog.agent.activate(self.user_id, super_mode=False)
        self.cog.agent.sessions[self.user_id]["user_rank"] = user_rank

        activate_embed = discord.Embed(
            title="🤖 Agent Mode — Auto-Activated",
            description=(
                f"Switched because: **{self.reason}**\n\n"
                "**Pipeline:** Analyze → Plan → Execute → Present\n"
                "**Cost:** 3 AI Credits per message\n\n"
                "Your original request is being processed..."
            ),
            color=0x5865F2
        )
        await interaction.followup.send(embed=activate_embed)

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            await UserProfile.update_user(self.user_id, {
                "ai_credits": current_ai - 3
            })

        try:
            async with self.original_message.channel.typing():
                await self.cog.agent.handle_message(self.original_message)
        except Exception as e:
            if not is_admin:
                user = await UserProfile.get_user(self.user_id)
                await UserProfile.update_user(self.user_id, {
                    "ai_credits": user.get('ai_credits', 0) + 3
                })
            await self.original_message.reply(f"❌ Agent error. Credits refunded.")
            print(f"[Agent Switch Error] {e}")

    @discord.ui.button(label="Accept — Super Agent", emoji="⚡", style=discord.ButtonStyle.primary)
    async def accept_super(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        user = await UserProfile.get_user(self.user_id)
        is_admin = False
        if interaction.guild and hasattr(interaction.user, 'guild_permissions'):
            is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            if current_ai < 5:
                await interaction.followup.send(
                    f"❌ Super Agent requires **5 AI Credits** per message. You have **{current_ai}**.\n"
                    f"Use `/convert_ai` to get more.",
                    ephemeral=True
                )
                return

        user_rank = user.get("rank", "Beginner") if user else "Beginner"
        self.cog.agent.activate(self.user_id, super_mode=True)
        self.cog.agent.sessions[self.user_id]["user_rank"] = user_rank

        activate_embed = discord.Embed(
            title="⚡ Super Agent — Auto-Activated",
            description=(
                f"Switched because: **{self.reason}**\n\n"
                "**Pipeline:** Build → Review → Optimize → Verify → Final Review\n"
                "**Cost:** 5 AI Credits per message\n\n"
                "Your original request is being processed..."
            ),
            color=0x5865F2
        )
        await interaction.followup.send(embed=activate_embed)

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            await UserProfile.update_user(self.user_id, {
                "ai_credits": current_ai - 5
            })

        try:
            async with self.original_message.channel.typing():
                await self.cog.agent.handle_message(self.original_message)
        except Exception as e:
            if not is_admin:
                user = await UserProfile.get_user(self.user_id)
                await UserProfile.update_user(self.user_id, {
                    "ai_credits": user.get('ai_credits', 0) + 5
                })
            await self.original_message.reply(f"❌ Super Agent error. Credits refunded.")
            print(f"[Super Agent Switch Error] {e}")

    @discord.ui.button(label="Decline — Stay Normal", emoji="💬", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        decline_embed = discord.Embed(
            title="💬 Staying in Normal Chat",
            description="I'll do my best with normal chat mode. The response may be simplified.",
            color=0x99AAB5
        )
        await interaction.followup.send(embed=decline_embed)

        try:
            async with self.original_message.channel.typing():
                response = await self.cog.get_ai_response(self.original_message, skip_complexity_check=True)
                await ai_handler.send_response(
                    message=self.original_message,
                    ai_text=response,
                    user_name=self.original_message.author.display_name
                )
        except Exception as e:
            await self.original_message.reply(f"❌ AI Error: {str(e)[:200]}")

    @discord.ui.button(label="Auto-Accept (Always Switch)", emoji="🔄", style=discord.ButtonStyle.danger)
    async def auto_accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.responded = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        await UserProfile.update_user(self.user_id, {
            "auto_agent_switch": True
        })

        auto_embed = discord.Embed(
            title="🔄 Auto-Switch Enabled",
            description=(
                "From now on, complex requests will **automatically** switch to Agent mode.\n"
                "To disable: type `auto switch off` in any AI channel."
            ),
            color=0xE67E22
        )
        await interaction.followup.send(embed=auto_embed)

        user = await UserProfile.get_user(self.user_id)
        is_admin = False
        if interaction.guild and hasattr(interaction.user, 'guild_permissions'):
            is_admin = interaction.user.guild_permissions.administrator

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            if current_ai < 3:
                await interaction.followup.send(
                    f"❌ Not enough credits for agent mode. You have **{current_ai}**.",
                    ephemeral=True
                )
                return

        user_rank = user.get("rank", "Beginner") if user else "Beginner"
        self.cog.agent.activate(self.user_id, super_mode=False)
        self.cog.agent.sessions[self.user_id]["user_rank"] = user_rank

        if not is_admin:
            current_ai = user.get('ai_credits', 0) if user else 0
            await UserProfile.update_user(self.user_id, {
                "ai_credits": current_ai - 3
            })

        try:
            async with self.original_message.channel.typing():
                await self.cog.agent.handle_message(self.original_message)
        except Exception as e:
            if not is_admin:
                user = await UserProfile.get_user(self.user_id)
                await UserProfile.update_user(self.user_id, {
                    "ai_credits": user.get('ai_credits', 0) + 3
                })
            await self.original_message.reply(f"❌ Agent error. Credits refunded.")


class PremiumShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Select an item to buy",
        options=[
            discord.SelectOption(
                label=item['name'],
                value=key,
                description=f"{item['price']} pCredits - {item['description']}"
            )
            for key, item in PCREDIT_SHOP.items()
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return

        item_key = select.values[0]
        item = PCREDIT_SHOP[item_key]

        user = await UserProfile.get_user(self.user_id)
        if not user:
            await interaction.response.send_message("Profile not found. Use `/start` first.", ephemeral=True)
            return

        current_pcredits = user.get('pcredits', 0)
        if current_pcredits < item['price']:
            await interaction.response.send_message(
                f"Not enough pCredits. You need **{item['price']}** but have **{current_pcredits}**.",
                ephemeral=True
            )
            return

        updates = {"pcredits": current_pcredits - item['price']}
        if item_key == "team_slot":
            updates["max_teams"] = user.get("max_teams", 1) + 1
        elif item_key == "project_slots":
            updates["max_projects"] = user.get("max_projects", 2) + 5

        await UserProfile.update_user(self.user_id, updates)
        await interaction.response.send_message(
            f"✅ Purchased **{item['name']}** for **{item['price']}** pCredits!",
            ephemeral=True
        )


class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None
        self.session = None
        self.agent = AgentMode(anthropic_client, AI_MODEL, AI_PERSONALITY)
        self.command_tool = CommandBarTool(anthropic_client, AI_MODEL)
        self.converter_tool = CodeConverterTool(anthropic_client, AI_MODEL)

    # ============================================================
    # COMPLEXITY CHECKER
    # ============================================================

    async def _check_complexity(self, message_content: str) -> dict:
        """Ask AI to evaluate if a request is too complex for normal chat"""
        check_prompt = (
            "You are a complexity analyzer. Evaluate this user message and determine if it requires "
            "agent mode (multi-file code generation, complex systems, full projects) or can be handled "
            "in normal chat (simple questions, short code snippets, explanations).\n\n"
            f"USER MESSAGE: {message_content}\n\n"
            "Respond in EXACT JSON format (no markdown, raw JSON only):\n"
            '{"needs_agent": true/false, "difficulty": "simple/moderate/complex/advanced", '
            '"reason": "brief explanation", "recommended_mode": "normal/agent/super_agent", '
            '"detected_tools": ["template", "review", "project", "command", "convert"]}\n\n'
            "RULES:\n"
            "- needs_agent = true if: multi-file project, game system, complex script, full feature\n"
            "- needs_agent = false if: question, explanation, simple snippet, debugging help, short code\n"
            "- needs_agent = false if: code review, single conversion, template search, command bar script\n"
            "  (these are handled by normal chat tools)\n"
            "- detected_tools: list which tools would help:\n"
            "  template = code templates/boilerplate\n"
            "  review = code review/bug check\n"
            "  project = saved project lookup\n"
            "  command = command bar / studio setup script\n"
            "  convert = language or pattern conversion\n"
            "- ONLY output JSON"
        )

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: anthropic_client.messages.create(
                    model=AI_MODEL,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": check_prompt}]
                )
            )
            text = response.content[0].text if response.content else ""

            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
        except Exception as e:
            print(f"[Complexity Check Error] {e}")

        return {"needs_agent": False, "difficulty": "simple", "reason": "", "recommended_mode": "normal", "detected_tools": []}

    # ============================================================
    # AGENT TOOL EXECUTION IN NORMAL MODE
    # ============================================================

    async def _execute_agent_tool(self, message, tool_name: str, tool_args: str = "") -> str:
        """Execute an agent tool from normal chat mode and return result text"""

        if tool_name == "template":
            results = self.agent.templates.search(tool_args or message.content)
            if results:
                template = results[0]
                tmpl_data = template["template"]
                return (
                    f"**Execute agent_template** — Found: `{template['key']}`\n\n"
                    f"**{tmpl_data['name']}**\n"
                    f"{tmpl_data.get('description', 'No description')}\n\n"
                    f"💡 *To use this template with full code generation, switch to agent mode and type:*\n"
                    f"`use template {template['key']}`"
                )
            else:
                all_templates = self.agent.templates.get_all_names()
                if all_templates:
                    names = "\n".join([f"• `{t['key']}` — {t['name']}" for t in all_templates[:10]])
                    return (
                        f"**Execute agent_template** — No exact match found.\n\n"
                        f"**Available Templates:**\n{names}\n\n"
                        f"💡 *Switch to agent mode to use templates with full code generation.*"
                    )
                return "**Execute agent_template** — No templates available."

        elif tool_name == "review":
            code_content = tool_args or message.content
            pattern = r"```(\w*)\n([\s\S]*?)```"
            match = re.search(pattern, code_content)
            if match:
                language = match.group(1) or "lua"
                code = match.group(2).strip()
            else:
                code = code_content
                language = "lua"

            if len(code) < 10:
                return (
                    "**Execute agent_review** — Not enough code to review.\n"
                    "Paste your code in a code block and I'll analyze it."
                )

            review_data = await self.agent.code_reviewer.review_code(code, language)
            score = review_data.get("score", 0)
            grade = review_data.get("grade", "?")
            bugs = review_data.get("bugs", [])

            bug_text = ""
            if bugs:
                for b in bugs[:3]:
                    severity = b.get("severity", "medium").upper()
                    bug_text += f"  **[{severity}]** {b.get('issue', '?')}\n"
            else:
                bug_text = "  No bugs found!\n"

            return (
                f"**Execute agent_review** — Score: **{score}/100** ({grade})\n\n"
                f"**Issues Found:**\n{bug_text}\n"
                f"💡 *For a full review with fixes, switch to agent mode and type `review code`.*"
            )

        elif tool_name == "project":
            projects = self.agent.project_memory.get_projects(message.author.id)
            if projects:
                proj_list = ""
                for i, p in enumerate(projects[:5]):
                    task_count = len(p.get("tasks", []))
                    proj_list += f"  `{i + 1}` {p.get('original_request', '?')[:60]} — {task_count} tasks\n"
                return (
                    f"**Execute agent_project** — Found {len(projects)} saved project(s)\n\n"
                    f"**Your Projects:**\n{proj_list}\n"
                    f"💡 *Switch to agent mode and type `load project last` to continue working.*"
                )
            return (
                "**Execute agent_project** — No saved projects found.\n"
                "Complete an agent mode task to save a project."
            )

        elif tool_name == "command":
            # Check if user pasted code or is requesting new code
            code_pattern = r"```(\w*)\n([\s\S]*?)```"
            match = re.search(code_pattern, tool_args or message.content)

            if match:
                existing_code = match.group(2).strip()
                result = await self.command_tool.generate_command_scripts(
                    description="",
                    existing_code=existing_code
                )
            else:
                description = tool_args or message.content
                result = await self.command_tool.generate_command_scripts(description=description)

            if result.get("error"):
                return f"**Execute agent_command** — ❌ Error: {result['error']}"

            main_code = result.get("main_code", "")
            setup_code = result.get("setup_code", "")
            filename = result.get("filename", "Script.lua")
            safety_issues = result.get("safety_issues", [])

            output = f"**Execute agent_command** — Generated: `{filename}`\n\n"

            if safety_issues:
                output += f"⚠️ **Safety:** {len(safety_issues)} issue(s) were auto-fixed (no :Destroy() allowed)\n\n"

            output += f"**📄 Main Script** (`{filename}`):\n"
            if main_code:
                display_code = main_code[:1500] if len(main_code) > 1500 else main_code
                output += f"```lua\n{display_code}\n```\n"
                if len(main_code) > 1500:
                    output += f"*(truncated — {len(main_code)} chars total. Use agent mode for full output)*\n"

            output += f"\n**🔧 Command Bar Setup Script:**\n"
            if setup_code:
                display_setup = setup_code[:1500] if len(setup_code) > 1500 else setup_code
                output += f"```lua\n{display_setup}\n```\n"
                if len(setup_code) > 1500:
                    output += f"*(truncated — {len(setup_code)} chars total)*\n"

            output += (
                "\n─────────────────────\n"
                "**How to use:**\n"
                "1. Copy the **Setup Script** above\n"
                "2. Open Roblox Studio → View → Command Bar\n"
                "3. Paste and press Enter\n"
                "4. The script will auto-create everything in the right location\n\n"
                "⚠️ **Safety:** No `:Destroy()` calls are used — existing items are updated, not deleted.\n"
                "💡 *For complex multi-file projects with setup scripts, use agent mode.*"
            )
            return output

        elif tool_name == "convert":
            content = tool_args or message.content

            # Try to find code block and target
            code_pattern = r"```(\w*)\n([\s\S]*?)```"
            match = re.search(code_pattern, content)

            if match:
                code = match.group(2).strip()
                # Find target after the code block
                after_code = content[match.end():].strip().lower()

                # Look for "to <language/pattern>"
                to_match = re.search(r"(?:to|into|as)\s+(\w[\w\s]*)", after_code)
                if to_match:
                    target = to_match.group(1).strip()
                else:
                    # Look before the code block
                    before_code = content[:match.start()].strip().lower()
                    to_match = re.search(r"(?:to|into|as)\s+(\w[\w\s]*)", before_code)
                    if to_match:
                        target = to_match.group(1).strip()
                    else:
                        # Auto-detect and show info
                        detected_lang = self.converter_tool.detect_language(code)
                        detected_pattern = self.converter_tool.detect_pattern(code)
                        lang_name = self.converter_tool.SUPPORTED_LANGUAGES.get(detected_lang, {}).get("name", detected_lang)
                        pattern_name = self.converter_tool.SUPPORTED_PATTERNS.get(detected_pattern, {}).get("name", detected_pattern)

                        supported = self.converter_tool.get_supported_list()
                        return (
                            f"**Execute agent_convert** — Code detected as **{lang_name}** using **{pattern_name}** pattern\n\n"
                            f"Please specify what to convert to! Examples:\n"
                            f"• `convert this to python`\n"
                            f"• `convert this to oop`\n"
                            f"• `convert this to module pattern`\n\n"
                            f"{supported}"
                        )

                result = await self.converter_tool.auto_convert(code, target)
            else:
                # No code block — show usage help
                supported = self.converter_tool.get_supported_list()
                return (
                    f"**Execute agent_convert** — Code Converter\n\n"
                    f"Paste code in a code block and tell me what to convert it to.\n\n"
                    f"**Usage:**\n"
                    f"• `convert this to python` + code block\n"
                    f"• `convert to oop pattern` + code block\n"
                    f"• `convert to module` + code block\n\n"
                    f"{supported}"
                )

            if result.get("error"):
                error_msg = f"**Execute agent_convert** — ❌ {result['error']}"
                if result.get("supported"):
                    error_msg += f"\n\n{result['supported']}"
                return error_msg

            converted = result.get("converted", "")
            if not converted:
                return "**Execute agent_convert** — ❌ Conversion produced no output."

            # Determine which type of conversion happened
            if "from_lang" in result:
                output = (
                    f"**Execute agent_convert** — {result['from_lang']} → {result['to_lang']}\n\n"
                    f"📊 **Lines:** {result.get('original_lines', '?')} → {result.get('converted_lines', '?')}\n"
                )

                changes = result.get("changes", "")
                if changes and changes != "Standard conversion applied":
                    changes_display = changes[:500] if len(changes) > 500 else changes
                    output += f"\n**Changes:**\n{changes_display}\n"

                warnings = result.get("warnings", "")
                if warnings and warnings != "None":
                    warnings_display = warnings[:300] if len(warnings) > 300 else warnings
                    output += f"\n⚠️ **Warnings:**\n{warnings_display}\n"
            else:
                output = (
                    f"**Execute agent_convert** — {result.get('from_pattern', '?')} → {result.get('to_pattern', '?')} "
                    f"({result.get('language', 'Lua')})\n\n"
                    f"📊 **Lines:** {result.get('original_lines', '?')} → {result.get('converted_lines', '?')}\n"
                )

                structure = result.get("structure", "")
                if structure and structure != "Pattern conversion applied":
                    structure_display = structure[:500] if len(structure) > 500 else structure
                    output += f"\n**Architecture:**\n{structure_display}\n"

                changes = result.get("changes", "")
                if changes and changes != "Standard restructuring":
                    changes_display = changes[:500] if len(changes) > 500 else changes
                    output += f"\n**Changes:**\n{changes_display}\n"

            # Add converted code
            display_code = converted[:2000] if len(converted) > 2000 else converted

            # Detect target language for syntax highlighting
            target_lang_name = result.get("to_lang", result.get("language", "lua"))
            lang_key = "lua"
            if target_lang_name:
                for key, info in CodeConverterTool.SUPPORTED_LANGUAGES.items():
                    if target_lang_name.lower() == info["name"].lower() or target_lang_name.lower() == key:
                        lang_key = key
                        break

            output += f"\n**Converted Code:**\n```{lang_key}\n{display_code}\n```"

            if len(converted) > 2000:
                output += f"\n*(truncated — {len(converted)} chars total. Use agent mode for full output)*"

            output += "\n\n💡 *For multi-file conversions, use agent mode.*"
            return output

        return f"**Execute agent_{tool_name}** — Unknown tool."

    # ============================================================
    # AI RESPONSE (UPGRADED WITH 5 TOOLS)
    # ============================================================

    async def get_ai_response(self, message, skip_complexity_check=False):
        context = await ai_handler.get_context(message.channel, before=message, user_id=message.author.id)

        is_in_agent = self.agent.is_agent_mode(message.author.id)
        is_super = self.agent.is_super_agent(message.author.id) if is_in_agent else False

        mode_info = (
            "You are in NORMAL CHAT MODE. You are NOT in agent mode. "
            "Just respond naturally to the user's message like a normal chat assistant. "
            "Do NOT create task plans or do deep analysis. Just answer directly.\n\n"
            "IMPORTANT — YOU HAVE ACCESS TO THESE MODES AND TOOLS:\n"
            "═══════════════════════════════════════════\n"
            "MODES AVAILABLE:\n"
            "  • Normal Chat (current) — Simple Q&A, short code, explanations. Cost: 1 credit/msg\n"
            "  • Agent Mode — Multi-file projects, task planning, code generation. Cost: 3 credits/msg\n"
            "    Activate: user types 'change to agent mode'\n"
            "  • Super Agent — Full pipeline: build → review → optimize → verify. Cost: 5 credits/msg\n"
            "    Activate: user types 'change to super agent'\n\n"
            "AGENT TOOLS YOU CAN USE IN NORMAL CHAT (5 tools):\n"
            "  Include the EXACT tag in your response to invoke a tool:\n\n"
            "  • [TOOL:template:search_query] — Search code templates library\n"
            "      Use when: user asks about templates, starter code, boilerplate\n\n"
            "  • [TOOL:review:code_here] — Quick code review with scoring\n"
            "      Use when: user pastes code and asks for feedback, review, or bug check\n\n"
            "  • [TOOL:project:list] — Show user's saved projects\n"
            "      Use when: user asks about their projects, previous work, saved code\n\n"
            "  • [TOOL:command:description_or_code] — Generate Command Bar scripts\n"
            "      Use when: user wants a Studio setup script, command bar code,\n"
            "      or wants to auto-insert code into Roblox Studio\n"
            "      ⚠️ CRITICAL: NEVER include :Destroy() in command bar code!\n"
            "      Always use .Parent = nil for safe removal.\n"
            "      This generates TWO scripts: main code + auto-setup command\n\n"
            "  • [TOOL:convert:target_language_or_pattern] — Convert code\n"
            "      Use when: user wants to convert code to another language\n"
            "      (Python, JS, C#, etc.) or another pattern (OOP, Module, Promise, etc.)\n"
            "      Supported languages: lua, python, javascript, typescript, csharp, java, cpp, gdscript\n"
            "      Supported patterns: oop, module, procedural, functional, callback, promise,\n"
            "      ecs, singleton, observer, state_machine\n\n"
            "TOOL USAGE RULES:\n"
            "  1. You can use MULTIPLE tools in one response\n"
            "  2. Always answer the user's question FIRST, then add tool tags if helpful\n"
            "  3. For the command tool: NEVER generate code with :Destroy()\n"
            "  4. For convert tool: include the user's code block and the target in the tag\n"
            "  5. Don't use tools for simple questions — only when they add real value\n\n"
            "WHEN TO RECOMMEND AGENT MODE:\n"
            "  If the user asks for something complex (full systems, multi-file, game features),\n"
            "  suggest they switch: 'This would work better in agent mode! Type `change to agent mode`'\n"
            "  But still try to help with what you can in normal mode.\n"
            "═══════════════════════════════════════════"
        )

        system_prompt = f"You are {AI_NAME}. {AI_PERSONALITY}\n\nCURRENT MODE: {mode_info}"
        full_prompt = (
            f"System: {system_prompt}\n\n"
            f"=== RECENT CONVERSATION ===\n"
            f"{context}\n\n"
            f"=== CURRENT MESSAGE ===\n"
            f"{message.author.display_name}: {message.content}\n\n"
            f"Respond to the current message. You are in normal chat mode.\n"
            f"If the user's request would benefit from a tool, include the tool tag.\n"
            f"If the request is too complex for normal chat, mention agent mode.\n"
            f"Always answer the user's question directly first."
        )

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: anthropic_client.models.generate_content(
                    model=AI_MODEL,
                    contents=full_prompt
                )
            )
            ai_text = response.text or "No response generated."

            # Check for tool invocations in the AI response
            tool_pattern = r'\[TOOL:(\w+):([^\]]*)\]'
            tool_matches = re.findall(tool_pattern, ai_text)

            if tool_matches:
                clean_response = re.sub(tool_pattern, '', ai_text).strip()

                tool_results = []
                for tool_name_match, tool_args_match in tool_matches:
                    if tool_name_match in ("template", "review", "project", "command", "convert"):
                        result = await self._execute_agent_tool(message, tool_name_match, tool_args_match)
                        tool_results.append(result)

                if tool_results:
                    separator = "\n\n─────────────────────\n\n"
                    if clean_response:
                        ai_text = clean_response + separator + "\n\n".join(tool_results)
                    else:
                        ai_text = "\n\n".join(tool_results)
                else:
                    ai_text = clean_response

            return ai_text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"AI Error: {str(e)}"

    # ============================================================
    # SLASH COMMANDS
    # ============================================================

    @app_commands.command(name="convert", description="Convert Studio Credits to pCredits")
    @app_commands.describe(amount="Number of pCredits to buy (each costs configured rate in credits)")
    async def convert(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount <= 0:
            await interaction.followup.send("❌ Please enter a positive amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        total_cost = amount * CREDIT_TO_PCREDIT_RATE
        current_credits = user.get('studio_credits', 0)
        current_pcredits = user.get('pcredits', 0)

        if current_credits < total_cost:
            embed = discord.Embed(
                title="❌ Not Enough Credits",
                description=(
                    f"You need **{total_cost}** Studio Credits for **{amount}** pCredit(s).\n"
                    f"You currently have **{current_credits}** Studio Credits.\n"
                    f"You're short by **{total_cost - current_credits}** credits."
                ),
                color=discord.Color.red()
            )
            embed.add_field(
                name="Rate",
                value=f"1 pCredit = {CREDIT_TO_PCREDIT_RATE} Studio Credits",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        new_credits = current_credits - total_cost
        new_pcredits = current_pcredits + amount

        await UserProfile.update_user(interaction.user.id, {
            "studio_credits": new_credits,
            "pcredits": new_pcredits
        })

        embed = discord.Embed(
            title="✅ Conversion Successful!",
            description=f"Converted **{total_cost}** Studio Credits → **{amount}** pCredit(s)",
            color=discord.Color.green()
        )
        embed.add_field(name="Studio Credits", value=f"💰 {current_credits} → {new_credits}", inline=True)
        embed.add_field(name="pCredits", value=f"💎 {current_pcredits} → {new_pcredits}", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="convert_ai", description="Convert pCredits to AI Credits")
    @app_commands.describe(amount="Number of pCredits to convert (each gives configured rate in AI credits)")
    async def convert_ai(self, interaction: discord.Interaction, amount: int = 1):
        await interaction.response.defer(ephemeral=True)

        if amount <= 0:
            await interaction.followup.send("❌ Please enter a positive amount.", ephemeral=True)
            return

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        current_pcredits = user.get('pcredits', 0)
        current_ai = user.get('ai_credits', 0)
        ai_gained = amount * PCREDIT_TO_AICREDIT_RATE

        if current_pcredits < amount:
            embed = discord.Embed(
                title="❌ Not Enough pCredits",
                description=(
                    f"You need **{amount}** pCredit(s) but only have **{current_pcredits}**.\n"
                    f"You're short by **{amount - current_pcredits}** pCredits.\n\n"
                    f"Use `/convert` to get more pCredits from Studio Credits."
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        new_pcredits = current_pcredits - amount
        new_ai = current_ai + ai_gained

        await UserProfile.update_user(interaction.user.id, {
            "pcredits": new_pcredits,
            "ai_credits": new_ai
        })

        embed = discord.Embed(
            title="✅ Conversion Successful!",
            description=f"Converted **{amount}** pCredit(s) → **{ai_gained}** AI Credits",
            color=discord.Color.green()
        )
        embed.add_field(name="pCredits", value=f"💎 {current_pcredits} → {new_pcredits}", inline=True)
        embed.add_field(name="AI Credits", value=f"🤖 {current_ai} → {new_ai}", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="pshop", description="Open the pCredit Shop")
    async def pshop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        embed = discord.Embed(title="💎 Premium Shop", color=discord.Color.gold())
        embed.add_field(
            name="Your Balance",
            value=f"💎 **{user.get('pcredits', 0)}** pCredits",
            inline=False
        )

        for key, item in PCREDIT_SHOP.items():
            embed.add_field(
                name=f"{item['name']} — {item['price']} pCredits",
                value=item['description'],
                inline=True
            )

        await interaction.followup.send(
            embed=embed,
            view=PremiumShopView(interaction.user.id),
            ephemeral=True
        )

    @app_commands.command(name="setup_ai", description="[Admin] Set up the AI channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        self.ai_channel_id = channel.id
        await interaction.followup.send(f"✅ AI channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="temp_chat_ai", description="Create a temporary AI chat channel")
    async def temp_chat(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserProfile.get_user(interaction.user.id)
        if not user:
            await UserProfile.create_user(interaction.user.id, interaction.user.name)
            user = await UserProfile.get_user(interaction.user.id)

        last_used = user.get('temp_chat_cooldown')
        if last_used:
            try:
                cooldown_time = datetime.fromisoformat(last_used)
                time_since = (datetime.utcnow() - cooldown_time).total_seconds()
                cooldown_seconds = AI_CHAT_COOLDOWN_HOURS * 3600

                if time_since < cooldown_seconds:
                    remaining = cooldown_seconds - time_since
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)

                    embed = discord.Embed(
                        title="⏰ Cooldown Active",
                        description=f"You can use this again in **{hours}h {minutes}m**.",
                        color=discord.Color.orange()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
            except Exception:
                pass

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                create_public_threads=True,
                manage_threads=True
            )
        }

        channel = await guild.create_text_channel(
            name=f"ai-chat-{interaction.user.name}",
            overwrites=overwrites
        )
        await UserProfile.update_user(interaction.user.id, {
            "temp_chat_cooldown": datetime.utcnow().isoformat()
        })

        await interaction.followup.send(
            f"✅ Channel created: {channel.mention}. Expires in {AI_CHAT_DURATION_MINUTES} minutes.",
            ephemeral=True
        )

        welcome_embed = discord.Embed(
            title=f"🤖 {AI_NAME}",
            description=(
                f"Welcome, {interaction.user.mention}. This channel expires in "
                f"{AI_CHAT_DURATION_MINUTES} minutes.\n\n"
                f"**Modes**\n"
                f"💬 **Normal Chat** — Ask anything, get quick answers (1 credit/msg)\n"
                f"`change to agent mode` — Task planning + code generation (3 credits/msg)\n"
                f"`change to super agent` — Full pipeline with reviews + optimization (5 credits/msg)\n\n"
                f"**🛠️ Tools Available in Normal Chat**\n"
                f"I can automatically use these when relevant:\n"
                f"• 📋 **Templates** — Search code templates & boilerplate\n"
                f"• 🔍 **Review** — Quick code review with scoring\n"
                f"• 📁 **Projects** — View your saved projects\n"
                f"• 🔧 **Command** — Generate Studio Command Bar scripts + auto-setup\n"
                f"• 🔄 **Convert** — Convert code between languages & patterns\n\n"
                f"**Agent Commands** (in agent mode)\n"
                f"`creative mode on/off` · `present task on/off`\n"
                f"`templates` · `review code` · `my projects` · `load project last`\n"
                f"`exit agent mode` — Return to normal chat\n\n"
                f"**Settings**\n"
                f"`auto switch on/off` — Auto-switch to agent for complex requests"
            ),
            color=0x5865F2
        )
        welcome_embed.set_footer(
            text="Normal: 1 credit | Agent: 3 credits | Super: 5 credits | Admins: free"
        )
        await channel.send(embed=welcome_embed)

        await asyncio.sleep(AI_CHAT_DURATION_MINUTES * 60)
        try:
            await channel.delete(reason="Temporary AI chat expired")
        except Exception:
            pass

    # ============================================================
    # MESSAGE LISTENER
    # ============================================================

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_temp_chat = (
            hasattr(message.channel, 'name')
            and message.channel.name.startswith("ai-chat-")
        )

        if not is_temp_chat and (
            not self.ai_channel_id or message.channel.id != self.ai_channel_id
        ):
            return

        if message.content.startswith(("!", "/")):
            return

        if len(message.content.strip()) < 2:
            return

        user = await UserProfile.get_user(message.author.id)
        if not user:
            await UserProfile.create_user(message.author.id, message.author.name)
            user = await UserProfile.get_user(message.author.id)

        # Safe admin check
        is_admin = False
        if message.guild and hasattr(message.author, 'guild_permissions'):
            is_admin = message.author.guild_permissions.administrator

        content_lower = message.content.strip().lower()

        # ========== AUTO SWITCH TOGGLE ==========
        if content_lower == "auto switch off":
            await UserProfile.update_user(message.author.id, {
                "auto_agent_switch": False
            })
            await message.reply("🔄 Auto-switch to agent mode is now **disabled**.")
            return

        if content_lower == "auto switch on":
            await UserProfile.update_user(message.author.id, {
                "auto_agent_switch": True
            })
            await message.reply("🔄 Auto-switch to agent mode is now **enabled**.")
            return

        # ========== SUPER AGENT ACTIVATION ==========
        if content_lower == "change to super agent":
            if not is_admin:
                current_ai = user.get('ai_credits', 0)
                if current_ai < 5:
                    await message.reply(
                        f"Super Agent requires **5 AI Credits** per message. "
                        f"You have **{current_ai}**.\n"
                        f"Use `/convert_ai` to get more."
                    )
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=True)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="⚡ Super Agent — Online",
                description=(
                    "Full development pipeline activated.\n\n"
                    "**Pipeline**\n"
                    "Build code > Self-review > Optimize > Verify alignment > Final review\n\n"
                    "**Post-processing**\n"
                    "Cross-file connector · Exploit scanner · Setup script · Test guide\n\n"
                    "**Settings**\n"
                    "`creative mode on/off` — Toggle experimental features\n"
                    "`present task on/off` — Toggle plan approval\n\n"
                    "**Cost:** 5 AI Credits per message (admins bypassed)\n\n"
                    "Type `exit agent mode` to disconnect.\n"
                    "What are we building?"
                ),
                color=0x5865F2
            )
            await message.reply(embed=activate_embed)
            return

        # ========== NORMAL AGENT ACTIVATION ==========
        elif content_lower == "change to agent mode":
            if not is_admin:
                current_ai = user.get('ai_credits', 0)
                if current_ai < 3:
                    await message.reply(
                        f"Agent mode requires **3 AI Credits** per message. "
                        f"You have **{current_ai}**.\n"
                        f"Use `/convert_ai` to get more."
                    )
                    return

            user_rank = user.get("rank", "Beginner")
            self.agent.activate(message.author.id, super_mode=False)
            self.agent.sessions[message.author.id]["user_rank"] = user_rank

            activate_embed = discord.Embed(
                title="🤖 Agent Mode — Online",
                description=(
                    "Task planning and code generation activated.\n\n"
                    "**Pipeline**\n"
                    "Analyze request > Plan tasks > Execute > Present results\n\n"
                    "**Settings**\n"
                    "`creative mode on/off` — Toggle extra features (default: off)\n"
                    "`present task on/off` — Toggle plan approval (default: off)\n\n"
                    "**Commands**\n"
                    "`templates` · `review code` · `my projects` · `load project last`\n\n"
                    "**Upgrade:** `change to super agent` for full pipeline\n"
                    "**Cost:** 3 AI Credits per message\n\n"
                    "Type `exit agent mode` to go back.\n"
                    "What do you want to build?"
                ),
                color=0x5865F2
            )
            await message.reply(embed=activate_embed)
            return

        # ========== AGENT MODE DEACTIVATION ==========
        elif content_lower == "exit agent mode":
            if self.agent.is_agent_mode(message.author.id):
                was_super = self.agent.is_super_agent(message.author.id)
                self.agent.deactivate(message.author.id)
                mode_name = "Super Agent" if was_super else "Agent"

                deactivate_embed = discord.Embed(
                    title=f"🔌 {mode_name} — Disconnected",
                    description=(
                        "Back to normal chat. Your projects are saved.\n"
                        "Use `change to agent mode` or `change to super agent` anytime.\n\n"
                        "💡 I can still use agent tools (templates, review, projects, command, convert) in normal chat!"
                    ),
                    color=0x5865F2
                )
                await message.reply(embed=deactivate_embed)
            else:
                await message.reply("You're not in agent mode.")
            return

        # ========== MODE SWITCHES ==========
        elif content_lower in ("upgrade to super", "switch to super agent"):
            if self.agent.is_agent_mode(message.author.id) and not self.agent.is_super_agent(message.author.id):
                if not is_admin:
                    current_ai = user.get('ai_credits', 0)
                    if current_ai < 5:
                        await message.reply(
                            f"Super Agent requires **5 AI Credits** per message. "
                            f"You have **{current_ai}**."
                        )
                        return
                self.agent.sessions[message.author.id]["super"] = True
                await message.reply(
                    "⚡ Upgraded to **Super Agent**. Full pipeline active. Cost: 5 credits/msg."
                )
                return

        elif content_lower in ("downgrade to agent", "switch to agent"):
            if self.agent.is_agent_mode(message.author.id) and self.agent.is_super_agent(message.author.id):
                self.agent.sessions[message.author.id]["super"] = False
                await message.reply(
                    "🤖 Switched to **Normal Agent**. Cost: 3 credits/msg."
                )
                return

        # ========== HANDLE AGENT MODE MESSAGES ==========
        if self.agent.is_agent_mode(message.author.id):
            is_super = self.agent.is_super_agent(message.author.id)
            credit_cost = 5 if is_super else 3

            user = await UserProfile.get_user(message.author.id)
            current_ai = user.get('ai_credits', 0) if user else 0

            if not is_admin:
                if current_ai < credit_cost:
                    mode_name = "Super Agent" if is_super else "Agent"
                    await message.reply(
                        f"**{mode_name}** costs **{credit_cost}** AI Credits per message. "
                        f"You have **{current_ai}**.\n"
                        f"Type `exit agent mode` to switch to normal chat (1 credit/msg).\n"
                        f"Use `/convert_ai` to get more credits."
                    )
                    return

                await UserProfile.update_user(message.author.id, {
                    "ai_credits": current_ai - credit_cost
                })

            try:
                async with message.channel.typing():
                    await self.agent.handle_message(message)
            except Exception as e:
                if not is_admin:
                    await UserProfile.update_user(message.author.id, {
                        "ai_credits": current_ai
                    })
                    await message.reply(
                        f"❌ An error occurred. Your **{credit_cost}** credits have been refunded."
                    )
                else:
                    await message.reply(f"❌ An error occurred: {str(e)[:200]}")
                print(f"[Agent Error] {e}")
            return

        # ========== NORMAL AI CHAT (WITH SMART FEATURES) ==========
        user = await UserProfile.get_user(message.author.id)
        current_ai = user.get('ai_credits', 0) if user else 0

        if not is_admin:
            if current_ai <= 0:
                await message.reply(
                    f"You don't have enough AI Credits to chat with {AI_NAME}.\n\n"
                    f"**Get credits:**\n"
                    f"`/convert` — Studio Credits → pCredits\n"
                    f"`/convert_ai` — pCredits → AI Credits"
                )
                return

        # ========== COMPLEXITY CHECK ==========
        auto_switch = user.get('auto_agent_switch', False) if user else False

        should_check = len(message.content) > 30 and any(
            word in content_lower for word in [
                "make", "create", "build", "write", "code", "script", "system",
                "game", "project", "feature", "implement", "develop", "full",
                "complete", "multi", "advanced", "complex"
            ]
        )

        if should_check:
            complexity = await self._check_complexity(message.content)

            if complexity.get("needs_agent", False):
                difficulty = complexity.get("difficulty", "complex")
                reason = complexity.get("reason", "Request requires multi-file code generation")
                recommended = complexity.get("recommended_mode", "agent")
                detected_tools = complexity.get("detected_tools", [])

                if auto_switch:
                    auto_mode = recommended == "super_agent"

                    if not is_admin:
                        cost = 5 if auto_mode else 3
                        if current_ai < cost:
                            await message.reply(
                                f"⚠️ This request needs {'Super Agent' if auto_mode else 'Agent'} mode "
                                f"(**{cost}** credits/msg) but you only have **{current_ai}**.\n"
                                f"Processing in normal chat instead."
                            )
                        else:
                            await UserProfile.update_user(message.author.id, {
                                "ai_credits": current_ai - cost
                            })

                            user_rank = user.get("rank", "Beginner") if user else "Beginner"
                            self.agent.activate(message.author.id, super_mode=auto_mode)
                            self.agent.sessions[message.author.id]["user_rank"] = user_rank

                            mode_name = "Super Agent" if auto_mode else "Agent"
                            auto_embed = discord.Embed(
                                title=f"🔄 Auto-Switched to {mode_name}",
                                description=(
                                    f"**Reason:** {reason}\n"
                                    f"**Difficulty:** {difficulty.title()}\n\n"
                                    f"Processing your request..."
                                ),
                                color=0x5865F2
                            )
                            auto_embed.set_footer(text="Type 'auto switch off' to disable auto-switching")
                            await message.reply(embed=auto_embed)

                            try:
                                async with message.channel.typing():
                                    await self.agent.handle_message(message)
                            except Exception as e:
                                if not is_admin:
                                    await UserProfile.update_user(message.author.id, {
                                        "ai_credits": current_ai
                                    })
                                    await message.reply(f"❌ Error. Credits refunded.")
                                print(f"[Auto Agent Error] {e}")
                            return
                else:
                    diff_icons = {"simple": "🟢", "moderate": "🟡", "complex": "🟠", "advanced": "🔴"}
                    diff_icon = diff_icons.get(difficulty, "⚪")

                    switch_embed = discord.Embed(
                        title="🔍 Complex Request Detected",
                        description=(
                            f"{diff_icon} **Difficulty:** {difficulty.title()}\n"
                            f"**Reason:** {reason}\n"
                            f"**Recommended:** {recommended.replace('_', ' ').title()}\n\n"
                            f"This request would produce better results in **Agent Mode**.\n"
                            f"Agent mode creates multi-file projects with task planning.\n\n"
                            f"**Choose an option below:**"
                        ),
                        color=0xE67E22
                    )

                    if detected_tools:
                        tool_text = ", ".join([f"`{t}`" for t in detected_tools])
                        switch_embed.add_field(
                            name="🛠️ Relevant Tools",
                            value=f"These agent tools would help: {tool_text}",
                            inline=False
                        )

                    switch_embed.add_field(
                        name="💰 Cost Comparison",
                        value=(
                            "💬 Normal Chat: **1 credit/msg** (simplified response)\n"
                            "🤖 Agent Mode: **3 credits/msg** (full project)\n"
                            "⚡ Super Agent: **5 credits/msg** (reviewed + optimized)"
                        ),
                        inline=False
                    )

                    switch_embed.set_footer(text=f"Your credits: {current_ai} AI Credits")

                    view = AgentSwitchView(self, message.author.id, message, difficulty, reason)
                    await message.reply(embed=switch_embed, view=view)
                    return

        # ========== NORMAL RESPONSE (with tool support) ==========
        if not is_admin:
            await UserProfile.update_user(message.author.id, {
                "ai_credits": current_ai - 1
            })

        try:
            async with message.channel.typing():
                response = await self.get_ai_response(message)
                await ai_handler.send_response(
                    message=message,
                    ai_text=response,
                    user_name=message.author.display_name
                )
        except Exception as e:
            if not is_admin:
                await UserProfile.update_user(message.author.id, {
                    "ai_credits": current_ai
                })
            await message.reply(f"❌ AI Error: {str(e)[:200]}")
            print(f"[AI Chat Error] {e}")


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))