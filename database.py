import motor.motor_asyncio
from datetime import datetime
from config import MONGODB_URI, DB_NAME
import json
import os
import random
import string

# ==================== JSON FILE STORAGE ====================
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TEAMS_FILE = os.path.join(DATA_DIR, "teams.json")
MARKETPLACE_FILE = os.path.join(DATA_DIR, "marketplace.json")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
QUESTS_FILE = os.path.join(DATA_DIR, "quests.json")

# Create data directory if not exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"✓ Created data directory: {DATA_DIR}")

# Create uploads directory for files
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)
    print(f"✓ Created uploads directory: {UPLOADS_DIR}")


def generate_id(prefix: str = "", length: int = 8) -> str:
    """Generate unique ID with optional prefix"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}" if prefix else random_part


def load_json(filepath: str) -> dict:
    """Load data from JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"⚠️ Error loading {filepath}: {e}")
    return {}


def save_json(filepath: str, data: dict):
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error saving {filepath}: {e}")


# Load existing data from files
_memory_users_raw = load_json(USERS_FILE)
_memory_teams = load_json(TEAMS_FILE)
_memory_marketplace = load_json(MARKETPLACE_FILE)
_memory_transactions = load_json(TRANSACTIONS_FILE)
_memory_settings = load_json(SETTINGS_FILE)
_memory_quests = load_json(QUESTS_FILE)

# Convert string keys back to int for users
_memory_users = {}
for k, v in _memory_users_raw.items():
    try:
        _memory_users[int(k)] = v
    except:
        _memory_users[k] = v

print(f"✓ Loaded {len(_memory_users)} users")
print(f"✓ Loaded {len(_memory_teams)} teams")
print(f"✓ Loaded {len(_memory_marketplace)} marketplace listings")
print(f"✓ Loaded {len(_memory_settings)} settings")


def save_users():
    save_json(USERS_FILE, _memory_users)

def save_teams():
    save_json(TEAMS_FILE, _memory_teams)

def save_marketplace():
    save_json(MARKETPLACE_FILE, _memory_marketplace)

def save_transactions():
    save_json(TRANSACTIONS_FILE, _memory_transactions)

def save_settings():
    save_json(SETTINGS_FILE, _memory_settings)

def save_quests():
    save_json(QUESTS_FILE, _memory_quests)

def save_all_data():
    save_users()
    save_teams()
    save_marketplace()
    save_transactions()
    save_settings()
    save_quests()
    print("✓ All data saved to files")


