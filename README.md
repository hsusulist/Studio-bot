# Ashtrails' Studio Bot 🎮

A comprehensive Discord bot for managing developer communities with rankings, marketplaces, team management, and advanced economy systems.

## Features 🚀

### 1. **Intelligent Onboarding & Dynamic Profiles**
- Auto-DM welcome on join with role selection
- Interactive role buttons: Builder, Scripter, UI Designer, Mesh Creator, Animator
- Experience input system for automatic rank assignment
- Dynamic nickname formatting: `[Role | Rank] Username`

### 2. **Rank Evolution & Progression System**
- 4 Tier Ranks: Beginner → Learner → Expert → Master
- XP/Level progression system
- Activity tracking (voice, messages, reputation)
- Privilege unlocking (marketplace access, pro-dev channels, tax reduction)

### 3. **Advanced Recruitment & Teams**
- `/find [role] [min_exp]` - Search developers by expertise
- Smart team creation with project tracking
- Auto-created private channels and voice rooms
- Milestone tracking and progress visualization
- Shared team wallet for pooled resources

### 4. **Code Marketplace & Economy**
- List and sell code snippets with `/sell`
- Secure escrow system for transactions
- Rating system (1-5 stars)
- Commission support with middleman protection
- Studio Credits currency for internal economy

### 5. **High-Performance Features**
- AI-powered Lua/Luau code review with `/review`
- Portfolio web-cards with developer stats
- Leaderboard system with real-time updates
- Daily quests and reward distribution
- Market tax system for economy balance

## Tech Stack

- **Language**: Python 3.10+
- **Bot Framework**: discord.py 2.3.2
- **Database**: MongoDB (motor async driver)
- **UI**: Discord Embeds, Buttons, Select Menus, Modals

## Installation

### Prerequisites
- Python 3.10+
- MongoDB instance (local or cloud)
- Discord Bot Token

### Setup Steps

1. **Clone and Install**
```bash
cd /workspaces/Studio-bot
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` with your values:
```
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_server_id
MONGODB_URI=mongodb://localhost:27017
```

3. **Get Your Discord Bot Token**
- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Create New Application
- Go to "Bot" → "Add Bot"
- Copy the token and paste in `.env`

4. **Start MongoDB**
```bash
mongod
```

5. **Run the Bot**
```bash
python bot.py
```

## Commands

All commands use minimal naming with button-based navigation (like the OWO bot).

| Command | Description | Buttons |
|---------|-------------|---------|
| `/help` | Help menu | Getting Started, Commands, Ranks |
| `/profile` | View profiles | Stats, Portfolio, Rank Info |
| `/shop` | Marketplace hub | Marketplace, My Listings, History, Credits |
| `/find` | Find developers | Search by role/experience |
| `/team` | Team management | Create, My Teams, Browse |
| `/sell` | Sell code | Format: `/sell Title \| Price \| Language` |
| `/quest` | Daily quests | View, Claim, Stats |
| `/review` | Code review | AI analysis with feedback |
| `/card` | Portfolio card | Generate developer stats card |
| `/leaderboard` | Top developers | Weekly rankings |
| `/stats` | Server stats | Community statistics |

## Database Schema

### Users Collection
```javascript
{
  _id: user_id,
  username: string,
  role: string,
  rank: "Beginner|Learner|Expert|Master",
  xp: number,
  level: number,
  experience_months: number,
  voice_minutes: number,
  message_count: number,
  reputation: number,
  studio_credits: number,
  portfolio_games: [string],
  created_at: datetime
}
```

### Teams Collection
```javascript
{
  _id: team_id,
  name: string,
  project: string,
  creator_id: user_id,
  members: [user_id],
  shared_wallet: number,
  milestones: [string],
  progress: number,
  created_at: datetime
}
```

### Marketplace Collection
```javascript
{
  _id: ObjectId,
  seller_id: user_id,
  title: string,
  price: number,
  code: string,
  language: string,
  rating: number,
  reviews: [{reviewer_id, rating, comment, date}],
  sold: number,
  created_at: datetime
}
```

## Economy System

- **Starting Balance**: 500 Studio Credits
- **Daily Quest Reward**: 50 Credits
- **Marketplace Tax**: 10% on sales
- **Commission Escrow**: 15% held by bot
- **XP Per Activity**: 25 XP (review), 50 XP (quest), 100 XP (sell)

## User Roles & Privileges

| Rank | Months Exp | Level | Privileges |
|------|-----------|-------|-----------|
| 🥚 Beginner | 0+ | 1-10 | Basic marketplace access |
| 🌱 Learner | 1+ | 11-30 | 5% tax reduction |
| 🔥 Expert | 12+ | 31-60 | Pro-Dev channel access, 10% tax |
| 👑 Master | 36+ | 61+ | 20% tax, premium features |

## Architecture

```
cogs/
├── shop.py          # Marketplace features
├── profile.py       # User profiles & leaderboard
├── team.py          # Team management
├── recruitment.py   # Developer finding
├── economy.py       # Quests, rewards, reviews
└── info.py          # Help and information

bot.py              # Main bot client
database.py         # MongoDB models
config.py           # Configuration constants
```

## Features in Detail

### Marketplace
- Sellers list code with `/sell Title | Price | Language`
- Buyers browse with pagination
- Automatic payment processing
- Escrow protection for large transactions
- Review/rating system

### Team System
- Create teams with project names
- Auto-create private channels
- Milestone tracking
- Shared wallet for pooling resources
- Member management

### Recruitment
- Find developers by role
- Filter by minimum experience
- Contact features
- Community connections

### Daily Quests
- Review scripts (50 Credits)
- Share tips (50 Credits)
- Assist teams (100 Credits)
- Complete commissions (150 Credits)
- One per day per user

## Future Enhancements

- [ ] Real AI code analysis (Claude/GPT-4)
- [ ] DevForum news scraper
- [ ] Portfolio image generation
- [ ] Advanced commission system
- [ ] Social features (following, messaging)
- [ ] Trading/marketplace filters
- [ ] API endpoints for web dashboard

## Troubleshooting

### Bot not responding?
- Check DISCORD_TOKEN is correct
- Verify bot has permissions in channel
- Ensure MongoDB is running

### Commands not showing?
- Try syncing: `!sync` (if using slash command sync)
- Restart the bot
- Check intents are enabled

### Database errors?
- Verify MongoDB connection: `mongosh`
- Check MONGODB_URI in .env
- Ensure MongoDB service is running

## Contributing

This is a template bot for Ashtrails' Studio. Customize colors, economy values, and features in `config.py`.

## License

MIT - Feel free to modify and deploy!