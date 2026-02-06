import json
import os
from datetime import datetime
from config import MONGODB_URI, DB_NAME

# File-based persistence paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TEAMS_FILE = os.path.join(DATA_DIR, "teams.json")
MARKETPLACE_FILE = os.path.join(DATA_DIR, "marketplace.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                # Ensure it's the correct type
                if isinstance(data, type(default_val)):
                    return data
                return default_val
        except:
            return default_val
    return default_val

def save_json(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4, default=str)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

# Initial Load
_memory_users = load_json(USERS_FILE, {})
_memory_teams = load_json(TEAMS_FILE, {})
_memory_marketplace = load_json(MARKETPLACE_FILE, {})
_memory_transactions = load_json(TRANSACTIONS_FILE, {})

# Convert string keys back to int for users if loaded from JSON
_memory_users = {int(k): v for k, v in _memory_users.items()}

try:
    import motor.motor_asyncio
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    db = client[DB_NAME]
    print("✓ MongoDB connected")
except Exception as e:
    print(f"⚠️ MongoDB not available: {e}")
    print("✓ Using local JSON storage (data will persist)")
    db = None

class UserProfile:
    """User data model"""
    
    @staticmethod
    async def create_user(user_id: int, username: str):
        """Create a new user profile"""
        user = {
            "_id": user_id,
            "username": username,
            "role": None,
            "rank": "Beginner",
            "xp": 0,
            "level": 1,
            "experience_months": 0,
            "voice_minutes": 0,
            "message_count": 0,
            "reputation": 0,
            "studio_credits": 500,
            "pcredits": 0,
            "ai_credits": 0,
            "max_teams": 1,
            "max_projects": 2,
            "temp_chat_cooldown": None,
            "created_at": datetime.utcnow().isoformat(),
            "last_quest": None,
            "portfolio_games": [],
            "reviews_given": 0,
            "reviews_received": []
        }
        if db is not None:
            try:
                await db["users"].insert_one(user)
            except: pass
        
        _memory_users[user_id] = user
        save_json(USERS_FILE, _memory_users)
        return user
    
    @staticmethod
    async def get_user(user_id: int):
        """Get user profile"""
        if db is not None:
            try:
                user = await db["users"].find_one({"_id": user_id})
                if user: return user
            except: pass
        return _memory_users.get(user_id)
    
    @staticmethod
    async def update_user(user_id: int, updates: dict):
        """Update user profile"""
        if db is not None:
            try:
                await db["users"].update_one({"_id": user_id}, {"$set": updates})
            except: pass
        
        if user_id in _memory_users:
            _memory_users[user_id].update(updates)
            save_json(USERS_FILE, _memory_users)
    
    @staticmethod
    async def add_xp(user_id: int, amount: int):
        user = await UserProfile.get_user(user_id)
        if not user: return
        new_xp = user.get("xp", 0) + amount
        level = (new_xp // 250) + 1
        await UserProfile.update_user(user_id, {"xp": new_xp, "level": level})

    @staticmethod
    async def add_credits(user_id: int, amount: int):
        user = await UserProfile.get_user(user_id)
        if not user: return
        new_credits = user.get("studio_credits", 500) + amount
        await UserProfile.update_user(user_id, {"studio_credits": new_credits})

    @staticmethod
    async def get_top_users(limit: int = 10):
        if db is not None:
            try:
                return await db["users"].find({}).sort("level", -1).limit(limit).to_list(limit)
            except: pass
        users = sorted(_memory_users.values(), key=lambda x: x.get("level", 0), reverse=True)[:limit]
        return users

class TeamData:
    @staticmethod
    async def create_team(team_id: str, creator_id: int, team_name: str, project: str):
        team = {
            "_id": team_id,
            "name": team_name,
            "project": project,
            "creator_id": creator_id,
            "members": [creator_id],
            "shared_wallet": 0,
            "milestones": [],
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        if db is not None:
            try: await db["teams"].insert_one(team)
            except: pass
        _memory_teams[team_id] = team
        save_json(TEAMS_FILE, _memory_teams)
        return team

    @staticmethod
    async def get_team(team_id: str):
        if db is not None:
            try: return await db["teams"].find_one({"_id": team_id})
            except: pass
        return _memory_teams.get(team_id)

class MarketplaceData:
    @staticmethod
    async def create_listing(listing):
        if "_id" not in listing:
            listing["_id"] = str(len(_memory_marketplace) + 1)
        if db is not None:
            try: await db["marketplace"].insert_one(listing)
            except: pass
        _memory_marketplace[listing["_id"]] = listing
        save_json(MARKETPLACE_FILE, _memory_marketplace)
        return listing["_id"]

    @staticmethod
    async def get_listings():
        if db is not None:
            try: return await db["marketplace"].find({}).to_list(100)
            except: pass
        return list(_memory_marketplace.values())

class TransactionData:
    @staticmethod
    async def create_transaction(seller_id, buyer_id, amount, listing_id, tx_type):
        tx = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "listing_id": listing_id,
            "type": tx_type,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        if db is not None:
            try: await db["transactions"].insert_one(tx)
            except: pass
        _memory_transactions[str(len(_memory_transactions))] = tx
        save_json(TRANSACTIONS_FILE, _memory_transactions)

    @staticmethod
    async def get_user_transactions(user_id):
        if db is not None:
            try:
                return await db["transactions"].find({"$or": [{"seller_id": user_id}, {"buyer_id": user_id}]}).to_list(50)
            except: pass
        return [t for t in _memory_transactions.values() if t.get("seller_id") == user_id or t.get("buyer_id") == user_id]
