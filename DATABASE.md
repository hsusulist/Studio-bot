# Database Reference Guide

## Quick Start: Database Operations

### Import & Usage

```python
from database import UserProfile, TeamData, MarketplaceData, TransactionData

# User Operations
user = await UserProfile.get_user(user_id)
await UserProfile.add_xp(user_id, 100)
await UserProfile.add_credits(user_id, 50)

# Team Operations
team = await TeamData.get_team(team_id)
await TeamData.add_member(team_id, user_id)

# Marketplace Operations
listings = await MarketplaceData.get_listings()
await MarketplaceData.add_review(listing_id, reviewer_id, 5, "Amazing code!")

# Transactions
await TransactionData.create_transaction(seller_id, buyer_id, 100, listing_id, "marketplace")
```

## UserProfile - Complete Reference

### Create User
```python
await UserProfile.create_user(user_id, username)
```
- **user_id**: Discord user ID (int)
- **username**: User's Discord name (str)

### Get User
```python
user = await UserProfile.get_user(user_id)
```
- **Returns**: User document (dict) or None

**User Document Structure**:
```python
{
    "_id": 123456789,
    "username": "john_doe",
    "role": "Builder",                    # or None if not set
    "rank": "Beginner",                   # Beginner, Learner, Expert, Master
    "xp": 250,
    "level": 2,                           # (xp // 250) + 1
    "experience_months": 0,
    "voice_minutes": 120,
    "message_count": 45,
    "reputation": 5,
    "studio_credits": 750,
    "created_at": datetime.datetime(...),
    "last_quest": None,
    "portfolio_games": ["Game 1", "Game 2"],
    "reviews_given": 3,
    "reviews_received": [
        {"reviewer_id": 111111, "rating": 5, "comment": "Good work"}
    ]
}
```

### Update User
```python
await UserProfile.update_user(user_id, {
    "role": "Scripter",
    "experience_months": 6
})
```
- **Updates**: Any fields in user document
- **Merges**: Only specified fields are updated

### Add XP
```python
await UserProfile.add_xp(user_id, 100)
```
- **Auto-calculates**: New level based on XP
- **Formula**: `level = (xp // 250) + 1`
- **Example**: 250 XP = Level 2, 500 XP = Level 3

### Add Reputation
```python
await UserProfile.add_reputation(user_id, 10)
```
- **Increments**: reputation counter
- **Used for**: Trust scoring, role filtering

### Add Credits
```python
await UserProfile.add_credits(user_id, 100)
```
- **Increments**: studio_credits balance
- **Negative values**: `await UserProfile.add_credits(user_id, -50)` for deductions

### Get Top Users (Leaderboard)
```python
top_10 = await UserProfile.get_top_users(limit=10)
```
- **Returns**: List of top users sorted by level
- **Default limit**: 10
- **Includes**: _id, username, level, reputation, role

## TeamData - Complete Reference

### Create Team
```python
await TeamData.create_team(team_id, creator_id, team_name, project)
```
- **team_id**: Unique identifier (str, usually UUID)
- **creator_id**: Discord ID of team creator (int)
- **team_name**: Team name (str)
- **project**: Project description (str)

**Example**:
```python
team_id = str(uuid.uuid4())[:8]  # "a1b2c3d4"
await TeamData.create_team(team_id, 123456789, "Swift Builders", "Combat System")
```

### Get Team
```python
team = await TeamData.get_team(team_id)
```

**Team Document**:
```python
{
    "_id": "a1b2c3d4",
    "name": "Swift Builders",
    "project": "Combat System",
    "creator_id": 123456789,
    "members": [123456789, 111111111, 222222222],
    "shared_wallet": 0,
    "milestones": ["Phase 1: Design", "Phase 2: Development"],
    "progress": 45,                        # 0-100
    "created_at": datetime.datetime(...)
}
```

### Add Member to Team
```python
await TeamData.add_member(team_id, user_id)
```
- **Adds**: user_id to members array
- **Prevents**: Duplicate checking (do it manually if needed)

### Update Milestone
```python
await TeamData.update_milestone(team_id, "v1.0 Released", 100)
```
- **milestone_name**: Current milestone (str)
- **progress**: Progress percentage 0-100 (int)

## MarketplaceData - Complete Reference

### List Code for Sale
```python
listing_id = await MarketplaceData.list_code(
    seller_id=123456789,
    title="Smooth Walking Script",
    price=75,
    code="local speed = 16",
    language="Lua"
)
```
- **Returns**: Inserted listing ID (ObjectId)

**Listing Document**:
```python
{
    "_id": ObjectId(...),
    "seller_id": 123456789,
    "title": "Smooth Walking Script",
    "price": 75,
    "code": "local speed = 16",
    "language": "Lua",
    "rating": 0,
    "reviews": [],
    "sold": 0,
    "created_at": datetime.datetime(...)
}
```

