# Ashtrails' Studio Bot - Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Discord Server                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Members    │  │   Channels   │  │  Reactions   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
└───────────────────────┬────────────────────────────────────────┘
                        │
                  Discord.py
                        │
                        ▼
            ┌───────────────────────┐
            │   Studio Bot          │
            │   (bot.py)            │
            │                       │
            │  • Core logic         │
            │  • Event handlers     │
            │  • Cog management     │
            └───────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐    ┌──────────┐    ┌─────────┐
    │ Cogs   │    │Database  │    │ Config  │
    │(6x)    │    │(database │    │(config  │
    │        │    │.py)      │    │.py)     │
    └────────┘    └──────────┘    └─────────┘
```

## Cog Module Architecture

```
                        Bot Command
                            │
            ┌───────────────┼────────────────┐
            │               │                │
            ▼               ▼                ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Embed    │   │ View     │   │ Database │
        │(UI)      │   │(Buttons) │   │(Queries) │
        └──────────┘   └──────────┘   └──────────┘
            │               │                │
            └───────────────┴────────────────┘
                            │
                        Response
                        to User
```

## Command Flow Example: /shop

```
User: /shop
  │
  ▼
bot.py → ShopCog.shop()
  │
  ▼
Create ShopView with buttons:
  │
  ├─→ [🛍️ Marketplace]  → Show marketplace listings with pagination
  ├─→ [📦 My Listings]  → Show user's own listings
  ├─→ [📜 History]      → Show transaction history
  └─→ [💰 Credits]      → Show credit balance
  │
  ▼
Database queries
  │
  ├─→ MarketplaceData.get_listings()
  ├─→ UserProfile.get_user()
  ├─→ TransactionData.get_user_transactions()
  │
  ▼
Send Embed + Buttons to User
```

## Database Schema Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                        MongoDB                              │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   USERS      │────────→│   TEAMS      │                 │
│  │              │         │              │                 │
│  │ _id: int     │         │ members[]    │                 │
│  │ role: str    │         │ creator_id   │                 │
│  │ rank: str    │         │              │                 │
│  │ xp: int      │         │ shared_wallet│                 │
│  │ credits: int │         │ progress: %  │                 │
│  │ reputation   │         │              │                 │
│  └──────────────┘         └──────────────┘                 │
│       │                                                     │
│       │                                                     │
│       ▼                        ▼                            │
│  ┌──────────────┐    ┌──────────────────┐                │
│  │MARKETPLACE   │    │  TRANSACTIONS    │                │
│  │              │    │                  │                │
│  │ seller_id────┼───→│ seller_id: int   │                │
│  │ title        │    │ buyer_id: int    │                │
│  │ price        │    │ amount: int      │                │
│  │ code         │    │ listing_id       │                │
│  │ reviews[]    │    │ status           │                │
│  │ rating       │    │ type             │                │
│  └──────────────┘    └──────────────────┘                │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

## XP & Rank Progression Flow

```
User Activity
  │
  ├─→ Message posted         → +5 XP
  ├─→ Daily quest completed  → +50 XP
  ├─→ Code reviewed          → +25 XP
  ├─→ Marketplace sale       → +100 XP
  │
  ▼
XP Total Increased
  │
  ▼
