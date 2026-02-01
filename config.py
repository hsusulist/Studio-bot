# Studio Bot - Comprehensive Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# Database
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "ashrails_studio"

# Features
PREFIX = "/"
BOT_COLOR = 3092790  # #2F2F9F (Professional Blue)
EMBED_FOOTER = "Ashtrails' Studio Bot"

# Roles
ROLES = {
    "Builder": "🏗️",
    "Scripter": "📝",
    "UI Designer": "🎨",
    "Mesh Creator": "⚙️",
    "Animator": "🎬",
    "Modeler": "🟦"
}

# Ranks
RANKS = {
    "Beginner": 0,
    "Learner": 1,
    "Expert": 2,
    "Master": 3,
}

RANK_THRESHOLDS = {
    "Beginner": {"months": 0, "xp": 0},
    "Learner": {"months": 1, "xp": 100},
    "Expert": {"months": 12, "xp": 500},
    "Master": {"months": 36, "xp": 2000}
}

# Economy
DAILY_QUEST_REWARD = 50  # Studio Credits
MARKET_COMMISSION_TAX = 0.10  # 10%
