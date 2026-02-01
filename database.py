import motor.motor_asyncio
from datetime import datetime
from config import MONGODB_URI, DB_NAME

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    db = client[DB_NAME]
    print("✓ MongoDB connected")
except Exception as e:
    print(f"⚠️ MongoDB not available: {e}")
    print("⚠️ Using in-memory storage (data will not persist)")
    db = None

# In-memory fallback storage
_memory_users = {}
_memory_teams = {}
_memory_marketplace = {}
_memory_transactions = {}

# Collections
if db is not None:
    users_collection = db["users"]
    teams_collection = db["teams"]
    marketplace_collection = db["marketplace"]
    transactions_collection = db["transactions"]
    leaderboard_collection = db["leaderboard"]
    quests_collection = db["quests"]
else:
    users_collection = None
    teams_collection = None
    marketplace_collection = None
    transactions_collection = None
    leaderboard_collection = None
    quests_collection = None


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
            "studio_credits": 500,  # Starting balance
            "created_at": datetime.utcnow(),
            "last_quest": None,
            "portfolio_games": [],
            "reviews_given": 0,
            "reviews_received": []
        }
        try:
            if db is not None:
                await users_collection.insert_one(user)
        except Exception as e:
            print(f"MongoDB error in create_user: {e}")
        
        # Store in memory
        _memory_users[user_id] = user
        return user
    
    @staticmethod
    async def get_user(user_id: int):
        """Get user profile"""
        try:
            if db is not None:
                return await users_collection.find_one({"_id": user_id})
        except Exception as e:
            print(f"MongoDB error in get_user: {e}")
        
        # Fallback to in-memory
        return _memory_users.get(user_id)
    
    @staticmethod
    async def update_user(user_id: int, updates: dict):
        """Update user profile"""
        try:
            if db is not None:
                await users_collection.update_one(
                    {"_id": user_id},
                    {"$set": updates}
                )
        except Exception as e:
            print(f"MongoDB error in update_user: {e}")
        
        # Update in memory
        if user_id in _memory_users:
            _memory_users[user_id].update(updates)
    
    @staticmethod
    async def add_xp(user_id: int, amount: int):
        """Add XP to user"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        new_xp = user["xp"] + amount
        level = (new_xp // 250) + 1  # Level every 250 XP
        
        try:
            if db is not None:
                await users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {"xp": new_xp, "level": level}}
                )
        except Exception as e:
            print(f"MongoDB error in add_xp: {e}")
        
        # Update in memory
        _memory_users[user_id]["xp"] = new_xp
        _memory_users[user_id]["level"] = level
    
    @staticmethod
    async def add_reputation(user_id: int, amount: int):
        """Add reputation points"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        if db is not None:
            await users_collection.update_one(
                {"_id": user_id},
                {"$inc": {"reputation": amount}}
            )
        else:
            _memory_users[user_id]["reputation"] = user.get("reputation", 0) + amount
    
    @staticmethod
    @staticmethod
    async def add_credits(user_id: int, amount: int):
        """Add studio credits"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        try:
            if db is not None:
                await users_collection.update_one(
                    {"_id": user_id},
                    {"$inc": {"studio_credits": amount}}
                )
        except Exception as e:
            print(f"MongoDB error in add_credits: {e}")
        
        # Update in memory
        _memory_users[user_id]["studio_credits"] = user.get("studio_credits", 500) + amount
    
    @staticmethod
    async def get_top_users(limit: int = 10):
        """Get leaderboard top users"""
        try:
            if db is not None:
                return await users_collection.find(
                    {},
                    {"_id": 1, "username": 1, "level": 1, "reputation": 1, "role": 1}
                ).sort("level", -1).limit(limit).to_list(limit)
        except Exception as e:
            print(f"MongoDB error in get_top_users: {e}")
        
        # Fallback to in-memory
        users = sorted(_memory_users.values(), key=lambda x: x.get("level", 0), reverse=True)[:limit]
        return users


class TeamData:
    """Team management model"""
    
    @staticmethod
    async def create_team(team_id: str, creator_id: int, team_name: str, project: str):
        """Create a new team"""
        team = {
            "_id": team_id,
            "name": team_name,
            "project": project,
            "creator_id": creator_id,
            "members": [creator_id],
            "shared_wallet": 0,
            "milestones": [],
            "progress": 0,
            "created_at": datetime.utcnow(),
        }
        try:
            if db is not None:
                await teams_collection.insert_one(team)
            else:
                _memory_teams[team_id] = team
        except Exception as e:
            print(f"MongoDB error in create_team: {e}")
            # Fallback to in-memory storage
            _memory_teams[team_id] = team
        return team
    
    @staticmethod
    async def get_team(team_id: str):
        """Get team data"""
        if db is not None:
            return await teams_collection.find_one({"_id": team_id})
        else:
            return _memory_teams.get(team_id)
    
    @staticmethod
    async def add_member(team_id: str, user_id: int):
        """Add member to team"""
        if db is not None:
            await teams_collection.update_one(
                {"_id": team_id},
                {"$push": {"members": user_id}}
            )
        else:
            if team_id in _memory_teams and user_id not in _memory_teams[team_id].get("members", []):
                _memory_teams[team_id]["members"].append(user_id)
    
    @staticmethod
    async def update_milestone(team_id: str, milestone_name: str, progress: int):
        """Update team milestone"""
        if db is not None:
            await teams_collection.update_one(
                {"_id": team_id},
                {"$set": {"progress": progress, "milestones": milestone_name}}
            )
        else:
            if team_id in _memory_teams:
                _memory_teams[team_id]["progress"] = progress
                _memory_teams[team_id]["milestones"] = milestone_name


class MarketplaceData:
    """Code marketplace model"""
    
    @staticmethod
    async def create_listing(listing):
        """Create a marketplace listing"""
        try:
            if db is not None:
                result = await marketplace_collection.insert_one(listing)
                return result.inserted_id
        except Exception as e:
            print(f"MongoDB error in create_listing: {e}")
        
        # Fallback to in-memory storage
        listing_id = listing.get('_id', len(_memory_marketplace))
        _memory_marketplace[listing_id] = listing
        return listing_id
    
    @staticmethod
    async def list_code(seller_id: int, title: str, price: int, code: str, language: str = "Lua"):
        """List code for sale"""
        listing = {
            "seller_id": seller_id,
            "title": title,
            "price": price,
            "code": code,
            "language": language,
            "rating": 0,
            "reviews": [],
            "sold": 0,
            "created_at": datetime.utcnow()
        }
        if db is not None:
            result = await marketplace_collection.insert_one(listing)
            return result.inserted_id
        else:
            listing_id = len(_memory_marketplace)
            _memory_marketplace[listing_id] = listing
            return listing_id
    
    @staticmethod
    async def get_listings(filter_role: str = None):
        """Get marketplace listings"""
        try:
            if db is not None:
                listings = await marketplace_collection.find({}).to_list(50)
                return listings
        except Exception as e:
            print(f"MongoDB error in get_listings: {e}")
        
        # Fallback to in-memory
        return list(_memory_marketplace.values())[:50]
    
    @staticmethod
    async def add_review(listing_id, reviewer_id: int, rating: int, comment: str):
        """Add review to listing"""
        if db is not None:
            await marketplace_collection.update_one(
                {"_id": listing_id},
                {
                    "$push": {
                        "reviews": {
                            "reviewer_id": reviewer_id,
                            "rating": rating,
                            "comment": comment,
                            "date": datetime.utcnow()
                        }
                    }
                }
            )
        else:
            if listing_id in _memory_marketplace:
                _memory_marketplace[listing_id]["reviews"].append({
                    "reviewer_id": reviewer_id,
                    "rating": rating,
                    "comment": comment,
                    "date": datetime.utcnow()
                })


class TransactionData:
    """Transaction/Payment tracking"""
    
    @staticmethod
    async def create_transaction(seller_id: int, buyer_id: int, amount: int, listing_id, tx_type: str):
        """Record a transaction"""
        transaction = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "listing_id": listing_id,
            "type": tx_type,  # "marketplace", "commission", "quest_reward"
            "status": "pending",  # pending, completed, disputed
            "created_at": datetime.utcnow()
        }
        if db is not None:
            await transactions_collection.insert_one(transaction)
        else:
            _memory_transactions[len(_memory_transactions)] = transaction
    
    @staticmethod
    async def get_user_transactions(user_id: int):
        """Get user's transaction history"""
        if db is not None:
            return await transactions_collection.find({
                "$or": [{"seller_id": user_id}, {"buyer_id": user_id}]
            }).to_list(20)
        else:
            user_txs = [t for t in _memory_transactions.values() 
                       if t.get("seller_id") == user_id or t.get("buyer_id") == user_id]
            return user_txs[:20]