# ==================== MONGODB CONNECTION ====================
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
    print(f"⚠️ MongoDB not available: {e}")
    print("✓ Using JSON file storage (data will persist)")
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
                user = await users_collection.find_one({"_id": user_id})
                if user:
                    _memory_users[user_id] = user
                    save_users()
                    return user
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
        
        new_xp = user.get("xp", 0) + amount
        level = (new_xp // 250) + 1
        
        await UserProfile.update_user(user_id, {"xp": new_xp, "level": level})
    
    @staticmethod
    async def add_credits(user_id: int, amount: int):
        """Add studio credits"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        
        new_credits = user.get("studio_credits", 500) + amount
        await UserProfile.update_user(user_id, {"studio_credits": new_credits})
    
    @staticmethod
    async def update_seller_rating(user_id: int, new_rating: int):
        """Update seller rating and check if can still sell"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        
        total_ratings = user.get('total_ratings', 0) + 1
        current_avg = user.get('seller_rating', 5.0)
        
        # Calculate new average
        new_avg = ((current_avg * (total_ratings - 1)) + new_rating) / total_ratings
        new_avg = round(new_avg, 2)
        
        # If rating drops below 2.0, disable selling
        can_sell = new_avg >= 2.0
        
        await UserProfile.update_user(user_id, {
            "seller_rating": new_avg,
            "total_ratings": total_ratings,
            "can_sell": can_sell
        })
        
        return new_avg, can_sell
    
    @staticmethod
    async def add_purchase(user_id: int, listing_id: str):
        """Add listing to user's purchases"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        
        purchases = user.get('purchases', [])
        purchases.append({
            "listing_id": listing_id,
            "purchased_at": datetime.utcnow().isoformat()
        })
        await UserProfile.update_user(user_id, {"purchases": purchases})
    
    @staticmethod
    async def get_top_users(limit: int = 10):
        """Get leaderboard top users"""
        try:
            if db is not None:
                return await users_collection.find(
                    {},
                    {"_id": 1, "username": 1, "level": 1, "reputation": 1, "role": 1, "roles": 1, "rank": 1, "player_id": 1}
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
        
        print(f"✓ Created team {team_name} with ID: {unique_id}")
        return team
    
    @staticmethod
    async def get_team(team_id: str):
        if team_id in _memory_teams:
            return _memory_teams[team_id]
        return None
    
    @staticmethod
    async def get_team_by_unique_id(unique_id: str):
        """Get team by unique ID"""
        for team in _memory_teams.values():
            if team.get('team_id') == unique_id:
                return team
        return None
    
    @staticmethod
    async def get_user_teams(user_id: int):
        user_teams = []
        for team_id, team in _memory_teams.items():
            if user_id in team.get("members", []):
                user_teams.append(team)
        return user_teams
    
    @staticmethod
    async def get_all_teams():
        return list(_memory_teams.values())
    
    @staticmethod
    async def add_member(team_id: str, user_id: int):
        if team_id in _memory_teams:
            if user_id not in _memory_teams[team_id].get("members", []):
                _memory_teams[team_id]["members"].append(user_id)
                save_teams()
    
    @staticmethod
    async def update_team(team_id: str, updates: dict):
        if team_id in _memory_teams:
            _memory_teams[team_id].update(updates)
            save_teams()


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
    async def get_listing(listing_id: str):
        """Get a specific listing by ID"""
        if listing_id in _memory_marketplace:
            return _memory_marketplace[listing_id]
        return None
    
    @staticmethod
    async def get_listings(
        category: str = None, 
        seller_id: int = None,
        search: str = None,
        sort_by: str = "newest",  # newest, oldest, price_low, price_high, rating
        page: int = 1,
        per_page: int = 5
    ):
        """Get marketplace listings with filters, search, sort, and pagination"""
        listings = list(_memory_marketplace.values())
        
        # Filter by status (only active)
        listings = [l for l in listings if l.get('status', 'active') == 'active']
        
        # Filter by category
        if category and category in MarketplaceData.CATEGORIES:
            listings = [l for l in listings if l.get('category') == category]
        
        # Filter by seller
        if seller_id:
            listings = [l for l in listings if l.get('seller_id') == seller_id]
        
        # Search by title or description
        if search:
            search_lower = search.lower()
            listings = [l for l in listings if 
                search_lower in l.get('title', '').lower() or 
                search_lower in l.get('description', '').lower()]
        
        # Sort
        if sort_by == "newest":
            listings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == "oldest":
            listings.sort(key=lambda x: x.get('created_at', ''))
        elif sort_by == "price_low":
            listings.sort(key=lambda x: x.get('price', 0))
        elif sort_by == "price_high":
            listings.sort(key=lambda x: x.get('price', 0), reverse=True)
        elif sort_by == "rating":
            listings.sort(key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == "best_selling":
            listings.sort(key=lambda x: x.get('sold', 0), reverse=True)
        
        # Calculate pagination
        total = len(listings)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            "listings": listings[start:end],
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page
        }
    
    @staticmethod
    async def get_user_listings(user_id: int):
        """Get all listings by a user"""
        return [l for l in _memory_marketplace.values() if l.get('seller_id') == user_id]
    
    @staticmethod
    async def update_listing(listing_id: str, updates: dict):
        """Update a listing"""
        if listing_id in _memory_marketplace:
            _memory_marketplace[listing_id].update(updates)
            save_marketplace()
    
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
    async def add_review(listing_id: str, reviewer_id: int, rating: int, comment: str):
        """Add review to listing and update seller rating"""
        review_data = {
            "review_id": generate_id("R-", 6),
            "reviewer_id": reviewer_id,
            "rating": rating,
            "comment": comment,
            "date": datetime.utcnow().isoformat()
        }
        
        if listing_id in _memory_marketplace:
            listing = _memory_marketplace[listing_id]
            
            if "reviews" not in listing:
                listing["reviews"] = []
            listing["reviews"].append(review_data)
            
            # Update average rating
            total_ratings = listing.get('total_ratings', 0) + 1
            current_avg = listing.get('rating', 0)
            new_avg = ((current_avg * (total_ratings - 1)) + rating) / total_ratings
            
            listing["rating"] = round(new_avg, 1)
            listing["total_ratings"] = total_ratings
            
            save_marketplace()
            
            # Also update seller's rating
            seller_id = listing.get('seller_id')
            if seller_id:
                await UserProfile.update_seller_rating(seller_id, rating)
            
            return review_data
        
        return None
    
    @staticmethod
    async def increment_sold(listing_id: str):
        """Increment sold count"""
        if listing_id in _memory_marketplace:
            _memory_marketplace[listing_id]["sold"] = _memory_marketplace[listing_id].get("sold", 0) + 1
            save_marketplace()
    
    @staticmethod
    async def can_user_sell(user_id: int) -> tuple:
        """Check if user can sell on marketplace"""
        user = await UserProfile.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if not user.get('can_sell', True):
            rating = user.get('seller_rating', 0)
            return False, f"Your seller rating is too low ({rating}/5). Get more positive reviews to sell again."
        
        return True, "OK"


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
        
        _memory_transactions[tx_id] = transaction
        save_transactions()
        
        print(f"✓ Created transaction {tx_id}: {tx_type} - {amount} credits")
        return tx_id
    
    @staticmethod
    async def get_user_transactions(user_id: int):
        """Get user's transaction history"""
        user_txs = [t for t in _memory_transactions.values() 
                   if t.get("seller_id") == user_id or t.get("buyer_id") == user_id]
        return sorted(user_txs, key=lambda x: x.get("created_at", ""), reverse=True)[:20]


# ==================== QUEST DATA ====================
class QuestData:
    """Quest system with unique IDs"""
    
    DAILY_QUESTS = [
        {"id": "review", "name": "Review a Script", "reward": 50, "desc": "Help someone improve their code"},
        {"id": "tip", "name": "Share a Building Tip", "reward": 50, "desc": "Post helpful tips"},
        {"id": "team", "name": "Assist a Team", "reward": 100, "desc": "Contribute to a team"},
        {"id": "commission", "name": "Complete a Commission", "reward": 150, "desc": "Finish a paid project"},
    ]
    
    @staticmethod
    async def get_user_quests(user_id: int):
        """Get user's quest progress"""
        user_key = str(user_id)
        if user_key not in _memory_quests:
            _memory_quests[user_key] = {
                "completed_today": [],
                "last_reset": datetime.utcnow().date().isoformat()
            }
            save_quests()
        
        # Reset if new day
        last_reset = _memory_quests[user_key].get('last_reset', '')
        today = datetime.utcnow().date().isoformat()
        
        if last_reset != today:
            _memory_quests[user_key] = {
                "completed_today": [],
                "last_reset": today
            }
            save_quests()
        
        return _memory_quests[user_key]
    
    @staticmethod
    async def complete_quest(user_id: int, quest_id: str):
        """Mark quest as completed"""
        user_key = str(user_id)
        quests = await QuestData.get_user_quests(user_id)
        
        if quest_id not in quests.get('completed_today', []):
            quests['completed_today'].append(quest_id)
            _memory_quests[user_key] = quests
            save_quests()
            return True
        
        return False