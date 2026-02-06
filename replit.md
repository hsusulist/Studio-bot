# Discord Bot - Ashtrails' Studio

## Overview
A Discord bot for managing a creative studio community. Features include role selection, experience tracking, team management, economy system, and marketplace.

## Tech Stack
- Python 3.11
- discord.py 2.3.2
- MongoDB (via motor driver) for data persistence
- python-dotenv for environment management

## Required Environment Variables
The bot requires these secrets to run:
- `DISCORD_TOKEN` - Your Discord bot token from the Discord Developer Portal
- `GUILD_ID` - The Discord server (guild) ID where the bot operates
- `MONGODB_URI` (optional) - MongoDB connection string (defaults to in-memory storage if not provided)

## Project Structure
```
bot.py          - Main bot entry point
config.py       - Configuration and environment loading
database.py     - MongoDB/in-memory database operations
cogs/           - Bot command modules
  economy.py    - Economy/credits system
  info.py       - Info commands
  profile.py    - User profile commands
  recruitment.py - Recruitment features
  shop.py       - Shop commands
  team.py       - Team management
```

## Running the Bot
The bot runs via the "Discord Bot" workflow which executes `python bot.py`.

## Features
- Role-based member onboarding (Builder, Scripter, UI Designer, etc.)
- Experience tracking with rank progression
- Voice and message activity tracking
- Team management system
- Virtual economy with Studio Credits
- Marketplace for code/assets
