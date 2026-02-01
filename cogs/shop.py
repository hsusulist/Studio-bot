import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile, MarketplaceData
from config import BOT_COLOR
import asyncio

class ShopView(discord.ui.View):
    """Main shop navigation with buttons"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
    
    @discord.ui.button(label="Marketplace", emoji="🛍️", style=discord.ButtonStyle.blurple)
    async def marketplace(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.show_marketplace(interaction)
    
    @discord.ui.button(label="My Listings", emoji="📦", style=discord.ButtonStyle.success)
    async def my_listings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.show_my_listings(interaction)
    
    @discord.ui.button(label="History", emoji="📜", style=discord.ButtonStyle.secondary)
    async def history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.show_history(interaction)
    
    @discord.ui.button(label="My Credits", emoji="💰", style=discord.ButtonStyle.green)
    async def credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = await UserProfile.get_user(self.user_id)
        
        # Create user if doesn't exist
        if not user:
            await UserProfile.create_user(self.user_id, interaction.user.name)
            user = await UserProfile.get_user(self.user_id)
        
        credits = user.get('studio_credits', 0) if user else 0
        
        embed = discord.Embed(
            title="Studio Credits Balance",
            description=f"**{credits} Studio Credits**",
            color=BOT_COLOR
        )
        embed.add_field(name="Lifetime Earned", value=f"{credits}", inline=False)
        embed.set_footer(text="Earn more by completing quests and selling code!")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def show_marketplace(self, interaction: discord.Interaction):
        """Show marketplace listings"""
        listings = await MarketplaceData.get_listings()
        
        if not listings:
            embed = discord.Embed(
                title="Marketplace Empty",
                description="No listings yet. Be the first to sell code!",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Show first listing with pagination
        listing = listings[0]
        embed = self._create_listing_embed(listing)
        
        view = MarketplacePaginationView(listings, 0, self.user_id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    async def show_my_listings(self, interaction: discord.Interaction):
        """Show user's own listings"""
        listings = await MarketplaceData.get_listings()
        my_listings = [l for l in listings if l.get('seller_id') == self.user_id]
        
        if not my_listings:
            embed = discord.Embed(
                title="No Listings",
                description="You haven't listed any code yet.\n\nUse `/sell` to create a listing!",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        listing = my_listings[0]
        embed = self._create_listing_embed(listing, is_own=True)
        view = MyListingsPaginationView(my_listings, 0, self.user_id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    async def show_history(self, interaction: discord.Interaction):
        """Show transaction history"""
        from database import TransactionData
        transactions = await TransactionData.get_user_transactions(self.user_id)
        
        if not transactions:
            embed = discord.Embed(
                title="No Transaction History",
                description="You haven't made any purchases or sales yet.",
                color=BOT_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Transaction History",
            color=BOT_COLOR
        )
        
        for tx in transactions[:10]:
            role = "Seller" if tx['seller_id'] == self.user_id else "Buyer"
            amount = tx['amount']
            tx_type = tx['type'].capitalize()
            embed.add_field(
                name=f"{tx_type} ({role})",
                value=f"**{amount}** Credits",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @staticmethod
    def _create_listing_embed(listing, is_own=False):
        """Create embed for a listing"""
        embed = discord.Embed(
            title=listing.get('title', 'Code Snippet'),
            description=f"**{listing.get('price')} Credits**",
            color=BOT_COLOR
        )
        embed.add_field(name="Rating", value=f"⭐ {listing.get('rating', 0)}", inline=True)
        embed.add_field(name="Sold", value=f"{listing.get('sold', 0)} times", inline=True)
        embed.add_field(name="Language", value=listing.get('language', 'Lua'), inline=True)
        
        if is_own:
            embed.add_field(name="Revenue", value=f"💰 {listing.get('sold', 0) * listing.get('price', 0)}", inline=False)
        
        return embed


class MarketplacePaginationView(discord.ui.View):
    """Pagination for marketplace listings"""
    
    def __init__(self, listings, current_page: int, user_id: int):
        super().__init__(timeout=60)
        self.listings = listings
        self.current_page = current_page
        self.user_id = user_id
        self.max_page = len(listings) - 1
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="Buy", emoji="💳", style=discord.ButtonStyle.success)
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        listing = self.listings[self.current_page]
        user = await UserProfile.get_user(self.user_id)
        
        if user['studio_credits'] < listing.get('price', 0):
            embed = discord.Embed(
                title="Insufficient Credits",
                description=f"You need **{listing.get('price')}** credits but only have **{user['studio_credits']}**",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Process payment
        from database import TransactionData
        seller_id = listing.get('seller_id')
        price = listing.get('price')
        
        await UserProfile.add_credits(self.user_id, -price)
        await UserProfile.add_credits(seller_id, price)
        await TransactionData.create_transaction(seller_id, self.user_id, price, listing.get('_id'), "marketplace")
        
        embed = discord.Embed(
            title="Purchase Complete! ✓",
            description=f"Code: `{listing.get('code', 'N/A')}`",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _update_display(self, interaction: discord.Interaction):
        listing = self.listings[self.current_page]
        embed = ShopView._create_listing_embed(listing)
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_page + 1}")
        await interaction.response.edit_message(embed=embed, view=self)


class MyListingsPaginationView(discord.ui.View):
    """Pagination for user's listings"""
    
    def __init__(self, listings, current_page: int, user_id: int):
        super().__init__(timeout=60)
        self.listings = listings
        self.current_page = current_page
        self.user_id = user_id
        self.max_page = len(listings) - 1
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await self._update_display(interaction)
    
    @discord.ui.button(label="Reviews", emoji="⭐", style=discord.ButtonStyle.blurple)
    async def reviews(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        listing = self.listings[self.current_page]
        
        embed = discord.Embed(
            title="Reviews for: " + listing.get('title', 'Code'),
            color=BOT_COLOR
        )
        
        reviews = listing.get('reviews', [])
        if not reviews:
            embed.description = "No reviews yet"
        else:
            for review in reviews[:5]:
                embed.add_field(
                    name=f"⭐ {review['rating']}/5",
                    value=f"{review['comment']}\n*-<@{review['reviewer_id']}>*",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _update_display(self, interaction: discord.Interaction):
        listing = self.listings[self.current_page]
        embed = ShopView._create_listing_embed(listing, is_own=True)
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_page + 1}")
        await interaction.response.edit_message(embed=embed, view=self)


class ShopCog(commands.Cog):
    """Shop and Marketplace Commands"""
    
    def __init__(self, bot):
        self.bot = bot

    async def shop(self, interaction: discord.Interaction):
        """Open the shop/marketplace"""
        await interaction.response.defer()
        view = ShopView(interaction.user.id)
        
        embed = discord.Embed(
            title="Ashtrails' Studio Shop",
            description="Browse code, manage listings, and track transactions.",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Features",
            value="🛍️ Marketplace\n📦 My Listings\n📜 History\n💰 Credits",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    @bot.tree.command(name="shop", description="Open the shop/marketplace")
    async def shop_cmd(interaction: discord.Interaction):
        """Open the shop/marketplace"""
        await interaction.response.defer()
        view = ShopView(interaction.user.id)
        
        embed = discord.Embed(
            title="Ashtrails' Studio Shop",
            description="Browse code, manage listings, and track transactions.",
            color=BOT_COLOR
        )
        embed.add_field(
            name="Features",
            value="🛍️ Marketplace\n📦 My Listings\n📜 History\n💰 Credits",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, view=view)
    
    await bot.add_cog(ShopCog(bot))
