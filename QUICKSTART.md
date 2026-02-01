# Quick Start Guide - Studio Bot

## 5-Minute Setup

### Step 1: Get Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Ashtrails Studio Bot")
4. Go to "Bot" section → Click "Add Bot"
5. Under "TOKEN" → Click "Copy"
6. Paste it in `.env` as `DISCORD_TOKEN=your_token`

### Step 2: Get Server ID (Guild ID)
1. In Discord, enable Developer Mode (Settings → Advanced → Developer Mode)
2. Right-click your server name → Copy Server ID
3. Paste it in `.env` as `GUILD_ID=your_id`

### Step 3: Invite Bot to Server
1. In Developer Portal → Bot → Scroll to OAuth2
2. Select scopes: `bot`
3. Select permissions:
   - ✓ Send Messages
   - ✓ Embed Links
   - ✓ Read Message History
   - ✓ Add Reactions
   - ✓ Use Slash Commands
   - ✓ Manage Messages (for moderation)
4. Copy generated URL and open in browser

### Step 4: Setup MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Windows: Download from https://www.mongodb.com/try/download/community

# Linux: sudo apt-get install mongodb
```

**Option B: MongoDB Cloud (Atlas)**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account → Create cluster
3. Copy connection string
4. Paste in `.env` as `MONGODB_URI=your_connection_string`

### Step 5: Run the Bot

```bash
cd /workspaces/Studio-bot

# Setup & install dependencies
pip install -r requirements.txt

# Run
python bot.py
```

Expected output:
```
✓ Loaded cog: shop
✓ Loaded cog: profile
✓ Loaded cog: team
✓ Loaded cog: recruitment
✓ Loaded cog: economy
✓ Loaded cog: info
✓ Bot logged in as StudioBot#1234
```

## Testing Commands

Once the bot is running, test in your Discord server:

```
/help              - View help menu
/profile           - View your profile
/shop              - Open marketplace
/team              - Team management
/find builder      - Find builder developers
/quest             - Daily quests
/leaderboard       - Top developers
```

## Verify Everything Works

### ✓ Bot responds to commands
- Type `/help` in Discord
- You should see an embed with buttons

### ✓ Database connected
- Run a command that saves data (e.g., `/quest`)
- Check MongoDB: `mongosh` → `use ashrails_studio`

### ✓ Profiles created
- Type `/profile` to view your auto-created profile
- Check role/rank are displayed

## Customization

### Change Bot Appearance
Edit in `config.py`:
```python
BOT_COLOR = 3092790  # Change hex color
EMBED_FOOTER = "Your Studio Name"
```

### Change Economy Values
```python
DAILY_QUEST_REWARD = 100  # More credits
MARKET_COMMISSION_TAX = 0.05  # Lower tax (5%)
```

### Add New Roles
```python
ROLES = {
    "Builder": "🏗️",
    "Your Role": "🎨",  # Add custom role
}
```

## Common Issues

### "Bot not responding"
- Check bot has permissions in channel (Server Settings → Roles → @bot)
- Verify bot is online (look for green dot)

### "MongoDB connection error"
- Make sure MongoDB is running: `mongosh`
- Check `MONGODB_URI` in `.env` is correct

### "Invalid token"
- Go back to Developer Portal and copy token again
- Make sure you copied from "Bot" section, not OAuth2

### Commands not showing up
- Restart the bot
- Discord may cache commands (wait 30 seconds)
- Check bot has `applications.commands` scope

## Next Steps

After the bot is running:

1. **Explore Features**
   - `/shop` - See marketplace system
   - `/team` - Create a team
   - `/find` - Search for developers
   - `/quest` - Complete daily tasks

2. **Customize**
   - Edit colors in `config.py`
   - Adjust economy values
   - Add your server-specific roles

3. **Expand**
   - Check `DEVELOPMENT.md` for adding features
   - Create new cogs for custom commands
   - Add event handlers for auto-leveling

4. **Deploy**
   - Run on VPS/server for 24/7
   - Use PM2 for process management
   - Setup logging

## Need Help?

Check these files:
- `README.md` - Full documentation
- `DEVELOPMENT.md` - Code structure & extending
- `cogs/` - Example implementations
- `database.py` - Database operations

Good luck building! 🚀
