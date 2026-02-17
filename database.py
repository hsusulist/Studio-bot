import json
import os
import uuid
import random
import string
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

UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)


def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, type(default_val)):
                    return data
                return default_val
        except Exception:
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


def _generate_invite_code():
    """Generate a random 6-char uppercase invite code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class UserProfile:
    """User data model"""

    @staticmethod
    async def create_user(user_id: int, username: str):
        player_id = f"DEV-{str(user_id)[-6:]}-{str(uuid.uuid4())[:4].upper()}"
        user = {
            "_id": user_id,
            "username": username,
            "player_id": player_id,
            "role": None,
            "roles": [],
            "rank": "Beginner",
            "xp": 0,
            "level": 1,
            "experience_months": 0,
            "voice_minutes": 0,
            "message_count": 0,
            "reputation": 0,
            "studio_credits": 10,
            "pcredits": 0,
            "ai_credits": 0,
            "max_teams": 3,
            "max_projects": 2,
            # Premium unlocks
            "has_agent_mode": False,
            "has_super_agent": False,
            "has_premium_badge": False,
            "has_custom_color": False,
            "has_team_storage": False,
            "has_team_banner": False,
            "has_featured_listing": False,
            "custom_color": None,
            "auto_agent_switch": False,
            "temp_chat_cooldown": None,
            "created_at": datetime.utcnow().isoformat(),
            "last_quest": None,
            "last_daily": None,
            "daily_streak": 0,
            "daily_claims": 0,
            "portfolio_games": [],
            "reviews_given": 0,
            "reviews_received": [],
            "sales_count": 0,
            "purchases_count": 0,
            "claimed_quests": [],
            "seller_rating": 5.0,
            "can_sell": True,
            "duel_wins": 0,
            "duel_losses": 0,
            "duel_draws": 0,
            "duel_credits_won": 0,
            "duel_credits_lost": 0,
            "duel_streak": 0,
            "duel_best_streak": 0,
            "duel_rank": "Novice Duelist",
            "duel_title_emoji": "🥉",
            "duel_history": [],
            "duel_powerups": {
                "shield": 0,
                "extra_time": 0,
                "peek": 0,
                "sabotage": 0,
                "reroll": 0
            },
        }
        if db is not None:
            try:
                await db["users"].insert_one(user)
            except Exception:
                pass

        _memory_users[user_id] = user
        save_json(USERS_FILE, _memory_users)
        return user

    @staticmethod
    async def get_user(user_id: int):
        if db is not None:
            try:
                user = await db["users"].find_one({"_id": user_id})
                if user:
                    return user
            except Exception:
                pass
        return _memory_users.get(user_id)

    @staticmethod
    async def update_user(user_id: int, updates: dict):
        if db is not None:
            try:
                await db["users"].update_one({"_id": user_id}, {"$set": updates})
            except Exception:
                pass

        if user_id in _memory_users:
            _memory_users[user_id].update(updates)
            save_json(USERS_FILE, _memory_users)

    @staticmethod
    async def add_xp(user_id: int, amount: int):
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        new_xp = user.get("xp", 0) + amount
        level = (new_xp // 250) + 1
        await UserProfile.update_user(user_id, {"xp": new_xp, "level": level})

    @staticmethod
    async def add_credits(user_id: int, amount: int):
        user = await UserProfile.get_user(user_id)
        if not user:
            return
        new_credits = user.get("studio_credits", 0) + amount
        await UserProfile.update_user(user_id, {"studio_credits": new_credits})

    @staticmethod
    async def get_top_users(limit: int = 10):
        if db is not None:
            try:
                return await db["users"].find({}).sort("level", -1).limit(limit).to_list(limit)
            except Exception:
                pass
        users = sorted(_memory_users.values(), key=lambda x: x.get("level", 0), reverse=True)[:limit]
        return users


class TeamData:

    @staticmethod
    async def create_team(team_id: str, creator_id: int, team_name: str, project: str = "", private: bool = True):
        """Create a new team. Project is optional."""
        invite_code = _generate_invite_code()
        # Make sure invite code is unique
        for _ in range(10):
            exists = False
            for t in _memory_teams.values():
                if t.get("invite_code") == invite_code:
                    exists = True
                    break
            if not exists:
                break
            invite_code = _generate_invite_code()

        team = {
            "_id": team_id,
            "name": team_name,
            "project": project or "No project yet",
            "creator_id": creator_id,
            "members": [creator_id],
            "max_members": 5,
            "shared_wallet": 0,
            "milestones": [],
            "progress": 0,
            "private": private,
            "invite_code": invite_code,
            "category_id": None,
            "has_storage": False,
            "has_banner": False,
            "banner_color": None,
            "banner_description": None,
            "projects": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        if db is not None:
            try:
                await db["teams"].insert_one(team)
            except Exception:
                pass
        _memory_teams[team_id] = team
        save_json(TEAMS_FILE, _memory_teams)
        return team

    @staticmethod
    async def get_team(team_id: str):
        if db is not None:
            try:
                return await db["teams"].find_one({"_id": team_id})
            except Exception:
                pass
        return _memory_teams.get(team_id)

    @staticmethod
    async def update_team(team_id: str, updates: dict):
        if db is not None:
            try:
                await db["teams"].update_one({"_id": team_id}, {"$set": updates})
            except Exception:
                pass
        if team_id in _memory_teams:
            _memory_teams[team_id].update(updates)
            save_json(TEAMS_FILE, _memory_teams)

    @staticmethod
    async def delete_team(team_id: str):
        if db is not None:
            try:
                await db["teams"].delete_one({"_id": team_id})
            except Exception:
                pass
        if team_id in _memory_teams:
            del _memory_teams[team_id]
            save_json(TEAMS_FILE, _memory_teams)

    @staticmethod
    async def add_member(team_id: str, user_id: int):
        team = await TeamData.get_team(team_id)
        if not team:
            return False
        members = team.get("members", [])
        if user_id in members:
            return False
        members.append(user_id)
        await TeamData.update_team(team_id, {"members": members})
        return True

    @staticmethod
    async def remove_member(team_id: str, user_id: int):
        team = await TeamData.get_team(team_id)
        if not team:
            return False
        members = team.get("members", [])
        if user_id not in members:
            return False
        members.remove(user_id)
        await TeamData.update_team(team_id, {"members": members})
        return True

    @staticmethod
    async def get_user_teams(user_id: int):
        """Get all teams a user is a member of"""
        results = []
        if db is not None:
            try:
                cursor = db["teams"].find({"members": user_id})
                results = await cursor.to_list(100)
                if results:
                    return results
            except Exception:
                pass
        # Fallback to memory
        for team_id, team in _memory_teams.items():
            if user_id in team.get("members", []):
                results.append(team)
        return results

    @staticmethod
    async def get_all_teams():
        """Get all public teams"""
        results = []
        if db is not None:
            try:
                cursor = db["teams"].find({"private": False})
                results = await cursor.to_list(100)
                if results:
                    return results
            except Exception:
                pass
        for team_id, team in _memory_teams.items():
            if not team.get("private", True):
                results.append(team)
        return results

    @staticmethod
    async def add_project(team_id: str, project_name: str, description: str = ""):
        """Add a project to a team"""
        team = await TeamData.get_team(team_id)
        if not team:
            return False
        projects = team.get("projects", [])
        projects.append({
            "name": project_name,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        })
        await TeamData.update_team(team_id, {"projects": projects})
        return True


class MarketplaceData:
    @staticmethod
    async def create_listing(listing):
        if "listing_id" not in listing:
            listing["listing_id"] = str(uuid.uuid4())[:8].upper()
        listing["_id"] = listing["listing_id"]
        listing.setdefault("status", "active")
        listing.setdefault("sold", 0)
        listing.setdefault("rating", 0)
        listing.setdefault("ratings_count", 0)
        listing.setdefault("created_at", datetime.utcnow().isoformat())

        if db is not None:
            try:
                await db["marketplace"].insert_one(listing)
            except Exception:
                pass

        _memory_marketplace[listing["listing_id"]] = listing
        save_json(MARKETPLACE_FILE, _memory_marketplace)
        return listing["listing_id"]

    @staticmethod
    async def get_listing_by_id(listing_id: str):
        listing_id = listing_id.strip().upper()
        if db is not None:
            try:
                result = await db["marketplace"].find_one({"listing_id": listing_id})
                if result:
                    return result
                result = await db["marketplace"].find_one({"_id": listing_id})
                if result:
                    return result
            except Exception:
                pass
        if listing_id in _memory_marketplace:
            return _memory_marketplace[listing_id]
        for key, val in _memory_marketplace.items():
            if val.get("listing_id", "").upper() == listing_id:
                return val
        return None

    @staticmethod
    async def get_listings(category=None, search=None, sort_by="newest", page=1, per_page=5):
        all_listings = []
        if db is not None:
            try:
                query = {"status": "active"}
                if category:
                    query["category"] = category
                results = await db["marketplace"].find(query).to_list(500)
                all_listings = results
            except Exception:
                all_listings = list(_memory_marketplace.values())
        else:
            all_listings = list(_memory_marketplace.values())

        if not (db is not None):
            all_listings = [l for l in all_listings if l.get("status", "active") == "active"]
            if category:
                all_listings = [l for l in all_listings if l.get("category") == category]

        if search:
            search_lower = search.lower()
            filtered = []
            for l in all_listings:
                title = l.get("title", "").lower()
                desc = l.get("description", "").lower()
                if search_lower in title or search_lower in desc:
                    filtered.append(l)
            all_listings = filtered

        if sort_by == "newest":
            all_listings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "oldest":
            all_listings.sort(key=lambda x: x.get("created_at", ""))
        elif sort_by == "price_low":
            all_listings.sort(key=lambda x: x.get("price", 0))
        elif sort_by == "price_high":
            all_listings.sort(key=lambda x: x.get("price", 0), reverse=True)
        elif sort_by == "rating":
            all_listings.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_by == "best_selling":
            all_listings.sort(key=lambda x: x.get("sold", 0), reverse=True)

        total = len(all_listings)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        start = (page - 1) * per_page
        end = start + per_page
        page_listings = all_listings[start:end]

        return {
            "listings": page_listings,
            "total": total,
            "page": page,
            "total_pages": total_pages
        }

    @staticmethod
    async def get_user_listings(user_id: int):
        if db is not None:
            try:
                return await db["marketplace"].find({"seller_id": user_id}).to_list(100)
            except Exception:
                pass
        return [l for l in _memory_marketplace.values() if l.get("seller_id") == user_id]

    @staticmethod
    async def can_user_sell(user_id: int):
        user = await UserProfile.get_user(user_id)
        if not user:
            return False, "You need to create a profile first! Use `/start`"
        if not user.get("can_sell", True):
            return False, "Your selling privileges have been revoked."
        return True, "OK"

    @staticmethod
    async def increment_sold(listing_id: str):
        listing_id = listing_id.strip().upper()
        if db is not None:
            try:
                await db["marketplace"].update_one(
                    {"listing_id": listing_id},
                    {"$inc": {"sold": 1}}
                )
            except Exception:
                pass
        if listing_id in _memory_marketplace:
            _memory_marketplace[listing_id]["sold"] = _memory_marketplace[listing_id].get("sold", 0) + 1
            save_json(MARKETPLACE_FILE, _memory_marketplace)
        else:
            for key, val in _memory_marketplace.items():
                if val.get("listing_id", "").upper() == listing_id:
                    val["sold"] = val.get("sold", 0) + 1
                    save_json(MARKETPLACE_FILE, _memory_marketplace)
                    break

    @staticmethod
    async def add_rating(listing_id: str, seller_id: int, rating: int):
        listing_id = listing_id.strip().upper()
        listing = await MarketplaceData.get_listing_by_id(listing_id)
        if listing:
            current_rating = listing.get("rating", 0)
            ratings_count = listing.get("ratings_count", 0)
            if ratings_count == 0:
                new_rating = rating
            else:
                new_rating = round(((current_rating * ratings_count) + rating) / (ratings_count + 1), 1)
            new_count = ratings_count + 1

            if db is not None:
                try:
                    await db["marketplace"].update_one(
                        {"listing_id": listing_id},
                        {"$set": {"rating": new_rating, "ratings_count": new_count}}
                    )
                except Exception:
                    pass
            if listing_id in _memory_marketplace:
                _memory_marketplace[listing_id]["rating"] = new_rating
                _memory_marketplace[listing_id]["ratings_count"] = new_count
                save_json(MARKETPLACE_FILE, _memory_marketplace)
            else:
                for key, val in _memory_marketplace.items():
                    if val.get("listing_id", "").upper() == listing_id:
                        val["rating"] = new_rating
                        val["ratings_count"] = new_count
                        save_json(MARKETPLACE_FILE, _memory_marketplace)
                        break

        seller = await UserProfile.get_user(seller_id)
        if seller:
            seller_listings = await MarketplaceData.get_user_listings(seller_id)
            rated_listings = [l for l in seller_listings if l.get("ratings_count", 0) > 0]
            if rated_listings:
                avg = round(sum(l.get("rating", 0) for l in rated_listings) / len(rated_listings), 1)
                await UserProfile.update_user(seller_id, {"seller_rating": avg})


class TransactionData:
    @staticmethod
    async def create_transaction(transaction_data):
        if isinstance(transaction_data, dict):
            tx = transaction_data.copy()
            tx.setdefault("status", "completed")
            tx.setdefault("created_at", datetime.utcnow().isoformat())

            if db is not None:
                try:
                    await db["transactions"].insert_one(tx)
                except Exception:
                    pass

            tx_key = tx.get("transaction_id", str(len(_memory_transactions)))
            _memory_transactions[tx_key] = tx
            save_json(TRANSACTIONS_FILE, _memory_transactions)
            return

    @staticmethod
    async def get_user_transactions(user_id):
        if db is not None:
            try:
                return await db["transactions"].find(
                    {"$or": [{"seller_id": user_id}, {"buyer_id": user_id}]}
                ).to_list(50)
            except Exception:
                pass
        return [
            t for t in _memory_transactions.values()
            if t.get("seller_id") == user_id or t.get("buyer_id") == user_id
        ]

# ===== DUEL DATA =====
DUEL_FILE = os.path.join(DATA_DIR, "duels.json")
DUEL_CONFIG_FILE = os.path.join(DATA_DIR, "duel_config.json")
_memory_duels = load_json(DUEL_FILE, {})
_memory_duel_config = load_json(DUEL_CONFIG_FILE, {})


class DuelData:

    DUEL_RANKS = [
        {"min": 0, "rank": "Novice Duelist", "emoji": "🥉"},
        {"min": 5, "rank": "Script Fighter", "emoji": "🥈"},
        {"min": 15, "rank": "Code Warrior", "emoji": "🥇"},
        {"min": 30, "rank": "Duel Master", "emoji": "⚔️"},
        {"min": 50, "rank": "Grand Champion", "emoji": "👑"},
        {"min": 100, "rank": "Legendary Duelist", "emoji": "💎"},
        {"min": 250, "rank": "Mythic Duelist", "emoji": "🌟"},
        {"min": 500, "rank": "Godlike Duelist", "emoji": "💀"},
    ]

    STREAK_MILESTONES = [10, 30, 50, 100, 500]

    @staticmethod
    def get_rank(wins: int):
        rank_info = DuelData.DUEL_RANKS[0]
        for r in DuelData.DUEL_RANKS:
            if wins >= r["min"]:
                rank_info = r
        return rank_info

    @staticmethod
    async def record_duel(winner_id: int, loser_id: int, bet: int, mode: str = "classic", rounds_data: list = None):
        duel_id = str(uuid.uuid4())[:8].upper()
        duel = {
            "_id": duel_id,
            "winner_id": winner_id,
            "loser_id": loser_id,
            "bet": bet,
            "mode": mode,
            "rounds": rounds_data or [],
            "created_at": datetime.utcnow().isoformat()
        }

        if db is not None:
            try:
                await db["duels"].insert_one(duel)
            except Exception:
                pass

        _memory_duels[duel_id] = duel
        save_json(DUEL_FILE, _memory_duels)

        # Update winner
        winner = await UserProfile.get_user(winner_id)
        if winner:
            new_wins = winner.get("duel_wins", 0) + 1
            new_streak = winner.get("duel_streak", 0) + 1
            best_streak = max(new_streak, winner.get("duel_best_streak", 0))
            new_credits_won = winner.get("duel_credits_won", 0) + bet
            rank_info = DuelData.get_rank(new_wins)

            history = winner.get("duel_history", [])
            history.append({
                "duel_id": duel_id,
                "opponent": loser_id,
                "result": "win",
                "bet": bet,
                "mode": mode,
                "date": datetime.utcnow().isoformat()
            })
            if len(history) > 50:
                history = history[-50:]

            await UserProfile.update_user(winner_id, {
                "duel_wins": new_wins,
                "duel_streak": new_streak,
                "duel_best_streak": best_streak,
                "duel_credits_won": new_credits_won,
                "duel_rank": rank_info["rank"],
                "duel_title_emoji": rank_info["emoji"],
                "duel_history": history
            })

            return {
                "duel_id": duel_id,
                "winner_new_streak": new_streak,
                "winner_best_streak": best_streak,
                "winner_new_rank": rank_info,
                "winner_old_wins": new_wins - 1,
                "milestone_hit": new_streak in DuelData.STREAK_MILESTONES
            }

        return {"duel_id": duel_id}

    @staticmethod
    async def record_loss(loser_id: int, bet: int):
        loser = await UserProfile.get_user(loser_id)
        if loser:
            old_streak = loser.get("duel_streak", 0)
            new_losses = loser.get("duel_losses", 0) + 1
            new_credits_lost = loser.get("duel_credits_lost", 0) + bet

            history = loser.get("duel_history", [])
            history.append({
                "opponent": None,
                "result": "loss",
                "bet": bet,
                "date": datetime.utcnow().isoformat()
            })
            if len(history) > 50:
                history = history[-50:]

            await UserProfile.update_user(loser_id, {
                "duel_losses": new_losses,
                "duel_streak": 0,
                "duel_credits_lost": new_credits_lost,
                "duel_history": history
            })

            return {"old_streak": old_streak}
        return {}

    @staticmethod
    async def record_draw(user1_id: int, user2_id: int):
        for uid in [user1_id, user2_id]:
            user = await UserProfile.get_user(uid)
            if user:
                await UserProfile.update_user(uid, {
                    "duel_draws": user.get("duel_draws", 0) + 1
                })

    @staticmethod
    async def get_duel_stats(user_id: int):
        user = await UserProfile.get_user(user_id)
        if not user:
            return None
        wins = user.get("duel_wins", 0)
        losses = user.get("duel_losses", 0)
        draws = user.get("duel_draws", 0)
        total = wins + losses + draws
        win_rate = (wins / total * 100) if total > 0 else 0

        rank_info = DuelData.get_rank(wins)

        return {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "total": total,
            "win_rate": win_rate,
            "streak": user.get("duel_streak", 0),
            "best_streak": user.get("duel_best_streak", 0),
            "credits_won": user.get("duel_credits_won", 0),
            "credits_lost": user.get("duel_credits_lost", 0),
            "rank": rank_info["rank"],
            "rank_emoji": rank_info["emoji"],
            "powerups": user.get("duel_powerups", {}),
            "history": user.get("duel_history", [])
        }

    @staticmethod
    async def get_head_to_head(user1_id: int, user2_id: int):
        all_duels = []
        if db is not None:
            try:
                cursor = db["duels"].find({
                    "$or": [
                        {"winner_id": user1_id, "loser_id": user2_id},
                        {"winner_id": user2_id, "loser_id": user1_id}
                    ]
                })
                all_duels = await cursor.to_list(100)
            except Exception:
                pass

        if not all_duels:
            for d in _memory_duels.values():
                if (d.get("winner_id") == user1_id and d.get("loser_id") == user2_id) or \
                   (d.get("winner_id") == user2_id and d.get("loser_id") == user1_id):
                    all_duels.append(d)

        u1_wins = sum(1 for d in all_duels if d.get("winner_id") == user1_id)
        u2_wins = sum(1 for d in all_duels if d.get("winner_id") == user2_id)

        return {
            "total_duels": len(all_duels),
            "user1_wins": u1_wins,
            "user2_wins": u2_wins,
            "history": all_duels[-10:]
        }

    @staticmethod
    async def add_powerup(user_id: int, powerup_name: str, amount: int = 1):
        user = await UserProfile.get_user(user_id)
        if not user:
            return False
        powerups = user.get("duel_powerups", {
            "shield": 0, "extra_time": 0,
            "peek": 0, "sabotage": 0, "reroll": 0
        })
        if powerup_name not in powerups:
            return False
        powerups[powerup_name] = powerups.get(powerup_name, 0) + amount
        await UserProfile.update_user(user_id, {"duel_powerups": powerups})
        return True

    @staticmethod
    async def use_powerup(user_id: int, powerup_name: str):
        user = await UserProfile.get_user(user_id)
        if not user:
            return False
        powerups = user.get("duel_powerups", {})
        if powerups.get(powerup_name, 0) <= 0:
            return False
        powerups[powerup_name] -= 1
        await UserProfile.update_user(user_id, {"duel_powerups": powerups})
        return True

    @staticmethod
    async def get_duel_leaderboard(limit: int = 10):
        if db is not None:
            try:
                return await db["users"].find(
                    {"duel_wins": {"$gt": 0}}
                ).sort("duel_wins", -1).limit(limit).to_list(limit)
            except Exception:
                pass
        users = [u for u in _memory_users.values() if u.get("duel_wins", 0) > 0]
        users.sort(key=lambda x: x.get("duel_wins", 0), reverse=True)
        return users[:limit]

    # ===== STREAK CHANNEL CONFIG =====
    @staticmethod
    async def set_streak_channel(guild_id: int, channel_id: int):
        _memory_duel_config[str(guild_id)] = {
            "streak_channel_id": channel_id
        }
        save_json(DUEL_CONFIG_FILE, _memory_duel_config)

        if db is not None:
            try:
                await db["duel_config"].update_one(
                    {"_id": str(guild_id)},
                    {"$set": {"streak_channel_id": channel_id}},
                    upsert=True
                )
            except Exception:
                pass

    @staticmethod
    async def get_streak_channel(guild_id: int):
        if db is not None:
            try:
                config = await db["duel_config"].find_one({"_id": str(guild_id)})
                if config:
                    return config.get("streak_channel_id")
            except Exception:
                pass
        config = _memory_duel_config.get(str(guild_id), {})
        return config.get("streak_channel_id")

# Add at bottom of database.py
# After DuelData class

ACTIVE_DUELS_FILE = os.path.join(DATA_DIR, "active_duels.json")
_memory_active_duels = load_json(ACTIVE_DUELS_FILE, {})


class ActiveDuelData:

    @staticmethod
    async def create_active_duel(duel_id, p1_id, p2_id, bet, channel_id, guild_id):
        duel = {
            "_id": duel_id,
            "p1_id": p1_id,
            "p2_id": p2_id,
            "p1_name": "",
            "p2_name": "",
            "bet": bet,
            "channel_id": channel_id,
            "guild_id": guild_id,
            "mode": None,
            "status": "active",
            "spectators": [],
            "round": 0,
            "p1_score": 0,
            "p2_score": 0,
            "created_at": datetime.utcnow().isoformat()
        }

        if db is not None:
            try:
                await db["active_duels"].insert_one(duel)
            except Exception:
                pass

        _memory_active_duels[duel_id] = duel
        save_json(ACTIVE_DUELS_FILE, _memory_active_duels)
        return duel

    @staticmethod
    async def get_active_duel(duel_id):
        if db is not None:
            try:
                return await db["active_duels"].find_one({"_id": duel_id})
            except Exception:
                pass
        return _memory_active_duels.get(duel_id)

    @staticmethod
    async def update_active_duel(duel_id, updates):
        if db is not None:
            try:
                await db["active_duels"].update_one({"_id": duel_id}, {"$set": updates})
            except Exception:
                pass
        if duel_id in _memory_active_duels:
            _memory_active_duels[duel_id].update(updates)
            save_json(ACTIVE_DUELS_FILE, _memory_active_duels)

    @staticmethod
    async def delete_active_duel(duel_id):
        if db is not None:
            try:
                await db["active_duels"].delete_one({"_id": duel_id})
            except Exception:
                pass
        if duel_id in _memory_active_duels:
            del _memory_active_duels[duel_id]
            save_json(ACTIVE_DUELS_FILE, _memory_active_duels)

    @staticmethod
    async def get_all_active_duels(guild_id=None):
        duels = []
        if db is not None:
            try:
                query = {"status": "active"}
                if guild_id:
                    query["guild_id"] = guild_id
                duels = await db["active_duels"].find(query).to_list(50)
                if duels:
                    return duels
            except Exception:
                pass
        for d in _memory_active_duels.values():
            if d.get("status") == "active":
                if guild_id and d.get("guild_id") != guild_id:
                    continue
                duels.append(d)
        return duels

    @staticmethod
    async def add_spectator(duel_id, user_id):
        duel = await ActiveDuelData.get_active_duel(duel_id)
        if not duel:
            return False
        specs = duel.get("spectators", [])
        if user_id in specs:
            return False
        specs.append(user_id)
        await ActiveDuelData.update_active_duel(duel_id, {"spectators": specs})
        return True