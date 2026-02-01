# Development Guide - Studio Bot

## Project Structure

```
Studio-bot/
├── bot.py                    # Main bot client & core initialization
├── config.py                 # Configuration & constants
├── database.py               # MongoDB models & database operations
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore
├── start.sh                  # Bot startup script
├── README.md                 # Main documentation
└── cogs/                     # Command modules (features)
    ├── __init__.py
    ├── shop.py              # Marketplace & transaction system
    ├── profile.py           # User profiles & leaderboard
    ├── team.py              # Team creation & management
    ├── recruitment.py       # Developer discovery (/find)
    ├── economy.py           # Quests, rewards, reviews
    └── info.py              # Help & information
```

## Adding New Features

### Creating a New Cog

1. **Create a new file** in `cogs/` directory:
```python
# cogs/myfeature.py
from discord.ext import commands
from config import BOT_COLOR
import discord

class MyFeatureCog(commands.Cog):
    """Description of your feature"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="mycommand")
    async def my_command(self, ctx):
        """Command description"""
        embed = discord.Embed(
            title="My Command",
            color=BOT_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

2. **The bot automatically loads** all `.py` files from `cogs/` folder

### Command Pattern: Buttons Instead of Subcommands

This bot uses **button-based navigation** instead of subcommands (like OWO bot):

```python
# ❌ DON'T DO THIS:
/shop marketplace
/shop listings
/shop history

# ✅ DO THIS:
/shop  <- Opens main menu with buttons below
```

Example buttons view:
```python
class MyCommandView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Option 1", emoji="📋", style=discord.ButtonStyle.blurple)
    async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Do something
        embed = discord.Embed(title="Result", color=BOT_COLOR)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Option 2", emoji="⚙️", style=discord.ButtonStyle.success)
    async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Another action
        pass
```

## Database Operations

### Adding User Data

```python
from database import UserProfile

# Create user
await UserProfile.create_user(user_id, username)

# Get user
user = await UserProfile.get_user(user_id)

# Update user
await UserProfile.update_user(user_id, {"role": "Builder"})

# Add XP
await UserProfile.add_xp(user_id, 100)

# Add credits
await UserProfile.add_credits(user_id, 50)
```

### Adding Team Data

```python
from database import TeamData

# Create team
await TeamData.create_team(team_id, creator_id, team_name, project)

# Get team
team = await TeamData.get_team(team_id)

# Add member
await TeamData.add_member(team_id, user_id)

# Update milestone
await TeamData.update_milestone(team_id, milestone_name, progress)
```

### Adding Marketplace Listings

```python
from database import MarketplaceData

# List code
listing_id = await MarketplaceData.list_code(
    seller_id, title, price, code, language="Lua"
)

# Get listings
listings = await MarketplaceData.get_listings()

# Add review
await MarketplaceData.add_review(listing_id, reviewer_id, rating, comment)
```

## Configuration

Edit `config.py` to customize:

```python
# Colors
BOT_COLOR = 3092790  # Hex to decimal

# Economy
DAILY_QUEST_REWARD = 50
MARKET_COMMISSION_TAX = 0.10

# Roles & Ranks
ROLES = {
    "Builder": "🏗️",
    "Scripter": "📝",
    # Add more...
}

RANKS = {
    "Beginner": 0,
    "Learner": 1,
    # Add more...
}

# Thresholds for rank progression
RANK_THRESHOLDS = {
    "Beginner": {"months": 0, "xp": 0},
    "Learner": {"months": 1, "xp": 100},
    # Add more...
}
```

## Styling Standards

### Embeds
- Always use `color=BOT_COLOR`
- Include `embed.set_footer(text="Ashtrails' Studio Bot")`
- Use consistent field naming with emojis

```python
embed = discord.Embed(
    title="Feature Title",
    description="Brief description",
    color=BOT_COLOR
)
embed.add_field(name="🎯 Stat Name", value="Value", inline=True)
embed.set_footer(text="Ashtrails' Studio Bot")
```

### Button Styles
- Primary/Blurple: Main actions
- Success/Green: Confirmations, claims
- Secondary/Gray: Navigation, minor options
- Red: Dangerous actions (if needed)

## Event Handlers

Bot already handles:
- `on_ready()` - Bot login
- `on_member_join()` - Send welcome DM

Add more in `bot.py`:

```python
@commands.Cog.listener()
async def on_message(self, message):
    if message.author.bot:
        return
    
    # Your logic

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Handle reactions
        pass
```

## Testing

### Manual Testing
```bash
# Terminal 1: Start MongoDB
mongod

# Terminal 2: Run bot
python bot.py

# Discord: Test commands
/help
/profile
/shop
```

### Database Testing
```python
# In Python shell
python3
>>> from database import UserProfile
>>> import asyncio
>>> asyncio.run(UserProfile.create_user(123456789, "TestUser"))
```

## Performance Tips

1. **Use ephemeral messages** for responses:
   ```python
   await interaction.followup.send(embed=embed, ephemeral=True)
   ```

2. **Cache leaderboard data**:
   ```python
   # Don't query every time
   @tasks.loop(hours=1)
   async def update_leaderboard(self):
       # Cache the top 10
       pass
   ```

3. **Use pagination** for large lists:
   ```python
   class PaginationView(discord.ui.View):
       # Only show 10 items at a time
       pass
   ```

## Common Patterns

### Modal Input (for user input)
```python
class MyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Modal Title")
        self.input_field = discord.ui.TextInput(
            label="Field Name",
            placeholder="Example input"
        )
        self.add_item(self.input_field)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.input_field.value
        # Process value
```

### Select Menus
```python
class MySelectView(discord.ui.View):
    @discord.ui.select(
        placeholder="Choose an option",
        options=[
            discord.SelectOption(label="Option 1", value="opt1"),
            discord.SelectOption(label="Option 2", value="opt2"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected = select.values[0]
        # Handle selection
```

## Deployment

### Local
```bash
./start.sh
```

### Production (Example with PM2)
```bash
npm install -g pm2
pm2 start bot.py --name "studio-bot" --interpreter python3
pm2 save
pm2 startup
```

## Debugging

Enable debug logging:
```python
# bot.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs:
```bash
tail -f bot.log
```

## Contributing

When adding features:
1. Follow naming conventions (snake_case for functions)
2. Use type hints where possible
3. Document with docstrings
4. Use buttons for multi-option commands
5. Always use ephemeral for sensitive info
6. Test with multiple user scenarios
