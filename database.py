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

# Try MongoDB connection with better error handling
client = None
db = None

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URI, 
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000
    )
    db = client[DB_NAME]
    print("✓ MongoDB connected")
except Exception as e:
    print(f"⚠️ MongoDB connection error: {e}")
    print("⚠️ Using in-memory storage (data will not persist)")
    db = None
    client = None

# Collections
if db is not None:
    users_collection = db["users"]
    teams_collection = db["teams"]
    marketplace_collection = db["marketplace"]
    transactions_collection = db["transactions"]
    settings_collection = db["settings"]
else:
    users_collection = None
    teams_collection = None
    marketplace_collection = None
    transactions_collection = None
    settings_collection = None


# ==================== USER PROFILE ====================
class UserProfile:
    """User data model with unique ID"""
    
    @staticmethod
    async def create_user(user_id: int, username: str):
        """Create a new user profile with unique player ID"""
        # Generate unique player ID
        player_id = generate_id("P-", 6)
        
        # Make sure it's unique
        while any(u.get('player_id') == player_id for u in _memory_users.values()):
            player_id = generate_id("P-", 6)
        
        user = {
            "_id": user_id,
            "player_id": player_id,  # ✅ Unique player ID
            "username": username,
            "role": None,
            "roles": [],
            "rank": "Beginner",
            "xp": 0,
            "level": 1,
            "experience_months": 0,
            "voice_minutes": 0,
            "message_count": 0,
            "reputation": 0,
            "studio_credits": 500,
            "created_at": datetime.utcnow().isoformat(),
            "last_quest": None,
            "portfolio_games": [],
            "reviews_given": 0,
            "reviews_received": [],
            "seller_rating": 5.0,  # ✅ Seller rating (1-5)
            "total_ratings": 0,    # ✅ Number of ratings received
            "can_sell": True,      # ✅ Can sell on marketplace
            "sales_count": 0,      # ✅ Total sales
            "purchases": [],       # ✅ Purchase history
            "inventory": []
        }
        
        _memory_users[user_id] = user
        save_users()
        
        try:
            if db is not None:
                await users_collection.insert_one(user)
        except Exception as e:
            print(f"MongoDB error in create_user: {e}")
        
        print(f"✓ Created user {username} with Player ID: {player_id}")
        return user
    
    @staticmethod
    async def get_user(user_id: int):
        """Get user profile"""
        if user_id in _memory_users:
            return _memory_users[user_id]
        
        try:
            if db is not None:
                return await users_collection.find_one({"_id": user_id})
        except Exception as e:
            print(f"MongoDB error in get_user: {e}")
        
        return None
    
    @staticmethod
    async def get_user_by_player_id(player_id: str):
        """Get user by their unique player ID"""
        for user in _memory_users.values():
            if user.get('player_id') == player_id:
                return user
        return None
    
    @staticmethod
    async def update_user(user_id: int, updates: dict):
        """Update user profile"""
        if user_id not in _memory_users:
            _memory_users[user_id] = {
                "_id": user_id,
                "player_id": generate_id("P-", 6),
                "username": "Unknown",
                "role": None,
                "roles": [],
                "rank": "Beginner",
                "xp": 0,
                "level": 1,
                "experience_months": 0,
                "voice_minutes": 0,
                "message_count": 0,
                "reputation": 0,
                "studio_credits": 500,
                "created_at": datetime.utcnow().isoformat(),
                "seller_rating": 5.0,
                "total_ratings": 0,
                "can_sell": True,
                "sales_count": 0,
                "purchases": [],
                "inventory": []
            }
        
        _memory_users[user_id].update(updates)
        save_users()
        
        try:
            if db is not None:
                await users_collection.update_one(
                    {"_id": user_id},
                    {"$set": updates},
                    upsert=True
                )
        except Exception as e:
            print(f"MongoDB error in update_user: {e}")
    
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
    async def add_credits(user_id: int, amount: int):
        """Add studio credits"""
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
    async def add_purchase(user_id: int, listing_id: str):
        """Add listing to user's purchases"""
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
        
        users = sorted(_memory_users.values(), key=lambda x: x.get("level", 0), reverse=True)[:limit]
        return users


# ==================== TEAM DATA ====================
class TeamData:
    """Team management model with unique ID"""
    
    @staticmethod
    async def create_team(team_id: str, creator_id: int, team_name: str, project: str):
        """Create a new team with unique ID"""
        # Generate unique team ID
        unique_id = generate_id("T-", 6)
        
        team = {
            "_id": team_id,
            "team_id": unique_id,  # ✅ Unique team ID
            "name": team_name,
            "project": project,
            "creator_id": creator_id,
            "members": [creator_id],
            "shared_wallet": 0,
            "milestones": [],
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        _memory_teams[team_id] = team
        save_teams()
        
        try:
            if db is not None:
                await teams_collection.insert_one(team)
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


# ==================== MARKETPLACE DATA ====================
class MarketplaceData:
    """Enhanced marketplace with categories, files, and ratings"""
    
    # Listing categories
    CATEGORIES = ["code", "build", "ui"]
    
    # Minimum rating to sell
    MIN_SELLER_RATING = 2.0
    
    @staticmethod
    async def create_listing(listing: dict):
        """Create a marketplace listing with unique ID"""
        # Generate unique listing ID
        listing_id = generate_id("L-", 8)
        
        # Make sure it's unique
        while listing_id in _memory_marketplace:
            listing_id = generate_id("L-", 8)
        
        listing['_id'] = listing_id
        listing['listing_id'] = listing_id
        listing['created_at'] = datetime.utcnow().isoformat()
        listing['status'] = listing.get('status', 'active')
        listing['sold'] = listing.get('sold', 0)
        listing['reviews'] = listing.get('reviews', [])
        listing['rating'] = listing.get('rating', 0)
        listing['total_ratings'] = 0
        listing['category'] = listing.get('category', 'code')  # code, build, ui
        listing['file_path'] = listing.get('file_path', None)  # For builds/UIs
        listing['file_name'] = listing.get('file_name', None)
        
        _memory_marketplace[listing_id] = listing
        save_marketplace()
        
        print(f"✓ Created listing: {listing.get('title')} with ID: {listing_id}")
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
    async def delete_listing(listing_id: str):
        """Delete a listing"""
        if listing_id in _memory_marketplace:
            # Also delete file if exists
            listing = _memory_marketplace[listing_id]
            if listing.get('file_path') and os.path.exists(listing['file_path']):
                try:
                    os.remove(listing['file_path'])
                except:
                    pass
            
            del _memory_marketplace[listing_id]
            save_marketplace()
    
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


# ==================== TRANSACTION DATA ====================
class TransactionData:
    """Transaction/Payment tracking with unique ID"""
    
    @staticmethod
    async def create_transaction(seller_id: int, buyer_id: int, amount: int, listing_id, tx_type: str):
        """Record a transaction with unique ID"""
        tx_id = generate_id("TX-", 10)
        
        transaction = {
            "_id": tx_id,
            "transaction_id": tx_id,
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "listing_id": listing_id,
            "type": tx_type,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
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