### Get Listing
```python
listings = await MarketplaceData.get_listings()
```
- **Returns**: List of all listings (max 50)

### Add Review to Listing
```python
await MarketplaceData.add_review(
    listing_id,
    reviewer_id=111111111,
    rating=5,
    comment="Exactly what I needed!"
)
```

**Review Document**:
```python
{
    "reviewer_id": 111111111,
    "rating": 5,
    "comment": "Exactly what I needed!",
    "date": datetime.datetime(...)
}
```

## TransactionData - Complete Reference

### Create Transaction
```python
await TransactionData.create_transaction(
    seller_id=123456789,
    buyer_id=111111111,
    amount=75,
    listing_id=ObjectId(...),
    tx_type="marketplace"
)
```

**Transaction Types**:
- `"marketplace"` - Marketplace purchase
- `"commission"` - Commission work
- `"quest_reward"` - Daily quest reward

**Transaction Document**:
```python
{
    "_id": ObjectId(...),
    "seller_id": 123456789,
    "buyer_id": 111111111,
    "amount": 75,
    "listing_id": ObjectId(...),
    "type": "marketplace",
    "status": "pending",              # pending, completed, disputed
    "created_at": datetime.datetime(...)
}
```

### Get User Transactions
```python
transactions = await TransactionData.get_user_transactions(user_id)
```
- **Returns**: List of transactions where user is buyer or seller
- **Max results**: 20 most recent

## Database Queries in Cogs

### Example: Give XP for Activity
```python
from database import UserProfile

class ActivityCog(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        user = await UserProfile.get_user(message.author.id)
        if not user:
            await UserProfile.create_user(message.author.id, message.author.name)
        
        # Award 5 XP per message
        await UserProfile.add_xp(message.author.id, 5)
        
        # Track message count
        current = user.get('message_count', 0)
        await UserProfile.update_user(
            message.author.id,
            {"message_count": current + 1}
        )
```

### Example: Teammate Achievement
```python
async def add_teammate(team_id, user_id, teammate_id):
    await TeamData.add_member(team_id, teammate_id)
    await UserProfile.add_reputation(teammate_id, 1)  # +1 rep for joining team
```

### Example: Complete Sale
```python
async def complete_sale(listing_id, seller_id, buyer_id, price):
    # Update credits
    await UserProfile.add_credits(buyer_id, -price)
    await UserProfile.add_credits(seller_id, price)
    
    # Record transaction
    await TransactionData.create_transaction(
        seller_id, buyer_id, price, listing_id, "marketplace"
    )
    
    # Update stats
    await UserProfile.add_xp(seller_id, 100)
    await UserProfile.add_reputation(seller_id, 1)
```

## Filtering & Searching

### Filter by Role
```python
all_users = await UserProfile.get_top_users(limit=100)
builders = [u for u in all_users if u.get('role') == 'Builder']
```

### Filter by Rank
```python
all_users = await UserProfile.get_top_users(limit=100)
experts = [u for u in all_users if u.get('rank') == 'Expert']
```

### Filter by Level Range
```python
all_users = await UserProfile.get_top_users(limit=100)
mid_level = [u for u in all_users if 15 <= u['level'] <= 40]
```

### Search Teams by Project
```python
# Current implementation: get all, filter manually
# Future: Add database index on 'project' field
all_teams = await teams_collection.find({"project": {"$regex": "combat", "$options": "i"}}).to_list(10)
```

## Best Practices

### 1. Always Check User Exists
```python
user = await UserProfile.get_user(user_id)
if not user:
    await UserProfile.create_user(user_id, username)
    user = await UserProfile.get_user(user_id)
```

### 2. Use Transactions for Financial Operations
```python
# Withdraw first
await UserProfile.add_credits(buyer_id, -100)
try:
    # Process
    await complete_purchase(...)
except Exception as e:
    # Refund if error
    await UserProfile.add_credits(buyer_id, 100)
    raise
```

### 3. Cache for Performance
```python
# For leaderboard
cached_leaderboard = None
last_update = None

@tasks.loop(minutes=30)
async def update_leaderboard():
    global cached_leaderboard
    cached_leaderboard = await UserProfile.get_top_users(10)
```

### 4. Validate Input
```python
if price < 0 or price > 10000:
    raise ValueError("Invalid price range")

if not title or len(title) > 100:
    raise ValueError("Invalid title")
```

## Advanced: Raw MongoDB Access

```python
from database import users_collection

# Direct query (use sparingly)
user = await users_collection.find_one({"_id": user_id})

# Aggregation pipeline
result = await users_collection.aggregate([
    {"$match": {"rank": "Master"}},
    {"$sort": {"reputation": -1}},
    {"$limit": 5}
]).to_list(5)
```

---

**Remember**: Always use async/await patterns. Database operations are non-blocking but async.