Calculate Level: level = (xp // 250) + 1
  │
  ▼
Check Rank Requirements:
  │
  ├─→ 0+ months → Beginner
  ├─→ 1+ months → Learner
  ├─→ 12+ months → Expert
  ├─→ 36+ months → Master
  │
  ▼
Update User Profile
  │
  ▼
Unlock Privileges
  │
  ├─→ Marketplace access
  ├─→ Pro-Dev channels
  ├─→ Tax reduction (15% → 5% → 0%)
  └─→ Premium features

```

## Economy System Flow

```
Earning Credits                     Spending Credits
     │                                   │
     ├─→ Daily Quest (+50-150)          ├─→ Marketplace Tax (10%)
     ├─→ Code Sales (+Variable)         ├─→ Commission Escrow (15%)
     ├─→ Tournament (+500+)             ├─→ Team Fees
     └─→ Rewards (+Variable)            └─→ Premium Features
     │                                   │
     ▼                                   ▼
User Studio Credits Balance
```

## Marketplace Transaction Flow

```
Seller                          Buyer
  │                              │
  ├─→ /sell [Title|Price|Code]   │
  │        │                     │
  │        ▼                     │
  │    MarketplaceData           │
  │    .list_code()              │
  │        │                     │
  │        └────────────┬────────────→ /shop → Browse
  │                     │             │
  │                     │             ▼
  │                     │         Review listing
  │                     │             │
  │                     │         [Buy Button]
  │                     │             │
  │                     └─────────────┼────→ Verify Credits
  │                                   │
  │                                   ▼
  │                         Credits Deducted (buyer)
  │                                   │
  │        ┌──────────────────────────┘
  │        │
  │        ▼
  │    Create Transaction
  │    .create_transaction()
  │        │
  │        ├─→ Seller: +Credits
  │        ├─→ Buyer: Code sent
  │        └─→ Record in DB
  │
  ▼
Award 100 XP to Seller
```

## Team Collaboration Flow

```
User: /team
  │
  ▼
[👥 Create] → Modal input (team name, project)
            └─→ TeamData.create_team()
            └─→ User becomes creator
  │
  ├─→ [📊 My Teams] → Show user's teams with progress
  │
  ├─→ [🔍 Browse] → Find public teams
  │       │
  │       ├─→ [👥 Members] → See team members
  │       ├─→ [📈 Progress] → View progress bar
  │       ├─→ [🎯 Milestone] → Check milestones
  │       └─→ [💰 Wallet] → Shared credits
  │
  └─→ Team collaboration features:
      │
      ├─→ Private #team-chat channel (auto-created)
      ├─→ Shared wallet (pool credits)
      ├─→ Progress tracking (0-100%)
      ├─→ Milestone system
      └─→ Member rewards
```

## User Profile Display Architecture

```
/profile [@user]
  │
  ┌─┴─┬─────────────────────────────┐
  │   │                             │
  │   ▼                             ▼
  │ UserProfile                 View Selection
  │ .get_user()                 (Buttons)
  │   │                             │
  │   ├─→ [📊 Stats]  ───────┐     │
  │   │                      │     │
  │   ├─→ [🎮 Portfolio] ──┐ │     │
  │   │                    │ │     │
  │   └─→ [👑 Rank Info]   │ │     │
  │                         │ │     │
  └─────────────────────────┼─┼─────┘
                            │ │
          ┌─────────────────┘ │
          │                   │
          ▼                   ▼
       Embed              Embed with
       Stats              Portfolio/
                         Rank Details
```

## Recruitment (/find) Flow

```
User: /find builder 2
  │
  ▼
RecruitmentCog.find()
  │
  ├─→ Filter by role: "Builder"
  │
  ├─→ Filter by experience: >= 2 years
  │
  ├─→ Get top users matching criteria
  │
  ├─→ Create pagination view
  │
  ├─→ Buttons:
  │   ├─→ [◀][▶] Navigation
  │   └─→ [💬 Contact] Send message
  │
  ▼
Display developer cards with:
  │
  ├─→ Name
  ├─→ Level
  ├─→ Reputation
  ├─→ Role
  └─→ User ID
```

## Cog Loading System

```
bot.py (setup_hook)
  │
  ├─→ Read cogs/ directory
  │
  ├─→ For each .py file:
  │   │
  │   ├─→ Load cog
  │   ├─→ Call async setup(bot)
  │   └─→ Register commands
  │
  └─→ Ready for commands
```

## Command Routing

```
User Message in Discord
  │
  ▼
check prefix = "/"
  │
  ├─ NO → ignore
  │
  YES
  ▼
Extract command name
  │
  ▼
Find matching cog
  │
  ▼
Get cog method
  │
  ▼
Execute with context
  │
  ├─→ Create embed(s)
  ├─→ Create view(s)
  ├─→ Send response
  │
  ▼
User Interaction
  │
  ├─→ Button click
  ├─→ Select choice
  ├─→ Modal submit
  │
  ▼
Button handler (in view)
  │
  ├─→ Query database if needed
  ├─→ Update profile/stats
  ├─→ Send follow-up message
  │
  ▼
Complete
```

## Error Handling Flow

```
Command Execution
  │
  ├─→ Try:
  │   │
  │   ├─→ Check user exists
  │   ├─→ Validate input
  │   ├─→ Query database
  │   ├─→ Process logic
  │   └─→ Send response
  │
  └─→ Except: (Catch errors)
      │
      ├─→ Invalid input? → Show help
      ├─→ Insufficient credits? → Error message
      ├─→ Database error? → Retry or fail gracefully
      └─→ Permission denied? → Notify user
```

## Data Flow: Complete Purchase Example

```
1. User opens /shop
   └─→ ShopView created with buttons

2. User clicks [🛍️ Marketplace]
   └─→ MarketplaceData.get_listings()
   └─→ Show first listing with pagination

3. User clicks [▶] to see next listing
   └─→ Update view with next listing

4. User clicks [💳 Buy]
   └─→ Verify buyer credits
   └─→ UserProfile.get_user(buyer_id)
   └─→ Check buyer credits >= price?
       │
       ├─ NO: Show error, stop
       │
       └─ YES: Proceed
           └─→ UserProfile.add_credits(buyer_id, -price)
           └─→ UserProfile.add_credits(seller_id, +price)
           └─→ TransactionData.create_transaction(...)
           └─→ Show success message
           └─→ Send code to buyer
           └─→ Award 100 XP to seller

5. Complete
   └─→ Transaction saved
   └─→ Credits transferred
   └─→ Both users notified
```

---

This architecture supports:
✅ Scalability (async operations)
✅ Modularity (cog-based design)
✅ Database integration (MongoDB)
✅ User interactions (buttons, modals)
✅ Error handling
✅ Feature expansion
