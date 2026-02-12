import re
import asyncio
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