import re
import json
import asyncio
import os
from datetime import datetime
from ai_tools import SplitMessageTool


LUAU_TEMPLATES = {
    "inventory": {
        "name": "Inventory System",
        "description": "Complete inventory with add, remove, stack, save/load",
        "tags": ["inventory", "backpack", "items", "storage"],
        "files": {
            "InventoryModule.lua": "-- InventoryModule\nlocal InventoryModule = {}\nInventoryModule.__index = InventoryModule\nlocal MAX_SLOTS = 30\nlocal MAX_STACK = 64\nfunction InventoryModule.new(player)\n    local self = setmetatable({}, InventoryModule)\n    self.Player = player\n    self.Items = {}\n    self.MaxSlots = MAX_SLOTS\n    return self\nend\nfunction InventoryModule:AddItem(itemName, qty)\n    qty = qty or 1\n    for _, slot in ipairs(self.Items) do\n        if slot.Name == itemName and slot.Quantity < MAX_STACK then\n            local space = MAX_STACK - slot.Quantity\n            local toAdd = math.min(qty, space)\n            slot.Quantity += toAdd\n            qty -= toAdd\n            if qty <= 0 then return true end\n        end\n    end\n    if #self.Items < self.MaxSlots and qty > 0 then\n        table.insert(self.Items, {Name = itemName, Quantity = qty})\n        return true\n    end\n    return false\nend\nfunction InventoryModule:RemoveItem(itemName, qty)\n    qty = qty or 1\n    for i = #self.Items, 1, -1 do\n        local slot = self.Items[i]\n        if slot.Name == itemName then\n            if slot.Quantity <= qty then\n                qty -= slot.Quantity\n                table.remove(self.Items, i)\n            else\n                slot.Quantity -= qty\n                qty = 0\n            end\n            if qty <= 0 then return true end\n        end\n    end\n    return false\nend\nfunction InventoryModule:HasItem(itemName, qty)\n    qty = qty or 1\n    local total = 0\n    for _, slot in ipairs(self.Items) do\n        if slot.Name == itemName then total += slot.Quantity end\n    end\n    return total >= qty\nend\nfunction InventoryModule:Serialize()\n    return game:GetService('HttpService'):JSONEncode(self.Items)\nend\nfunction InventoryModule:Deserialize(data)\n    local ok, items = pcall(function() return game:GetService('HttpService'):JSONDecode(data) end)\n    if ok and type(items) == 'table' then self.Items = items end\nend\nreturn InventoryModule"
        }
    },
    "shop": {
        "name": "Shop System",
        "description": "In-game shop with categories and currency",
        "tags": ["shop", "store", "buy", "sell", "currency"],
        "files": {"ShopModule.lua": "-- Shop Module\nlocal ShopModule = {}\nlocal Items = {\n    {Id='sword', Name='Sword', Price=100},\n    {Id='shield', Name='Shield', Price=75},\n    {Id='potion', Name='Potion', Price=25}\n}\nfunction ShopModule:GetItems() return Items end\nfunction ShopModule:GetItem(id)\n    for _, item in ipairs(Items) do\n        if item.Id == id then return item end\n    end\nend\nreturn ShopModule"}
    },
    "pet": {
        "name": "Pet System",
        "description": "Pet follow, equip, inventory system",
        "tags": ["pet", "pets", "follow", "companion"],
        "files": {"PetModule.lua": "-- Pet Module\nlocal PetModule = {}\nPetModule.__index = PetModule\nfunction PetModule.new(player)\n    local self = setmetatable({}, PetModule)\n    self.Player = player\n    self.Pets = {}\n    self.Equipped = nil\n    return self\nend\nfunction PetModule:AddPet(name)\n    table.insert(self.Pets, {Name=name, Level=1})\n    return true\nend\nfunction PetModule:Equip(index)\n    self.Equipped = self.Pets[index]\n    return self.Equipped\nend\nreturn PetModule"}
    },
    "datastore": {
        "name": "DataStore System",
        "description": "Robust data saving with retry and auto-save",
        "tags": ["data", "save", "load", "datastore"],
        "files": {"DataManager.lua": "-- DataManager\nlocal DSS = game:GetService('DataStoreService')\nlocal Players = game:GetService('Players')\nlocal DataManager = {}\nDataManager.__index = DataManager\nfunction DataManager.new(storeName, defaults)\n    local self = setmetatable({}, DataManager)\n    self.Store = DSS:GetDataStore(storeName)\n    self.Defaults = defaults or {}\n    self.Cache = {}\n    return self\nend\nfunction DataManager:Load(player)\n    local key = 'Player_'..player.UserId\n    local data\n    for i = 1, 3 do\n        local ok, result = pcall(function() return self.Store:GetAsync(key) end)\n        if ok then data = result; break end\n        task.wait(1)\n    end\n    self.Cache[player.UserId] = data or self.Defaults\n    return self.Cache[player.UserId]\nend\nfunction DataManager:Save(player)\n    local data = self.Cache[player.UserId]\n    if not data then return end\n    pcall(function() self.Store:SetAsync('Player_'..player.UserId, data) end)\nend\nreturn DataManager"}
    },
    "combat": {
        "name": "Combat System",
        "description": "Combat with damage, cooldowns, knockback",
        "tags": ["combat", "fight", "damage", "pvp"],
        "files": {"CombatModule.lua": "-- Combat Module\nlocal CombatModule = {}\nlocal Cooldowns = {}\nlocal COOLDOWN = 0.5\nfunction CombatModule:CanAttack(player)\n    return (os.clock() - (Cooldowns[player.UserId] or 0)) >= COOLDOWN\nend\nfunction CombatModule:Attack(player)\n    Cooldowns[player.UserId] = os.clock()\nend\nfunction CombatModule:Damage(humanoid, amount)\n    if humanoid and humanoid.Health > 0 then\n        humanoid:TakeDamage(amount)\n        return true\n    end\n    return false\nend\nreturn CombatModule"}
    },
    "leaderboard": {
        "name": "Leaderboard System",
        "description": "Leaderstats with save/load and leveling",
        "tags": ["leaderboard", "stats", "score", "level"],
        "files": {"LeaderboardScript.lua": "-- Leaderboard\nlocal Players = game:GetService('Players')\nlocal DSS = game:GetService('DataStoreService')\nlocal Store = DSS:GetDataStore('Stats_v1')\nPlayers.PlayerAdded:Connect(function(player)\n    local ls = Instance.new('Folder')\n    ls.Name = 'leaderstats'\n    ls.Parent = player\n    local coins = Instance.new('IntValue')\n    coins.Name = 'Coins'\n    coins.Parent = ls\n    local ok, data = pcall(function() return Store:GetAsync('Stats_'..player.UserId) end)\n    if ok and data then coins.Value = data.Coins or 0 end\nend)\nPlayers.PlayerRemoving:Connect(function(player)\n    local ls = player:FindFirstChild('leaderstats')\n    if ls then\n        pcall(function() Store:SetAsync('Stats_'..player.UserId, {Coins = ls.Coins.Value}) end)\n    end\nend)"}
    }
}


