import discord
from discord.ext import commands
from database import UserProfile
from config import BOT_COLOR


class ItemListView(discord.ui.View):
    """Pagination and filter view like OWO"""
    
    def __init__(self, items, current_page=0):
        super().__init__(timeout=None)
        self.items = items
        self.current_page = current_page
        self.max_page = max(0, (len(items) - 1) // 5)
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_display(interaction)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await self.update_display(interaction)
    
    @discord.ui.select(placeholder="Type filter...", 
                       options=[discord.SelectOption(label="All", value="all"),
                               discord.SelectOption(label="Builder", value="builder")])
    async def type_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
    
    @discord.ui.select(placeholder="Filter by...",
                       options=[discord.SelectOption(label="Recent", value="recent"),
                               discord.SelectOption(label="Popular", value="popular")])
    async def sort_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
    
    async def update_display(self, interaction: discord.Interaction):
        start = self.current_page * 5
        end = start + 5
        page_items = self.items[start:end]
        
        embed = discord.Embed(
            title="📊 Items List",
            description=f"Page {self.current_page + 1}/{self.max_page + 1}",
            color=BOT_COLOR
        )
        
        for item in page_items:
            embed.add_field(name=item['name'], value=item['value'], inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)


class SimpleMenu(commands.Cog):
    """Simple menu with all features"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def start(self, ctx):
        """Main menu with pagination like OWO"""
        # Mock items for demo
        items = [
            {"name": "📛 Unique Item", "value": "Rarity item 1"},
            {"name": "🔥 Fire Staff", "value": "Weapon item 2"},
            {"name": "💎 Diamond Sword", "value": "Weapon item 3"},
            {"name": "⚔️ Battle Axe", "value": "Weapon item 4"},
            {"name": "🛡️ Shield", "value": "Armor item 5"},
            {"name": "👑 Crown", "value": "Armor item 6"},
            {"name": "💰 Gold Coin", "value": "Currency item 7"},
        ]
        
        view = ItemListView(items)
        
        embed = discord.Embed(
            title="⭐ Ashtrails' Studio",
            description="Page 1/2 | Sorting by rarity",
            color=BOT_COLOR
        )
        
        for i in range(5):
            item = items[i]
            embed.add_field(name=item['name'], value=item['value'], inline=False)
        
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(SimpleMenu(bot))
