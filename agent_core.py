import re
import json
import asyncio
import time
import io
import os
import discord
from datetime import datetime
from anthropic import Anthropic
from ai_tools import SplitMessageTool, CodeThreadTool, ReadMessagesTool
from agent_features import (
    TemplateLibrary, ProjectMemory, FileTreeExporter,
    CodeReviewTool, SmartCodeConnector, AntiExploitScanner,
    SetupScriptGenerator, AutoTestGenerator, LiveCodeExplainer
)

# Anthropic Integration Setup
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

anthropic_client = Anthropic(
    api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
    base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
)


# ============================================================
# AGENT MEMORY
# ============================================================

class AgentMemory:
    def __init__(self):
        self.hot = []
        self.warm = []
        self.current_plan = None
        self.max_hot = 5
        self.max_warm = 3
        self.max_chars = 3000

    def add_message(self, role, content):
        self.hot.append({"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()})
        self._optimize()

    def save_plan(self, plan):
        if self.current_plan:
            summary = self._summarize_plan(self.current_plan)
            self.warm.append(summary)
            if len(self.warm) > self.max_warm:
                self.warm.pop(0)
        self.current_plan = plan

    def _summarize_plan(self, plan):
        tasks = ", ".join([t.get("name", "?") for t in plan.get("tasks", [])])
        return {
            "request": plan.get("original_request", "")[:200],
            "difficulty": plan.get("difficulty", ""),
            "tasks": tasks
        }

    def _optimize(self):
        if len(self.hot) > self.max_hot:
            old = self.hot.pop(0)
            self.warm.append({"messages": [old["role"] + ": " + old["content"][:100]]})
        total = sum(len(m.get("content", "")) for m in self.hot) + sum(len(str(w)) for w in self.warm)
        while total > self.max_chars and self.warm:
            self.warm.pop(0)
            total = sum(len(m.get("content", "")) for m in self.hot) + sum(len(str(w)) for w in self.warm)

    def get_context_string(self):
        parts = []
        if self.warm:
            parts.append("=== PREVIOUS CONTEXT ===")
            for item in self.warm:
                if isinstance(item, dict):
                    if "request" in item:
                        parts.append("Prev: " + item.get("request", ""))
                    elif "messages" in item:
                        for m in item["messages"]:
                            parts.append("  " + m)
        if self.current_plan:
            parts.append("=== CURRENT PLAN ===")
            parts.append("Request: " + self.current_plan.get("original_request", ""))
            for t in self.current_plan.get("tasks", []):
                status = "DONE" if t.get("completed") else "PENDING"
                parts.append("  [" + status + "] " + t.get("name", ""))
        if self.hot:
            parts.append("=== RECENT ===")
            for msg in self.hot:
                parts.append(msg["role"] + ": " + msg["content"])
        return "\n".join(parts)

    def clear(self):
        self.hot = []
        self.warm = []
        self.current_plan = None


# ============================================================
# CODE STANDARDS
# ============================================================

CODE_STANDARDS = """
CODE QUALITY RULES (MUST FOLLOW):
1. Use task.wait() NOT wait()
2. Use proper variable naming (camelCase for local, PascalCase for functions)
3. Wrap DataStore calls in pcall()
4. Always nil-check: FindFirstChild before accessing
5. Add type comments for function parameters
6. Validate RemoteEvent data on server side
7. Use local variables (never global)
8. Add error handling for all network calls
9. Clean up connections on player leaving
10. Use task.spawn() for async operations
"""


def get_complexity_prompt(rank):
    if rank == "Beginner":
        return "USER IS A BEGINNER. Write simple code with LOTS of comments explaining every step. Use basic patterns only."
    elif rank == "Learner":
        return "USER IS A LEARNER. Write clear code with helpful comments. Use standard patterns."
    elif rank == "Expert":
        return "USER IS AN EXPERT. Write clean professional code. Use advanced patterns. Comments only for complex logic."
    elif rank == "Master":
        return "USER IS A MASTER. Write optimized production code. Advanced OOP. Minimal comments."
    return "Write clear, well-commented code."


# ============================================================
# ANIMATION CONSTANTS
# ============================================================

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
PROGRESS_SPINNER = ["◐", "◓", "◑", "◒"]
PHASE_ICONS = {
    "analyzing": "🔍",
    "planning": "📋",
    "building": "🔨",
    "reviewing": "🔎",
    "optimizing": "⚡",
    "connecting": "🔗",
    "scanning": "🛡️",
    "finalizing": "📦",
    "complete": "✅",
    "error": "❌",
    "idle": "⏳",
}
MILESTONE_MESSAGES = {
    25: "Quarter way there!",
    50: "Halfway done!",
    75: "Almost there!",
    100: "Build complete!",
}
BAR_STYLES = {
    "main": {"filled": "█", "partial": "▓", "empty": "░"},
    "mini": {"filled": "▰", "partial": "▰", "empty": "▱"},
    "slim": {"filled": "━", "partial": "╍", "empty": "┄"},
}
PHASE_COLORS = {
    "analyzing": 0x5865F2,
    "planning": 0x9B59B6,
    "building": 0xE67E22,
    "reviewing": 0x3498DB,
    "optimizing": 0xF1C40F,
    "connecting": 0x1ABC9C,
    "scanning": 0xE74C3C,
    "finalizing": 0x2ECC71,
    "complete": 0x57F287,
    "error": 0xED4245,
    "idle": 0x99AAB5,
}
FRAME_INTERVAL = 0.7


# ============================================================
# LIVE PANEL
# ============================================================

class LivePanel:
    """
    A visually rich, animated embed panel that updates in-place
    showing real-time progress with spinners, phase tracking,
    mini progress bars, ETA, and milestone celebrations.
    """

    def __init__(self, channel, title="Agent"):
        self.channel = channel
        self.title = title
        self.message = None

        # Status
        self.status = "idle"
        self.phase = "idle"
        self.phase_history = []

        # Tasks
        self.total_tasks = 0
        self.completed_tasks = 0
        self.task_statuses = {}
        self.task_times = {}

        # Timing
        self.start_time = time.time()
        self.phase_start_time = time.time()
        self.task_start_times = {}

        # Logging
        self.log_lines = []
        self.max_visible_logs = 12

        # Animation
        self._active_step = None
        self._animation_task = None
        self._frame_index = 0
        self._spinner_index = 0
        self._animating = False
        self._lock = asyncio.Lock()

        # Stats
        self.total_lines_generated = 0
        self.total_api_calls = 0
        self.files_created = 0
        self.bugs_fixed = 0
        self.milestones_hit = set()

        # Sub-steps within current task
        self._sub_steps = []
        self._current_sub_step = None

    # ============================================================
    # EMBED BUILDER
    # ============================================================

    def _build_embed(self):
        elapsed = time.time() - self.start_time

        # Dynamic color based on phase
        color = PHASE_COLORS.get(self.phase, 0x99AAB5)

        # Dynamic title with phase icon
        icon = PHASE_ICONS.get(self.phase, "⏳")
        if self.status == "running" and self._animating:
            spinner = SPINNER_FRAMES[self._spinner_index % len(SPINNER_FRAMES)]
            title_text = f"{spinner} {self.title}"
        elif self.status == "complete":
            title_text = f"✅ {self.title}"
        elif self.status == "error":
            title_text = f"❌ {self.title}"
        else:
            title_text = f"{icon} {self.title}"

        embed = discord.Embed(title=title_text, color=color)
        sections = []

        # ---- MAIN PROGRESS BAR ----
        if self.total_tasks > 0:
            pct = (self.completed_tasks / self.total_tasks) * 100
            bar = self._build_bar(pct, 22, "main")
            eta = self._estimate_eta()

            progress_text = f"```ansi\n{bar} {pct:.0f}%\n"
            progress_text += f"Tasks: {self.completed_tasks}/{self.total_tasks}"
            if eta:
                progress_text += f"  ·  ETA: {eta}"
            progress_text += f"  ·  {self._format_time(elapsed)}\n```"
            sections.append(progress_text)

            # Check milestones
            for milestone, msg in MILESTONE_MESSAGES.items():
                if pct >= milestone and milestone not in self.milestones_hit:
                    self.milestones_hit.add(milestone)

        # ---- PHASE INDICATOR ----
        if self.phase != "idle":
            phase_display = self._build_phase_tracker()
            if phase_display:
                sections.append(phase_display)

        # ---- TASK STATUS GRID ----
        if self.task_statuses:
            task_grid = self._build_task_grid()
            if task_grid:
                sections.append(task_grid)

        # ---- LOG SECTION ----
        log_section = self._build_log_section()
        if log_section:
            sections.append(log_section)

        embed.description = "\n".join(sections) if sections else "```\nInitializing...\n```"

        # ---- FOOTER WITH STATS ----
        footer_parts = []
        if self.status == "running":
            phase_elapsed = time.time() - self.phase_start_time
            footer_parts.append(f"Phase: {self.phase} ({self._format_time(phase_elapsed)})")
        footer_parts.append(f"Elapsed: {self._format_time(elapsed)}")

        stats = []
        if self.total_lines_generated > 0:
            stats.append(f"{self.total_lines_generated} lines")
        if self.files_created > 0:
            stats.append(f"{self.files_created} files")
        if self.total_api_calls > 0:
            stats.append(f"{self.total_api_calls} API calls")
        if self.bugs_fixed > 0:
            stats.append(f"{self.bugs_fixed} bugs fixed")
        if stats:
            footer_parts.append(" · ".join(stats))

        embed.set_footer(text="  |  ".join(footer_parts))

        return embed

    # ============================================================
    # VISUAL BUILDERS
    # ============================================================

    def _build_bar(self, percentage, width, style="main"):
        s = BAR_STYLES[style]
        filled_count = int((percentage / 100) * width)
        has_partial = percentage > 0 and filled_count < width

        bar = s["filled"] * filled_count
        if has_partial and filled_count < width:
            bar += s["partial"]
            bar += s["empty"] * (width - filled_count - 1)
        else:
            bar += s["empty"] * (width - filled_count)

        return f"[{bar}]"

    def _build_phase_tracker(self):
        """Build a horizontal phase progress indicator"""
        all_phases = ["analyzing", "planning", "building", "reviewing", "optimizing", "connecting", "scanning", "finalizing"]

        relevant = []
        completed_phases = [ph["name"] for ph in self.phase_history]
        for p in all_phases:
            if p in completed_phases or p == self.phase:
                relevant.append(p)

        if not relevant:
            return ""

        parts = []
        for p in relevant:
            icon = PHASE_ICONS.get(p, "○")

            if p == self.phase and self.status == "running":
                spinner = PROGRESS_SPINNER[self._spinner_index % len(PROGRESS_SPINNER)]
                parts.append(f"{spinner} **{p.title()}**")
            elif p in completed_phases:
                parts.append(f"~~{icon} {p.title()}~~")
            else:
                parts.append(f"○ {p.title()}")

        return " → ".join(parts)

    def _build_task_grid(self):
        """Build a compact grid showing all task statuses"""
        if not self.task_statuses:
            return ""

        lines = []
        for task_id, info in sorted(self.task_statuses.items()):
            status = info.get("status", "pending")
            name = info.get("name", f"Task {task_id}")[:30]
            task_time = info.get("time", 0)
            task_lines = info.get("lines", 0)

            if status == "complete":
                icon = "✅"
                detail = f" — {task_lines} lines, {task_time:.1f}s"
            elif status == "running":
                spinner = SPINNER_FRAMES[self._spinner_index % len(SPINNER_FRAMES)]
                icon = spinner
                elapsed = time.time() - self.task_start_times.get(task_id, time.time())
                detail = f" — {self._format_time(elapsed)}"

                if self._sub_steps:
                    done = sum(1 for s in self._sub_steps if s.get("done"))
                    total = len(self._sub_steps)
                    mini_bar = self._build_bar((done / max(total, 1)) * 100, 8, "mini")
                    detail += f" {mini_bar}"
            elif status == "error":
                icon = "❌"
                detail = " — Failed"
            else:
                icon = "⬜"
                detail = ""

            lines.append(f"{icon} `{task_id}` {name}{detail}")

        return "\n".join(lines)

    def _build_log_section(self):
        """Build the scrolling log with active step animation"""
        display_lines = []

        visible = self.log_lines[-self.max_visible_logs:]
        for line in visible:
            display_lines.append(line)

        if self._active_step and self._animating:
            spinner = SPINNER_FRAMES[self._frame_index % len(SPINNER_FRAMES)]
            timestamp = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - self.phase_start_time
            display_lines.append(f"  {timestamp}  {spinner} {self._active_step} ({self._format_time(elapsed)})")

        if not display_lines:
            return ""

        log_text = "\n".join(display_lines)
        return f"```ansi\n{log_text}\n```"

    def _estimate_eta(self):
        """Estimate remaining time based on completed task times"""
        if self.completed_tasks == 0:
            return None

        elapsed = time.time() - self.start_time
        avg_per_task = elapsed / self.completed_tasks
        remaining_tasks = self.total_tasks - self.completed_tasks

        if remaining_tasks <= 0:
            return None

        eta_seconds = avg_per_task * remaining_tasks
        return self._format_time(eta_seconds)

    def _format_time(self, seconds):
        """Format seconds into human readable string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes < 60:
            return f"{minutes}m {secs}s"
        hours = int(minutes // 60)
        mins = minutes % 60
        return f"{hours}h {mins}m"

    # ============================================================
    # MESSAGE MANAGEMENT
    # ============================================================

    async def send(self):
        embed = self._build_embed()
        self.message = await self.channel.send(embed=embed)
        return self.message

    async def _safe_update(self):
        if not self.message:
            return
        if self._lock.locked():
            return  # Skip this frame instead of waiting
        async with self._lock:
            try:
                embed = self._build_embed()
                await self.message.edit(embed=embed)
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    retry_after = getattr(e, 'retry_after', 2.0)
                    await asyncio.sleep(retry_after)
                # Otherwise just skip this frame
    
    async def update(self):
        await self._safe_update()

    # ============================================================
    # ANIMATION ENGINE
    # ============================================================

    async def _animation_loop(self):
        fail_count = 0
        while self._animating:
            self._frame_index = (self._frame_index + 1) % len(SPINNER_FRAMES)
            self._spinner_index = (self._spinner_index + 1) % len(PROGRESS_SPINNER)

            try:
                await self._safe_update()
                fail_count = 0  # Reset on success
            except Exception:
                fail_count += 1

            # Dynamic interval: slow down if rate limited, speed up when clear
            if fail_count > 2:
                interval = min(FRAME_INTERVAL + (fail_count * 0.5), 3.0)
            else:
                interval = FRAME_INTERVAL

            await asyncio.sleep(interval)

    def _start_animation(self, step_text):
        self._stop_animation_sync()
        self._active_step = step_text
        self._frame_index = 0
        self._animating = True
        self._animation_task = asyncio.create_task(self._animation_loop())

    def _stop_animation_sync(self):
        self._animating = False
        self._active_step = None
        if self._animation_task and not self._animation_task.done():
            self._animation_task.cancel()
        self._animation_task = None

    async def _stop_animation(self):
            self._animating = False
            self._active_step = None
            if self._animation_task and not self._animation_task.done():
                self._animation_task.cancel()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._animation_task),
                        timeout=2.0
                    )
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            self._animation_task = None

    # ============================================================
    # PHASE MANAGEMENT
    # ============================================================

    async def set_phase(self, phase_name):
        """Transition to a new phase with visual tracking"""
        if self.phase != "idle" and self.phase != phase_name:
            phase_time = time.time() - self.phase_start_time
            self.phase_history.append({
                "name": self.phase,
                "duration": phase_time,
                "timestamp": datetime.now().isoformat()
            })

        self.phase = phase_name
        self.phase_start_time = time.time()
        self.status = "running"
        await self._safe_update()

    # ============================================================
    # TASK MANAGEMENT
    # ============================================================

    def set_task_info(self, task_num, total):
        self.total_tasks = total
        for i in range(1, total + 1):
            if i not in self.task_statuses:
                self.task_statuses[i] = {
                    "status": "pending",
                    "name": f"Task {i}",
                    "lines": 0,
                    "time": 0
                }

    def register_task(self, task_id, name):
        """Register a task with its name for display"""
        self.task_statuses[task_id] = {
            "status": "pending",
            "name": name[:35],
            "lines": 0,
            "time": 0
        }

    async def start_task(self, task_id, name=None):
        """Mark a task as actively running"""
        if name:
            self.task_statuses[task_id] = {
                "status": "running",
                "name": name[:35],
                "lines": 0,
                "time": 0
            }
        elif task_id in self.task_statuses:
            self.task_statuses[task_id]["status"] = "running"
        else:
            self.task_statuses[task_id] = {
                "status": "running",
                "name": f"Task {task_id}",
                "lines": 0,
                "time": 0
            }

        self.task_start_times[task_id] = time.time()
        self._sub_steps = []
        self._current_sub_step = None
        await self._safe_update()

    def complete_task(self, task_num, lines_count=0, seconds=0):
        """Mark a task as completed with stats"""
        self.completed_tasks += 1
        self.total_lines_generated += lines_count
        self.files_created += 1

        if task_num in self.task_statuses:
            self.task_statuses[task_num]["status"] = "complete"
            self.task_statuses[task_num]["lines"] = lines_count
            self.task_statuses[task_num]["time"] = seconds

        self.log_done(f"Task {task_num} — {lines_count} lines, {seconds}s")

    def fail_task(self, task_num, reason=""):
        """Mark a task as failed"""
        if task_num in self.task_statuses:
            self.task_statuses[task_num]["status"] = "error"
        self.log_error(f"Task {task_num} failed{': ' + reason if reason else ''}")

    # ============================================================
    # SUB-STEP TRACKING
    # ============================================================

    async def add_sub_step(self, name):
        """Add a sub-step to the current task"""
        self._sub_steps.append({"name": name, "done": False})
        self._current_sub_step = name
        await self._safe_update()

    async def complete_sub_step(self, name=None):
        """Mark a sub-step as done"""
        target = name or self._current_sub_step
        for step in self._sub_steps:
            if step["name"] == target:
                step["done"] = True
                break
        self._current_sub_step = None
        await self._safe_update()

    # ============================================================
    # LOGGING
    # ============================================================

    def log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if text.strip() == "":
            self.log_lines.append("")
        else:
            self.log_lines.append(f"  {timestamp}  │ {text}")

    def log_done(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"  {timestamp}  ✓ {text}")

    def log_warn(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"  {timestamp}  ⚠ {text}")

    def log_error(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"  {timestamp}  ✗ {text}")

    def log_info(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"  {timestamp}  ℹ {text}")

    def log_stat(self, label, value):
        """Log a key-value stat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"  {timestamp}  ▸ {label}: {value}")

    def increment_api_calls(self, count=1):
        self.total_api_calls += count

    def increment_bugs_fixed(self, count=1):
        self.bugs_fixed += count

    # ============================================================
    # STEP ANIMATION
    # ============================================================

    async def start_step(self, text):
        if self._active_step:
            await self._stop_animation()
        self._start_animation(text)

    async def complete_step(self, done_text=None):
        step = self._active_step or ""
        await self._stop_animation()
        if done_text:
            self.log_done(done_text)
        else:
            self.log_done(step)
        await self._safe_update()

    # ============================================================
    # FINISH / FAIL
    # ============================================================

    async def finish(self, summary_text=None):
        await self._stop_animation()
        self.status = "complete"
        self.phase = "complete"

        elapsed = time.time() - self.start_time

        if summary_text:
            self.log("")
            self.log(f"{'═' * 40}")
            self.log(summary_text)
            self.log(f"{'═' * 40}")

        stats = []
        if self.files_created > 0:
            stats.append(f"{self.files_created} files")
        if self.total_lines_generated > 0:
            stats.append(f"{self.total_lines_generated} lines")
        if self.total_api_calls > 0:
            stats.append(f"{self.total_api_calls} API calls")
        if self.bugs_fixed > 0:
            stats.append(f"{self.bugs_fixed} bugs fixed")
        stats.append(f"{self._format_time(elapsed)} total")

        if stats:
            self.log(f"  Final: {' · '.join(stats)}")

        await self._safe_update()

    async def fail(self, error_text=None):
        await self._stop_animation()
        self.status = "error"
        self.phase = "error"
        if error_text:
            self.log_error(error_text)
        await self._safe_update()


# ============================================================
# FILE SENDER
# ============================================================

class CodeFileSender:
    """
    Sends code as .lua / .py / .js file attachments.
    """

    EXTENSIONS = {
        "lua": ".lua",
        "luau": ".lua",
        "python": ".py",
        "py": ".py",
        "javascript": ".js",
        "js": ".js",
        "typescript": ".ts",
        "ts": ".ts",
        "json": ".json",
        "txt": ".txt",
    }

    def detect_language(self, filename):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        lang_map = {
            "lua": "lua", "luau": "lua",
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "json": "json",
        }
        return lang_map.get(ext, "lua")

    def make_file(self, filename, code):
        """Create a discord.File from code string"""
        buffer = io.BytesIO(code.encode("utf-8"))
        return discord.File(buffer, filename=filename)

    def make_files(self, files_dict):
        """Create multiple discord.File objects"""
        result = []
        for filename, code in files_dict.items():
            if code and code.strip():
                result.append(self.make_file(filename, code))
        return result

    async def send_files_to_thread(self, thread, files_dict, file_tree=None):
        """Send all files as attachments in a thread."""
        if file_tree:
            await thread.send(f"```\n{file_tree}\n```")
            await asyncio.sleep(0.3)

        file_items = list(files_dict.items())
        batch_size = 8

        for i in range(0, len(file_items), batch_size):
            batch = file_items[i:i + batch_size]
            files = []
            descriptions = []

            for filename, code in batch:
                if not code or not code.strip():
                    continue

                buffer = io.BytesIO(code.encode("utf-8"))
                files.append(discord.File(buffer, filename=filename))

                line_count = len(code.strip().split("\n"))
                descriptions.append(f"**{filename}** — {line_count} lines")

            if files:
                desc_text = "\n".join(descriptions)
                await thread.send(content=desc_text, files=files)
                await asyncio.sleep(0.5)

    async def send_single_file(self, channel, filename, code, description=None):
        """Send a single code file as attachment"""
        if not code or not code.strip():
            return

        buffer = io.BytesIO(code.encode("utf-8"))
        file = discord.File(buffer, filename=filename)
        line_count = len(code.strip().split("\n"))

        content = description or f"**{filename}** — {line_count} lines"
        await channel.send(content=content, file=file)


# ============================================================
# AGENT MODE
# ============================================================

class AgentMode:
    def __init__(self, genai_client, model_name, personality):
        self.genai_client = genai_client
        self.model_name = model_name
        self.personality = personality
        self.sessions = {}
        self._locks = {}
        self.splitter = SplitMessageTool()
        self.code_thread = CodeThreadTool()
        self.reader = ReadMessagesTool()
        self.templates = TemplateLibrary()
        self.project_memory = ProjectMemory()
        self.file_exporter = FileTreeExporter()
        self.file_sender = CodeFileSender()
        self.code_reviewer = CodeReviewTool(genai_client, model_name)
        self.connector = SmartCodeConnector(genai_client, model_name)
        self.exploit_scanner = AntiExploitScanner(genai_client, model_name)
        self.setup_gen = SetupScriptGenerator(genai_client, model_name)
        self.test_gen = AutoTestGenerator(genai_client, model_name)
        self.explainer = LiveCodeExplainer(genai_client, model_name)

    def _get_lock(self, user_id):
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    def is_agent_mode(self, user_id):
        return user_id in self.sessions and self.sessions[user_id].get("active", False)

    def is_super_agent(self, user_id):
        return user_id in self.sessions and self.sessions[user_id].get("super", False)

    def activate(self, user_id, super_mode=False):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "active": True,
                "super": super_mode,
                "memory": AgentMemory(),
                "state": "idle",
                "current_plan": None,
                "creative": False,
                "present_task": False,
                "user_rank": "Beginner"
            }
        else:
            self.sessions[user_id]["active"] = True
            self.sessions[user_id]["super"] = super_mode
            self.sessions[user_id]["state"] = "idle"

    def deactivate(self, user_id):
        if user_id in self.sessions:
            self.sessions[user_id]["active"] = False
            self.sessions[user_id]["state"] = "idle"
            self.sessions[user_id]["current_plan"] = None
            self.sessions[user_id]["memory"].clear()

    async def _call_ai(self, prompt, timeout=120):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model=self.model_name,
                    contents=prompt
                ),
                timeout=timeout
            )
            return response.text or ""
        except asyncio.TimeoutError:
            print(f"[Agent] AI call timed out after {timeout}s")
            return "ERROR: AI request timed out. Please try again."
        except Exception as e:
            print(f"[Agent] AI Error: {e}")
            return f"ERROR: {e}"

    async def handle_message(self, message):
        lock = self._get_lock(message.author.id)
        async with lock:
            await self._handle_message_internal(message)

    async def _handle_message_internal(self, message):
        user_id = message.author.id
        session = self.sessions[user_id]
        memory = session["memory"]
        state = session["state"]
        content_lower = message.content.strip().lower()

        memory.add_message("user", message.content)

        # Settings
        if content_lower == "creative mode on":
            session["creative"] = True
            await message.reply("Creative mode is now **on**.")
            return
        if content_lower == "creative mode off":
            session["creative"] = False
            await message.reply("Creative mode is now **off**.")
            return
        if content_lower in ("enable present task", "present task on"):
            session["present_task"] = True
            await message.reply("Task approval is now **on**.")
            return
        if content_lower in ("disable present task", "present task off"):
            session["present_task"] = False
            await message.reply("Task approval is now **off**.")
            return

        # Commands
        if content_lower in ("my projects", "list projects"):
            return await self._show_projects(message, user_id)
        if content_lower.startswith("load project"):
            return await self._load_project(message, user_id, content_lower)
        if content_lower in ("templates", "show templates"):
            return await self._show_templates(message)
        if content_lower.startswith("use template "):
            return await self._use_template(message, session, content_lower)
        if content_lower in ("review code",) or content_lower.startswith("review this"):
            return await self._start_code_review(message, session)

        # State routing
        if state == "idle":
            return await self._start_pipeline(message, session)
        elif state == "waiting_approval":
            return await self._handle_approval(message, session)
        elif state == "executing":
            await message.reply("Working on your previous request. Please wait.")
            return
        elif state == "follow_up":
            return await self._handle_followup(message, session)
        elif state == "waiting_code_review":
            return await self._handle_code_review_input(message, session)

    # ========================================================
    # PIPELINE - START
    # ========================================================

    async def _start_pipeline(self, message, session):
        memory = session["memory"]
        user_input = message.content
        is_super = session.get("super", False)
        is_creative = session.get("creative", False)
        channel = message.channel
        mode_label = "Super Agent" if is_super else "Agent"

        # Create live panel
        panel = LivePanel(channel, title=f"{mode_label} — Processing")
        await panel.send()

        # Phase 1: Analysis
        await panel.set_phase("analyzing")
        await panel.start_step("Analyzing request")

        memory_context = memory.get_context_string()
        channel_context = await self.reader.get_context(channel, before=message)

        template_matches = self.templates.search(user_input)
        template_context = ""
        if template_matches:
            template_context = "\nTEMPLATE AVAILABLE: " + self.templates.get_template_for_prompt(template_matches[0]["key"])

        await panel.complete_step("Request analyzed")

        complexity = get_complexity_prompt(session.get("user_rank", "Beginner"))

        if is_creative:
            creative_instruction = "\nCREATIVE MODE ON: Add extra features. Production-quality."
        else:
            creative_instruction = "\nCREATIVE MODE OFF: Do EXACTLY what asked. Minimal tasks."

        if template_matches:
            panel.log_info(f"Matched template: {template_matches[0]['key']}")
            await panel.update()

        # Phase 2: Planning
        await panel.set_phase("planning")
        await panel.start_step("Generating task plan")

        plan_prompt = (
            "You are an AI development agent.\n\n"
            "System: " + self.personality + "\n"
            + CODE_STANDARDS + "\n"
            + complexity + "\n"
            + creative_instruction + "\n\n"
            "CONTEXT:\n" + memory_context + "\n"
            "CHANNEL:\n" + channel_context + "\n"
            + template_context + "\n\n"
            "USER REQUEST: " + user_input + "\n\n"
            "Create a JSON task plan (no markdown, raw JSON only):\n"
            '{"difficulty": "Easy/Medium/Hard/Complex",'
            '"estimated_seconds": 30,'
            '"summary": "brief summary",'
            '"tasks": ['
            '{"id": 1, "name": "task name", "description": "what to build", "estimated_lines": 50},'
            '{"id": 2, "name": "task name", "description": "what to build", "estimated_lines": 80}'
            ']}\n\n'
            "Rules: Max 8 tasks. Each task = one file. ONLY output JSON."
        )
        plan_data = await self._call_ai(plan_prompt)
        panel.increment_api_calls()
        plan = self._parse_plan(plan_data, user_input)
        if template_matches:
            plan["template_used"] = template_matches[0]["key"]

        session["current_plan"] = plan
        memory.save_plan(plan)

        await panel.complete_step(f"Plan ready — {len(plan['tasks'])} tasks, {plan['difficulty']}")

        # Log task overview
        for t in plan["tasks"]:
            panel.log_stat(f"Task {t['id']}", f"{t['name']} (~{t.get('estimated_lines', '?')} lines)")
        await panel.update()

        # Present task approval?
        if session.get("present_task", False):
                session["state"] = "waiting_approval"

                # Difficulty badge
                diff = plan.get("difficulty", "Medium")
                diff_icons = {"Easy": "🟢", "Medium": "🟡", "Hard": "🟠", "Complex": "🔴"}
                diff_icon = diff_icons.get(diff, "⚪")

                total_est_lines = sum(t.get("estimated_lines", 0) for t in plan["tasks"])

                embed = discord.Embed(
                    title="📋 Task Plan — Awaiting Approval",
                    color=0x5865F2
                )

                # Header info
                header = (
                    f"{diff_icon} **Difficulty:** {diff}\n"
                    f"📁 **Tasks:** {len(plan['tasks'])}\n"
                    f"📝 **Est. Lines:** ~{total_est_lines}\n"
                    f"💬 **Request:** {plan.get('original_request', '')[:150]}"
                )
                embed.description = header

                # Each task as a field
                for task in plan["tasks"]:
                    lines_est = task.get("estimated_lines", "?")
                    task_header = f"📄 ~{lines_est} lines"

                    # Wrap description nicely
                    desc = task.get("description", "No description")
                    if len(desc) > 200:
                        desc = desc[:197] + "..."

                    embed.add_field(
                        name=f"`{task['id']}` {task['name']}",
                        value=f"{task_header}\n```\n{desc}\n```",
                        inline=False
                    )

                # Controls footer
                embed.add_field(
                    name="─────────────────────────────",
                    value=(
                        "✅ `approve` — Start building\n"
                        "✏️ `edit <num> <desc>` — Change a task\n"
                        "➕ `add <desc>` — Add a task\n"
                        "🗑️ `remove <num>` — Remove a task\n"
                        "❌ `cancel` — Cancel plan"
                    ),
                    inline=False
                )

                embed.set_footer(text=f"Plan generated in {round(time.time() - panel.start_time, 1)}s")

                await panel.finish("Waiting for approval")
                await channel.send(embed=embed)
                return

        session["state"] = "executing"
        await self._execute_pipeline(message, session, panel)

    # ========================================================
    # PIPELINE - EXECUTE
    # ========================================================

    async def _execute_pipeline(self, message, session, panel=None):
        plan = session["current_plan"]
        memory = session["memory"]
        tasks = plan["tasks"]
        channel = message.channel
        is_super = session.get("super", False)
        all_files = {}
        complexity = get_complexity_prompt(session.get("user_rank", "Beginner"))
        mode_label = "Super Agent" if is_super else "Agent"

        template_code = ""
        if plan.get("template_used"):
            template_code = self.templates.get_template_for_prompt(plan["template_used"])

        if panel is None:
            panel = LivePanel(channel, title=f"{mode_label} — Executing")
            await panel.send()

        # Register all tasks
        panel.total_tasks = len(tasks)
        panel.title = f"{mode_label} — Building"
        for task in tasks:
            panel.register_task(task["id"], task["name"])

        await panel.set_phase("building")
        await panel.start_step("Initializing build pipeline")
        await asyncio.sleep(0.6)
        await panel.complete_step("Build pipeline ready")

        setup_script = None
        test_guide = None

        # Pipeline timeout
        pipeline_start = time.time()
        max_pipeline_time = len(tasks) * 150
        
        for task_idx, task in enumerate(tasks):
            task_start = time.time()
            task_num = task["id"]

            await panel.start_task(task_num, task["name"])

            try:
                # ---- WRITING CODE ----
                await panel.start_step(f"Task {task_num}/{len(tasks)}: {task['name']} — Writing code")

                task_prompt = self._build_task_prompt(plan, tasks, task, complexity, template_code)
                code_result = await self._call_ai(task_prompt)
                panel.increment_api_calls()

                # Check if AI returned an error
                if code_result.startswith("ERROR:"):
                    panel.fail_task(task_num, code_result)
                    await panel.complete_step(f"Task {task_num} — Failed: {code_result[:50]}")
                    continue

                await panel.complete_step(f"Task {task_num} — Code generated")

                if is_super:
                    # ===== SUPER AGENT PIPELINE =====
                    await panel.set_phase("reviewing")

                    # SELF REVIEW
                    await panel.add_sub_step("Self Review")
                    await panel.start_step(f"Task {task_num} — Self-review")

                    review_prompt = (
                        "Review this Luau code for bugs, errors, and issues:\n\n"
                        + code_result[:3000] + "\n\n"
                        "If there are bugs, fix them and return the COMPLETE fixed code.\n"
                        "If no bugs, return the code as-is.\n"
                        "Start with BUGS FOUND: X\nThen the complete code."
                    )
                    reviewed = await self._call_ai(review_prompt)
                    panel.increment_api_calls()

                    if not reviewed.startswith("ERROR:"):
                        if "BUGS FOUND: 0" not in reviewed.upper():
                            code_result = reviewed
                            panel.increment_bugs_fixed()
                            await panel.complete_step(f"Task {task_num} — Fixed issues")
                        else:
                            await panel.complete_step(f"Task {task_num} — Review passed")
                    else:
                        await panel.complete_step(f"Task {task_num} — Review skipped (timeout)")
                    await panel.complete_sub_step("Self Review")

                    # OPTIMIZE
                    await panel.set_phase("optimizing")
                    await panel.add_sub_step("Optimize")
                    await panel.start_step(f"Task {task_num} — Optimizing")

                    upgrade_prompt = (
                        "Upgrade this Luau code:\n"
                        "- Add missing error handling\n"
                        "- Optimize performance\n"
                        "- Add input validation\n"
                        "- Improve structure\n\n"
                        + code_result[:3000] + "\n\n"
                        "Return COMPLETE upgraded code. Start with FILENAME:"
                    )
                    upgraded = await self._call_ai(upgrade_prompt)
                    panel.increment_api_calls()

                    if not upgraded.startswith("ERROR:"):
                        code_result = upgraded
                        await panel.complete_step(f"Task {task_num} — Optimized")
                    else:
                        await panel.complete_step(f"Task {task_num} — Optimize skipped (timeout)")
                    await panel.complete_sub_step("Optimize")

                    # VERIFY UPGRADES
                    await panel.add_sub_step("Verify")
                    await panel.start_step(f"Task {task_num} — Verifying upgrades")

                    review2_prompt = (
                        "Review this upgraded code for any new bugs:\n\n"
                        + code_result[:3000] + "\n\n"
                        "Fix any issues. Return COMPLETE fixed code."
                    )
                    reviewed2 = await self._call_ai(review2_prompt)
                    panel.increment_api_calls()

                    if not reviewed2.startswith("ERROR:"):
                        code_result = reviewed2
                        await panel.complete_step(f"Task {task_num} — Upgrades verified")
                    else:
                        await panel.complete_step(f"Task {task_num} — Verify skipped (timeout)")
                    await panel.complete_sub_step("Verify")

                    # ALIGNMENT CHECK
                    await panel.add_sub_step("Align Check")
                    await panel.start_step(f"Task {task_num} — Checking alignment")

                    reread_prompt = (
                        "Compare this code against the original request.\n\n"
                        "USER WANTED: " + plan.get("original_request", "") + "\n"
                        "TASK: " + task["name"] + " - " + task["description"] + "\n\n"
                        "CODE:\n" + code_result[:3000] + "\n\n"
                        "Does this fulfill what the user asked?\n"
                        "Respond: ALIGNED: YES/NO\nMISSING: [list or 'nothing']"
                    )
                    alignment = await self._call_ai(reread_prompt)
                    panel.increment_api_calls()

                    if not alignment.startswith("ERROR:"):
                        needs_more = (
                            "ALIGNED: NO" in alignment.upper()
                            or ("MISSING:" in alignment.upper() and "MISSING: NOTHING" not in alignment.upper())
                        )

                        if needs_more:
                            await panel.complete_step(f"Task {task_num} — Misalignment detected")

                            await panel.add_sub_step("Fix Alignment")
                            await panel.start_step(f"Task {task_num} — Fixing alignment")

                            fix_prompt = (
                                "Alignment report:\n" + alignment[:1000] + "\n\n"
                                "Current code:\n" + code_result[:3000] + "\n\n"
                                "Fix missing parts. Return COMPLETE code. Start with FILENAME:"
                            )
                            fixed = await self._call_ai(fix_prompt)
                            panel.increment_api_calls()

                            if not fixed.startswith("ERROR:"):
                                code_result = fixed
                                await panel.complete_step(f"Task {task_num} — Alignment fixed")
                            else:
                                await panel.complete_step(f"Task {task_num} — Fix skipped (timeout)")
                            await panel.complete_sub_step("Fix Alignment")

                            # Final check
                            await panel.add_sub_step("Final Check")
                            await panel.start_step(f"Task {task_num} — Final verification")

                            final_prompt = "Final review. Fix any bugs:\n\n" + code_result[:3000] + "\n\nReturn COMPLETE fixed code."
                            final_result = await self._call_ai(final_prompt)
                            panel.increment_api_calls()

                            if not final_result.startswith("ERROR:"):
                                code_result = final_result
                                await panel.complete_step(f"Task {task_num} — Final check passed")
                            else:
                                await panel.complete_step(f"Task {task_num} — Final check skipped")
                            await panel.complete_sub_step("Final Check")
                        else:
                            await panel.complete_step(f"Task {task_num} — Aligned ✓")
                    else:
                        await panel.complete_step(f"Task {task_num} — Alignment skipped (timeout)")
                    await panel.complete_sub_step("Align Check")

                    await panel.set_phase("building")

                # ---- EXTRACT & STORE ----
                filename = self._extract_filename(code_result, task)
                code_content = self._extract_code_content(code_result)

                if filename in all_files:
                    import os as _os
                    base, ext = _os.path.splitext(filename)
                    filename = f"{base}_task{task['id']}{ext}"

                if code_content:
                    all_files[filename] = code_content

                task["completed"] = True
                task["result"] = code_result
                task["filename"] = filename

                task_time = round(time.time() - task_start, 1)
                lines = len(code_content.split("\n")) if code_content else 0

                panel.complete_task(task_num, lines, task_time)
                await panel.update()

            except Exception as task_error:
                print(f"[Agent] Task {task_num} error: {task_error}")
                panel.fail_task(task_num, str(task_error)[:100])
                await panel.complete_step(f"Task {task_num} — Error: {str(task_error)[:50]}")

            memory.add_message("agent", f"Done task {task['id']}: {task['name']}")
            await asyncio.sleep(0.3)

        # ========== POST-PROCESSING (super only) ==========
        if is_super and all_files:
            panel.log("")

            # Cross-file connections
            await panel.set_phase("connecting")
            await panel.start_step("Checking cross-file connections")
            conn_result = await self.connector.check_connections(all_files)
            panel.increment_api_calls()
            if not conn_result.get("connected", True) and conn_result.get("fixed_files"):
                fixes = 0
                for fname, fcode in conn_result["fixed_files"].items():
                    if fname in all_files:
                        all_files[fname] = fcode
                        fixes += 1
                await panel.complete_step(f"Fixed {fixes} connection issues")
            else:
                await panel.complete_step("All files connected properly")

            # Vulnerability scan
            await panel.set_phase("scanning")
            await panel.start_step("Scanning for vulnerabilities")
            exploit_result = await self.exploit_scanner.scan(all_files)
            panel.increment_api_calls()
            if not exploit_result.get("safe", True) and exploit_result.get("patched_files"):
                patches = 0
                for fname, fcode in exploit_result["patched_files"].items():
                    if fname in all_files:
                        all_files[fname] = fcode
                        patches += 1
                vulns = len(exploit_result.get("vulnerabilities", []))
                panel.increment_bugs_fixed(vulns)
                await panel.complete_step(f"Patched {vulns} vulnerabilities")
            else:
                await panel.complete_step("No vulnerabilities detected")

            # Setup script
            await panel.set_phase("finalizing")
            await panel.start_step("Generating setup script")
            setup_script = await self.setup_gen.generate(all_files)
            panel.increment_api_calls()
            await panel.complete_step("Setup script ready")

            # Test guide
            await panel.start_step("Generating test guide")
            test_guide = await self.test_gen.generate(plan, all_files)
            panel.increment_api_calls()
            await panel.complete_step("Test guide ready")

        # ========== PRESENT RESULTS ==========
        await panel.start_step("Preparing output")

        total_lines = sum(len(code.split("\n")) for code in all_files.values())
        total_time = round(time.time() - panel.start_time, 1)

        await panel.finish(f"Done — {len(all_files)} files, {total_lines} lines, {total_time}s")

        # Create output thread
        ts = datetime.now().strftime("%H:%M")
        thread_name = f"{mode_label} | {message.author.display_name[:15]} | {ts}"

        try:
            output_thread = await panel.message.create_thread(
                name=thread_name,
                auto_archive_duration=60
            )
        except discord.HTTPException:
            output_thread = channel

        # Summary embed
        summary_embed = discord.Embed(
            title="Build Complete",
            color=0x57F287
        )

        summary_lines = []
        summary_lines.append(f"**Request:** {plan.get('original_request', '')[:200]}")
        summary_lines.append(f"**Difficulty:** {plan.get('difficulty', '?')}")
        summary_lines.append(f"**Files:** {len(all_files)} · **Lines:** {total_lines} · **Time:** {total_time}s")
        summary_lines.append(f"**Mode:** {mode_label}")
        if panel.total_api_calls > 0:
            summary_lines.append(f"**API Calls:** {panel.total_api_calls}")
        if panel.bugs_fixed > 0:
            summary_lines.append(f"**Bugs Fixed:** {panel.bugs_fixed}")
        if plan.get("template_used"):
            summary_lines.append(f"**Template:** {plan['template_used']}")
        summary_embed.description = "\n".join(summary_lines)

        task_list = ""
        for task in tasks:
            fname = task.get("filename", "")
            lc = len(all_files.get(fname, "").split("\n")) if fname in all_files else 0
            task_list += f"`{task['id']}` {task['name']} — {lc} lines\n"
        summary_embed.add_field(name="Tasks", value=task_list, inline=False)

        await output_thread.send(embed=summary_embed)

        # ---- Send code as FILE ATTACHMENTS ----
        if all_files:
            tree = self.file_exporter.build_file_tree(all_files)
            tree_embed = discord.Embed(
                title="📁 Project Structure",
                description=f"```\n{tree}\n```",
                color=0x5865F2
            )
            file_summary = []
            for fname, fcode in all_files.items():
                line_count = len(fcode.strip().split("\n"))
                ext = fname.rsplit(".", 1)[-1] if "." in fname else "?"
                file_summary.append(f"📄 **{fname}** — `{line_count} lines` · `.{ext}`")
            tree_embed.add_field(
                name="Files",
                value="\n".join(file_summary),
                inline=False
            )
            tree_embed.set_footer(text=f"{len(all_files)} files · {total_lines} total lines")
            await output_thread.send(embed=tree_embed)
            await asyncio.sleep(0.3)

            await self.file_sender.send_files_to_thread(output_thread, all_files)

            if is_super:
                await output_thread.send("---\n**Code Breakdown**")
                for fname, fcode in all_files.items():
                    explanation = await self.explainer.explain(fname, fcode)
                    exp_text = f"**{fname}**\n{explanation}"
                    chunks = self.splitter.split_content(exp_text)
                    for chunk in chunks:
                        await output_thread.send(chunk)
                        await asyncio.sleep(0.3)

                if setup_script and "ERROR" not in setup_script:
                    setup_code = self._extract_code_content(setup_script)
                    if setup_code:
                        await self.file_sender.send_single_file(
                            output_thread,
                            "AutoSetup.lua",
                            setup_code,
                            "**Setup Script** — Run in Studio command bar"
                        )
                    await asyncio.sleep(0.3)

                if test_guide and "ERROR" not in test_guide:
                    await output_thread.send("---\n**Testing Guide**")
                    chunks = self.splitter.split_content(test_guide)
                    for chunk in chunks:
                        await output_thread.send(chunk)
                        await asyncio.sleep(0.3)
        else:
            for task in tasks:
                result = task.get("result", "No output")
                chunks = self.splitter.split_content(f"**Task {task['id']}: {task['name']}**\n{result}")
                for chunk in chunks:
                    await output_thread.send(chunk)
                    await asyncio.sleep(0.3)

        await output_thread.send("---\nProject saved. Send a message for follow-ups.")
        self.project_memory.save_project(message.author.id, plan, [])

        session["state"] = "follow_up"
        memory.add_message("agent", "Project completed and saved.")

    # ========================================================
    # TASK PROMPT BUILDER
    # ========================================================

    def _build_task_prompt(self, plan, tasks, task, complexity, template_code):
        prompt = (
            "System: " + self.personality + "\n"
            + CODE_STANDARDS + "\n"
            + complexity + "\n\n"
            "PROJECT: " + plan.get("original_request", "") + "\n"
            "SUMMARY: " + plan.get("summary", "") + "\n\n"
        )
        if template_code:
            prompt += "REFERENCE TEMPLATE:\n" + template_code + "\n\n"

        prompt += "ALL TASKS:\n"
        for t in tasks:
            st = "DONE" if t.get("completed") else ("CURRENT" if t["id"] == task["id"] else "PENDING")
            prompt += f"  [{st}] {t['id']}: {t['name']} - {t['description']}\n"

        prompt += (
            f"\nCURRENT: Task {task['id']}: {task['name']}\n"
            f"Description: {task['description']}\n\n"
            "INSTRUCTIONS:\n"
            "- Complete ONLY this task\n"
            "- Write complete working Luau code\n"
            "- Follow ALL code quality rules\n"
            "- Start with: FILENAME: YourFile.lua\n"
            "- Then complete code in a code block\n"
            "- Add error handling with pcall where needed\n"
            "- Validate all remote calls server-side"
        )
        return prompt

    # ========================================================
    # APPROVAL
    # ========================================================

    async def _handle_approval(self, message, session):
        content = message.content.strip().lower()
        plan = session["current_plan"]

        if content in ("approve", "yes", "go"):
            session["state"] = "executing"
            await self._execute_pipeline(message, session)
        elif content in ("cancel", "no"):
            session["state"] = "idle"
            session["current_plan"] = None
            await message.reply("Cancelled.")
        elif content.startswith("edit "):
            parts = content[5:].strip().split(" ", 1)
            if len(parts) == 2:
                try:
                    num = int(parts[0])
                    for t in plan["tasks"]:
                        if t["id"] == num:
                            t["description"] = parts[1]
                            await message.reply(f"Task {num} updated. Type `approve` when ready.")
                            return
                except ValueError:
                    pass
            await message.reply("Usage: `edit 2 new description`")
        elif content.startswith("add "):
            desc = content[4:].strip()
            new_id = len(plan["tasks"]) + 1
            plan["tasks"].append({
                "id": new_id, "name": f"Task {new_id}",
                "description": desc, "completed": False, "estimated_lines": 50
            })
            await message.reply(f"Task {new_id} added. Type `approve` when ready.")
        elif content.startswith("remove "):
            try:
                num = int(content[7:].strip())
                plan["tasks"] = [t for t in plan["tasks"] if t["id"] != num]
                for i, t in enumerate(plan["tasks"]):
                    t["id"] = i + 1
                await message.reply("Task removed. Type `approve` when ready.")
            except ValueError:
                await message.reply("Usage: `remove 2`")
        else:
            await message.reply("`approve` · `edit <num> <desc>` · `add <desc>` · `remove <num>` · `cancel`")

    # ========================================================
    # FOLLOW UP
    # ========================================================

    async def _handle_followup(self, message, session):
        content = message.content.strip().lower()
        memory = session["memory"]

        if content in ("review code",) or content.startswith("review this"):
            return await self._start_code_review(message, session)
        if "task" in content and any(str(i) in content for i in range(1, 20)):
            session["state"] = "idle"
            return await self._start_pipeline(message, session)
        if any(w in content for w in ["make", "create", "build", "write", "code", "script", "new"]):
            session["state"] = "idle"
            return await self._start_pipeline(message, session)

        context = memory.get_context_string()
        prompt = f"System: {self.personality}\n\nCONTEXT:\n{context}\n\nUSER: {message.content}\n\nRespond helpfully."
        response = await self._call_ai(prompt)
        memory.add_message("agent", response[:200])
        await self.splitter.send_split(message, response, reply=True)

    # ========================================================
    # PROJECTS
    # ========================================================

    async def _show_projects(self, message, user_id):
        projects = self.project_memory.get_projects(user_id)
        if not projects:
            await message.reply("No saved projects. Complete an agent task to save one.")
            return

        embed = discord.Embed(title="Saved Projects", color=0x5865F2)
        for i, p in enumerate(projects):
            task_count = len(p.get("tasks", []))
            embed.add_field(
                name=f"`{i + 1}` {p.get('original_request', '?')[:60]}",
                value=f"{p.get('difficulty', '?')} · {task_count} tasks",
                inline=False
            )
        embed.set_footer(text="load project <number>  ·  load project last")
        await message.reply(embed=embed)

    async def _load_project(self, message, user_id, content):
        try:
            parts = content.replace("load project", "").strip()
            if parts in ("last", "latest"):
                project = self.project_memory.get_latest_project(user_id)
            else:
                project = self.project_memory.get_project_by_index(user_id, int(parts) - 1)
            if not project:
                await message.reply("Project not found.")
                return
            session = self.sessions.get(user_id)
            if not session:
                return
            plan = {
                "original_request": project.get("original_request", ""),
                "difficulty": project.get("difficulty", ""),
                "summary": project.get("summary", ""),
                "tasks": project.get("tasks", []),
                "timestamp": project.get("saved_at", "")
            }
            session["current_plan"] = plan
            session["state"] = "follow_up"
            session["memory"].save_plan(plan)
            await message.reply(f"**Project loaded:** {project.get('original_request', '')[:200]}\n\nAsk follow-ups or start a new request.")
        except (ValueError, IndexError):
            await message.reply("Usage: `load project 1` or `load project last`")

    # ========================================================
    # TEMPLATES
    # ========================================================

    async def _show_templates(self, message):
        templates = self.templates.get_all_names()
        embed = discord.Embed(title="Templates", color=0x5865F2)
        for t in templates:
            embed.add_field(
                name=f"`{t['key']}` {t['name']}",
                value=t["description"],
                inline=False
            )
        embed.set_footer(text="use template <name>")
        await message.reply(embed=embed)

    async def _use_template(self, message, session, content):
        key = content.replace("use template ", "").strip()
        template = self.templates.get_template(key)
        if not template:
            results = self.templates.search(key)
            if results:
                template = results[0]["template"]
                key = results[0]["key"]
            else:
                await message.reply("Template not found. Type `templates` to see available options.")
                return
        session["state"] = "idle"
        session["memory"].add_message("user", f"Build a project using the {template['name']} template")
        await self._start_pipeline(message, session)

    # ========================================================
    # CODE REVIEW
    # ========================================================

    async def _start_code_review(self, message, session):
        session["state"] = "waiting_code_review"
        await message.reply("Paste your code and I'll review it.")

    async def _handle_code_review_input(self, message, session):
        code = message.content.strip()
        pattern = r"```(\w*)\n([\s\S]*?)```"
        match = re.search(pattern, code)
        if match:
            language = match.group(1) or "lua"
            code = match.group(2).strip()
        else:
            language = "lua"

        if len(code) < 10:
            await message.reply("Paste actual code to review.")
            return

        channel = message.channel

        # Live panel for review
        panel = LivePanel(channel, title="Code Review")
        await panel.send()

        await panel.set_phase("analyzing")
        await panel.start_step("Analyzing code structure")
        await asyncio.sleep(0.5)
        await panel.complete_step(f"Parsed {len(code.splitlines())} lines of {language}")

        await panel.set_phase("reviewing")
        await panel.start_step("Checking for bugs and vulnerabilities")
        review_data = await self.code_reviewer.review_code(code, language)
        panel.increment_api_calls()

        score = review_data.get("score", 0)
        grade = review_data.get("grade", "?")
        bugs = review_data.get("bugs", [])
        perf = review_data.get("performance", [])
        sec = review_data.get("security", [])
        improved = review_data.get("improved_code", "")

        await panel.complete_step(f"Analysis complete — {score}/100 ({grade})")
        await panel.finish(f"Score: {score}/100 ({grade})")

        # Results embed
        if score >= 70:
            color = 0x57F287
        elif score >= 40:
            color = 0xFEE75C
        else:
            color = 0xED4245

        review_embed = discord.Embed(
            title=f"Code Review — {score}/100 ({grade})",
            color=color
        )

        filled = int(score / 5)
        bar = "█" * filled + "░" * (20 - filled)
        review_embed.description = f"```\n[{bar}] {score}/100\n```"

        if bugs:
            bug_text = ""
            for b in bugs[:5]:
                severity = b.get("severity", "medium").upper()
                bug_text += f"**[{severity}]** {b.get('issue', '?')}\n"
                fix = b.get("fix", "")
                if fix:
                    bug_text += f"Fix: {fix[:100]}\n\n"
            review_embed.add_field(name=f"Bugs ({len(bugs)})", value=bug_text[:1024], inline=False)
        else:
            review_embed.add_field(name="Bugs", value="None found", inline=False)

        if perf:
            perf_text = "\n".join([f"· {p.get('issue', '?')}" for p in perf[:3]])
            review_embed.add_field(name=f"Performance ({len(perf)})", value=perf_text[:1024], inline=False)

        if sec:
            sec_text = "\n".join([f"· {s.get('issue', '?')}" for s in sec[:3]])
            review_embed.add_field(name=f"Security ({len(sec)})", value=sec_text[:1024], inline=False)

        await channel.send(embed=review_embed)

        # Send improved code as FILE ATTACHMENT
        if improved and improved != code and len(improved) > 20:
            ext = self.file_sender.EXTENSIONS.get(language, ".lua")
            await self.file_sender.send_single_file(
                channel,
                f"improved_code{ext}",
                improved,
                "**Improved version** — with fixes applied"
            )

        session["state"] = "idle"

    # ========================================================
    # EXTRACTORS
    # ========================================================

    def _extract_filename(self, result, task):
        for line in result.split("\n")[:5]:
            line_clean = line.strip()
            if line_clean.upper().startswith("FILENAME:"):
                name = line_clean.split(":", 1)[1].strip().replace("`", "").replace("*", "").strip()
                if name:
                    return name
        name = re.sub(r'[^a-zA-Z0-9_]', '', task.get("name", "Task").replace(" ", "_"))
        return name + ".lua"

    def _extract_code_content(self, result):
        pattern = r"```\w*\n([\s\S]*?)```"
        match = re.search(pattern, result)
        if match:
            return match.group(1).strip()
        lines = result.split("\n")
        code_lines = [
            l for l in lines
            if not l.strip().upper().startswith("FILENAME:")
            and not l.strip().upper().startswith("BUGS FOUND:")
        ]
        fallback = "\n".join(code_lines).strip()
        return fallback if len(fallback) > 10 else ""

    def _parse_plan(self, ai_response, original_request):
        default = {
            "difficulty": "Medium", "estimated_seconds": 30,
            "summary": original_request[:200],
            "original_request": original_request,
            "tasks": [{"id": 1, "name": "Complete Request", "description": original_request[:200], "completed": False, "estimated_lines": 50}],
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            cleaned = ai_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(cleaned[start:end])
                plan["original_request"] = original_request
                plan["timestamp"] = datetime.utcnow().isoformat()
                for t in plan.get("tasks", []):
                    t["completed"] = False
                    if "id" not in t:
                        t["id"] = plan["tasks"].index(t) + 1
                return plan
        except Exception as e:
            print(f"[Agent] Plan parse error: {e}")
        return default