class TemplateLibrary:
    def __init__(self):
        self.templates = LUAU_TEMPLATES

    def search(self, query):
        query = query.lower()
        results = []
        for key, template in self.templates.items():
            score = 0
            if query in key.lower():
                score += 10
            if query in template["name"].lower():
                score += 8
            if query in template["description"].lower():
                score += 5
            for tag in template["tags"]:
                if query in tag:
                    score += 3
            if score > 0:
                results.append({"key": key, "template": template, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_template(self, key):
        return self.templates.get(key)

    def get_all_names(self):
        return [{"key": k, "name": v["name"], "description": v["description"]} for k, v in self.templates.items()]

    def get_template_for_prompt(self, key):
        template = self.templates.get(key)
        if not template:
            return ""
        parts = ["TEMPLATE: " + template["name"], "Description: " + template["description"]]
        for filename, code in template["files"].items():
            parts.append("FILE: " + filename)
            parts.append(code[:1500])
        return "\n".join(parts)


class ProjectMemory:
    def __init__(self):
        self.save_dir = "data/projects"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save_project(self, user_id, plan, results):
        project = {
            "user_id": user_id,
            "original_request": plan.get("original_request", ""),
            "difficulty": plan.get("difficulty", "Unknown"),
            "summary": plan.get("summary", ""),
            "tasks": [],
            "saved_at": datetime.utcnow().isoformat()
        }
        for task in plan.get("tasks", []):
            project["tasks"].append({
                "id": task.get("id"),
                "name": task.get("name", ""),
                "description": task.get("description", ""),
                "completed": task.get("completed", False),
                "result": task.get("result", "")[:3000]
            })
        projects = self._load_user_projects(user_id)
        projects.append(project)
        if len(projects) > 10:
            projects = projects[-10:]
        user_file = os.path.join(self.save_dir, str(user_id) + ".json")
        try:
            with open(user_file, "w") as f:
                json.dump(projects, f, indent=2, default=str)
        except Exception as e:
            print("[ProjectMemory] Save error: " + str(e))

    def _load_user_projects(self, user_id):
        user_file = os.path.join(self.save_dir, str(user_id) + ".json")
        if not os.path.exists(user_file):
            return []
        try:
            with open(user_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def get_projects(self, user_id):
        return self._load_user_projects(user_id)

    def get_latest_project(self, user_id):
        projects = self._load_user_projects(user_id)
        return projects[-1] if projects else None

    def get_project_by_index(self, user_id, index):
        projects = self._load_user_projects(user_id)
        if 0 <= index < len(projects):
            return projects[index]
        return None


class FileTreeExporter:
    ROBLOX_LOCATIONS = {
        "Module": "ReplicatedStorage/Modules/",
        "Server": "ServerScriptService/",
        "Client": "StarterPlayerScripts/",
        "GUI": "StarterGui/",
        "Config": "ReplicatedStorage/Config/",
        "Shared": "ReplicatedStorage/Shared/",
    }

    def __init__(self):
        self.splitter = SplitMessageTool()

    def detect_file_type(self, filename, code):
        fl = filename.lower()
        cl = code.lower()
        if "module" in fl or (code.strip().startswith("local") and "return" in code[-50:]):
            return "Module"
        if "server" in fl or "onserverevent" in cl:
            return "Server"
        if "client" in fl or "localplayer" in cl:
            return "Client"
        if "gui" in fl or "screengui" in cl:
            return "GUI"
        if "config" in fl:
            return "Config"
        return "Server"

    def build_file_tree(self, files_dict):
        lines = ["```", "Project Structure", ""]
        organized = {}
        for filename, code in files_dict.items():
            ft = self.detect_file_type(filename, code)
            loc = self.ROBLOX_LOCATIONS.get(ft, "ServerScriptService/")
            if loc not in organized:
                organized[loc] = []
            organized[loc].append(filename)
        for loc in sorted(organized.keys()):
            lines.append("  " + loc)
            for f in organized[loc]:
                lines.append("    " + f)
        lines.append("```")
        return "\n".join(lines)

    async def export_to_thread(self, thread, files_dict):
        tree = self.build_file_tree(files_dict)
        await thread.send(tree)
        await asyncio.sleep(0.3)

        for filename, code in files_dict.items():
            ft = self.detect_file_type(filename, code)
            loc = self.ROBLOX_LOCATIONS.get(ft, "ServerScriptService/")
            header = "**" + filename + "**\nLocation: `" + loc + filename + "`\n"
            await thread.send(header)
            await asyncio.sleep(0.2)

            lang = "lua"
            if filename.endswith(".py"):
                lang = "python"
            elif filename.endswith(".js"):
                lang = "javascript"

            code_msg = "```" + lang + "\n" + code + "\n```"
            if len(code_msg) > 1900:
                code_lines = code.split("\n")
                current = []
                current_len = 0
                for line in code_lines:
                    if current_len + len(line) + 20 > 1900 and current:
                        await thread.send("```" + lang + "\n" + "\n".join(current) + "\n```")
                        await asyncio.sleep(0.3)
                        current = [line]
                        current_len = len(line)
                    else:
                        current.append(line)
                        current_len += len(line) + 1
                if current:
                    await thread.send("```" + lang + "\n" + "\n".join(current) + "\n```")
            else:
                await thread.send(code_msg)
            await asyncio.sleep(0.3)


class CodeReviewTool:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def review_code(self, code, language="lua"):
        prompt = (
            "You are an expert Roblox Luau code reviewer.\n\n"
            "Review this code:\n```" + language + "\n" + code + "\n```\n\n"
            "Check: bugs, performance, security, best practices.\n\n"
            "Respond in JSON (no markdown wrapping):\n"
            '{"score": 85, "grade": "B+", '
            '"bugs": [{"issue": "desc", "severity": "high/medium/low", "fix": "how"}], '
            '"performance": [{"issue": "desc", "fix": "how"}], '
            '"security": [{"issue": "desc", "fix": "how"}], '
            '"improved_code": "full improved code"}'
        )
        result = await self._call_ai(prompt)
        return self._parse_review(result, code)

    def _parse_review(self, ai_response, original):
        default = {"score": 0, "grade": "?", "bugs": [], "performance": [], "security": [], "improved_code": original}
        try:
            cleaned = ai_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
        except Exception as e:
            print("[CodeReview] Parse error: " + str(e))
        return default


class SmartCodeConnector:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def check_connections(self, files_dict):
        files_summary = ""
        for filename, code in files_dict.items():
            files_summary += "FILE: " + filename + "\n" + code[:1000] + "\n\n"

        prompt = (
            "Check if these Roblox Luau files connect properly.\n\n"
            + files_summary + "\n\n"
            "Check:\n"
            "1. Do require() paths match actual file locations?\n"
            "2. Do RemoteEvent names match between server and client?\n"
            "3. Are all referenced modules actually created?\n"
            "4. Do function signatures match between calls?\n\n"
            "Respond JSON (no markdown):\n"
            '{"connected": true/false, "issues": [{"file": "name", "issue": "desc", "fix": "how"}], '
            '"fixed_files": {"filename": "fixed code if needed"}}'
        )
        result = await self._call_ai(prompt)
        return self._parse(result)

    def _parse(self, response):
        default = {"connected": True, "issues": [], "fixed_files": {}}
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
        except Exception:
            pass
        return default


class AntiExploitScanner:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def scan(self, files_dict):
        code_summary = ""
        for filename, code in files_dict.items():
            code_summary += "FILE: " + filename + "\n" + code[:1500] + "\n\n"

        prompt = (
            "You are a Roblox security expert. Scan for exploits:\n\n"
            + code_summary + "\n\n"
            "Check:\n"
            "1. RemoteEvents without server validation\n"
            "2. Client-trusted values (damage, currency)\n"
            "3. No rate limiting on remotes\n"
            "4. Missing sanity checks\n\n"
            "Respond JSON (no markdown):\n"
            '{"safe": true/false, "vulnerabilities": [{"file": "name", "issue": "desc", "severity": "high/medium/low", "fix": "how"}], '
            '"patched_files": {"filename": "patched code"}}'
        )
        result = await self._call_ai(prompt)
        return self._parse(result)

    def _parse(self, response):
        default = {"safe": True, "vulnerabilities": [], "patched_files": {}}
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
        except Exception:
            pass
        return default


class SetupScriptGenerator:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def generate(self, files_dict):
        code_summary = ""
        for filename, code in files_dict.items():
            code_summary += "FILE: " + filename + "\n" + code[:800] + "\n\n"

        prompt = (
            "Analyze these Roblox scripts and generate a SETUP SCRIPT.\n\n"
            + code_summary + "\n\n"
            "The setup script should create all required:\n"
            "- RemoteEvents/RemoteFunctions\n"
            "- Folders in ReplicatedStorage/ServerStorage\n"
            "- Any Parts/Models referenced\n"
            "- Directory structure\n\n"
            "Output ONLY the Luau setup script. User runs it once in Studio command bar."
        )
        return await self._call_ai(prompt)


class AutoTestGenerator:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def generate(self, plan, files_dict):
        prompt = (
            "Generate step-by-step testing instructions for this Roblox project.\n\n"
            "PROJECT: " + plan.get("original_request", "") + "\n\n"
            "FILES:\n" + "\n".join(files_dict.keys()) + "\n\n"
            "Format:\n"
            "1. [Step] — What to do\n"
            "   Expected: What should happen\n"
            "   If broken: What to check\n\n"
            "Keep it simple, 5-8 steps max."
        )
        return await self._call_ai(prompt)


class LiveCodeExplainer:
    def __init__(self, genai_client, model_name):
        self.genai_client = genai_client
        self.model_name = model_name

    async def _call_ai(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content(model=self.model_name, contents=prompt)
            )
            return response.text or ""
        except Exception as e:
            return "ERROR: " + str(e)

    async def explain(self, filename, code):
        prompt = (
            "Explain this Roblox Luau script in simple terms.\n\n"
            "FILE: " + filename + "\n"
            "```lua\n" + code[:2000] + "\n```\n\n"
            "Format:\n"
            "What this file does: [1 sentence]\n"
            "Line breakdown:\n"
            "- Lines 1-X: [what they do]\n"
            "- Lines X-Y: [what they do]\n"
            "Keep it SHORT. Max 6-8 line groups."
        )
        return await self._call_ai(prompt)