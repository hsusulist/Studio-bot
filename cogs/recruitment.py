import discord
from discord.ext import commands
from discord import app_commands
from database import UserProfile
from config import BOT_COLOR, ROLES
import random


class RoleFilterView(discord.ui.View):
    """Role filter buttons for find command"""

    def __init__(self, all_users, author_id: int):
        super().__init__(timeout=120)
        self.all_users = all_users
        self.author_id = author_id

        for role_name in ROLES.keys():
            self.add_item(RoleFilterButton(role_name, self.all_users, self.author_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Only the command user can interact with this.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        pass

    @discord.ui.button(label="All Roles", emoji="🔍", style=discord.ButtonStyle.blurple, row=4)
    async def all_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.all_users:
            embed = discord.Embed(
                title="<:empty:0000> No Developers Found",
                description="No developers available at the moment.",
                color=discord.Color.from_rgb(255, 85, 85)
            )
            embed.set_footer(text="Try again later!")
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Shuffle for variety each time
        shuffled = list(self.all_users)
        random.shuffle(shuffled)

        user = shuffled[0]
        embed = self._build_user_embed(user, 0, len(shuffled))

        view = FindResultsView(shuffled, 0, self.all_users, self.author_id, filter_label="All Roles")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Random Pick", emoji="🎲", style=discord.ButtonStyle.green, row=4)
    async def random_pick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.all_users:
            await interaction.response.send_message("No developers found.", ephemeral=True)
            return

        user = random.choice(self.all_users)
        embed = self._build_user_embed(user, 0, 1)
        embed.title = f"🎲 Random Developer: {user.get('username', 'Unknown')}"

        view = RandomResultView(self.all_users, user, self.author_id)
        await interaction.response.edit_message(embed=embed, view=view)

    def _build_user_embed(self, user, index, total):
        roles = user.get('roles', [])
        role_display = " ".join(f"{ROLES.get(r, '❓')} `{r}`" for r in roles) if roles else "`No roles set`"

        level = user.get('level', 1)
        rank = user.get('rank', 'Unranked')
        reputation = user.get('reputation', 0)

        # Progress bar for level
        progress = min(level / 50, 1.0)
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title=f"{user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(
            name="📊 Stats",
            value=f"```\nLevel: {level} [{bar}]\nRank:  {rank}\n```",
            inline=False
        )
        embed.add_field(name="⭐ Reputation", value=f"**{reputation}**", inline=True)
        embed.add_field(name="🏷️ Roles", value=role_display, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user['_id']}`", inline=False)
        embed.set_footer(text=f"Result {index + 1} of {total} • Use arrows to browse")

        return embed


class RandomResultView(discord.ui.View):
    """View for random pick results"""

    def __init__(self, all_users, current_user, author_id: int):
        super().__init__(timeout=120)
        self.all_users = all_users
        self.current_user = current_user
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Only the command user can interact with this.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Reroll", emoji="🎲", style=discord.ButtonStyle.green)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = random.choice(self.all_users)
        self.current_user = user

        roles = user.get('roles', [])
        role_display = " ".join(f"{ROLES.get(r, '❓')} `{r}`" for r in roles) if roles else "`No roles set`"

        level = user.get('level', 1)
        progress = min(level / 50, 1.0)
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title=f"🎲 Random Developer: {user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(
            name="📊 Stats",
            value=f"```\nLevel: {level} [{bar}]\nRank:  {user.get('rank', 'Unranked')}\n```",
            inline=False
        )
        embed.add_field(name="⭐ Reputation", value=f"**{user.get('reputation', 0)}**", inline=True)
        embed.add_field(name="🏷️ Roles", value=role_display, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user['_id']}`", inline=False)
        embed.set_footer(text="🎲 Reroll for another random developer!")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="DM Developer", emoji="💬", style=discord.ButtonStyle.success)
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_dm(interaction, self.current_user)

    @discord.ui.button(label="Back to Filters", emoji="🔙", style=discord.ButtonStyle.blurple)
    async def back_to_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔎 Find Developers",
            description=(
                "Browse talented developers by their roles.\n"
                "Select a role below to filter, or use **All Roles** to see everyone.\n\n"
                f"📋 **{len(self.all_users)}** developers available"
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Tip: Use 🎲 Random Pick for a surprise!")
        view = RoleFilterView(self.all_users, self.author_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def _send_dm(self, interaction: discord.Interaction, user_data: dict):
        await interaction.response.defer(ephemeral=True)
        developer_id = user_data['_id']

        if developer_id == interaction.user.id:
            embed = discord.Embed(
                title="🤔 That's you!",
                description="You can't send a recruitment DM to yourself.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            developer = await interaction.client.fetch_user(developer_id)

            embed = discord.Embed(
                title="📨 Someone is interested in your profile!",
                description=(
                    f"**{interaction.user.name}** (`{interaction.user.id}`) "
                    f"found your profile and wants to connect!"
                ),
                color=discord.Color.blue()
            )
            embed.add_field(
                name="👤 From",
                value=f"{interaction.user.mention}\n`{interaction.user.name}`",
                inline=True
            )
            if interaction.guild:
                embed.add_field(
                    name="🏠 Server",
                    value=interaction.guild.name,
                    inline=True
                )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="Reply to this user to start a conversation!")
            embed.timestamp = discord.utils.utcnow()

            await developer.send(embed=embed)

            confirm = discord.Embed(
                title="✅ Message Sent!",
                description=f"Your interest has been sent to **{developer.name}**.\nThey'll reach out if interested!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=confirm, ephemeral=True)
        except discord.Forbidden:
            error = discord.Embed(
                title="❌ DMs Disabled",
                description=f"**{user_data.get('username', 'This user')}** has their DMs closed.\nTry reaching out in the server instead.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)
        except discord.NotFound:
            error = discord.Embed(
                title="❌ User Not Found",
                description="This user no longer exists or left the platform.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)
        except Exception:
            error = discord.Embed(
                title="❌ Something Went Wrong",
                description="Could not send the message. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)


class RoleFilterButton(discord.ui.Button):
    """Individual role filter button"""

    def __init__(self, role_name: str, all_users, author_id: int):
        emoji = ROLES.get(role_name, "❓")
        super().__init__(label=role_name, emoji=emoji, style=discord.ButtonStyle.secondary)
        self.role_name = role_name
        self.all_users = all_users
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        filtered = [u for u in self.all_users if self.role_name in u.get('roles', [])]

        if not filtered:
            embed = discord.Embed(
                title=f"{ROLES.get(self.role_name, '❓')} No {self.role_name}s Found",
                description=f"No developers with the **{self.role_name}** role were found.\nTry a different role!",
                color=discord.Color.from_rgb(255, 170, 50)
            )

            # Show available roles with counts
            available = []
            for role in ROLES:
                count = len([u for u in self.all_users if role in u.get('roles', [])])
                if count > 0:
                    available.append(f"{ROLES[role]} {role}: **{count}**")

            if available:
                embed.add_field(name="📋 Available Roles", value="\n".join(available), inline=False)

            back_view = BackToFilterView(self.all_users, self.author_id)
            await interaction.response.edit_message(embed=embed, view=back_view)
            return

        # Sort filtered users by reputation descending
        filtered.sort(key=lambda u: u.get('reputation', 0), reverse=True)

        user = filtered[0]
        embed = self._build_filtered_embed(user, 0, len(filtered))

        view = FindResultsView(filtered, 0, self.all_users, self.author_id, filter_label=self.role_name)
        await interaction.response.edit_message(embed=embed, view=view)

    def _build_filtered_embed(self, user, index, total):
        roles = user.get('roles', [])
        role_display = " ".join(f"{ROLES.get(r, '❓')} `{r}`" for r in roles) if roles else "`No roles set`"

        level = user.get('level', 1)
        progress = min(level / 50, 1.0)
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title=f"{ROLES.get(self.role_name, '❓')} {user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(
            name="📊 Stats",
            value=f"```\nLevel: {level} [{bar}]\nRank:  {user.get('rank', 'Unranked')}\n```",
            inline=False
        )
        embed.add_field(name="⭐ Reputation", value=f"**{user.get('reputation', 0)}**", inline=True)
        embed.add_field(name="🏷️ Roles", value=role_display, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user['_id']}`", inline=False)
        embed.set_footer(text=f"Result {index + 1} of {total} • Filtered by {self.role_name}")

        return embed


class BackToFilterView(discord.ui.View):
    """Simple view with just a back button"""

    def __init__(self, all_users, author_id: int):
        super().__init__(timeout=120)
        self.all_users = all_users
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Only the command user can interact with this.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Back to Filters", emoji="🔙", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔎 Find Developers",
            description=(
                "Browse talented developers by their roles.\n"
                "Select a role below to filter, or use **All Roles** to see everyone.\n\n"
                f"📋 **{len(self.all_users)}** developers available"
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Tip: Use 🎲 Random Pick for a surprise!")
        view = RoleFilterView(self.all_users, self.author_id)
        await interaction.response.edit_message(embed=embed, view=view)


class FindResultsView(discord.ui.View):
    """Pagination for find results"""

    def __init__(self, users, current_page: int, all_users, author_id: int, filter_label: str = "All Roles"):
        super().__init__(timeout=120)
        self.users = users
        self.current_page = current_page
        self.max_page = min(len(users) - 1, 24)  # Show up to 25 results
        self.all_users = all_users
        self.author_id = author_id
        self.filter_label = filter_label
        self._update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Only the command user can interact with this.", ephemeral=True)
            return False
        return True

    def _update_buttons(self):
        self.first_page.disabled = self.current_page == 0
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= self.max_page
        self.last_page.disabled = self.current_page >= self.max_page

        self.page_indicator.label = f"{self.current_page + 1}/{self.max_page + 1}"

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary, row=0)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self._update_display(interaction)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        await self._update_display(interaction)

    @discord.ui.button(label="1/1", style=discord.ButtonStyle.primary, disabled=True, row=0)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
        await self._update_display(interaction)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.max_page
        await self._update_display(interaction)

    @discord.ui.button(label="DM Developer", emoji="💬", style=discord.ButtonStyle.success, row=1)
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = self.users[self.current_page]
        developer_id = user['_id']

        if developer_id == interaction.user.id:
            embed = discord.Embed(
                title="🤔 That's you!",
                description="You can't send a recruitment DM to yourself.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            developer = await interaction.client.fetch_user(developer_id)

            embed = discord.Embed(
                title="📨 Someone is interested in your profile!",
                description=(
                    f"**{interaction.user.name}** (`{interaction.user.id}`) "
                    f"found your profile and wants to connect!"
                ),
                color=discord.Color.blue()
            )
            embed.add_field(
                name="👤 From",
                value=f"{interaction.user.mention}\n`{interaction.user.name}`",
                inline=True
            )
            if interaction.guild:
                embed.add_field(
                    name="🏠 Server",
                    value=interaction.guild.name,
                    inline=True
                )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="Reply to this user to start a conversation!")
            embed.timestamp = discord.utils.utcnow()

            await developer.send(embed=embed)

            confirm = discord.Embed(
                title="✅ Message Sent!",
                description=f"Your interest has been sent to **{developer.name}**.\nThey'll reach out if interested!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=confirm, ephemeral=True)
        except discord.Forbidden:
            error = discord.Embed(
                title="❌ DMs Disabled",
                description=f"**{user.get('username', 'This user')}** has their DMs closed.\nTry reaching out in the server instead.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)
        except discord.NotFound:
            error = discord.Embed(
                title="❌ User Not Found",
                description="This user no longer exists or left the platform.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)
        except Exception:
            error = discord.Embed(
                title="❌ Something Went Wrong",
                description="Could not send the message. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error, ephemeral=True)

    @discord.ui.button(label="Back to Filters", emoji="🔙", style=discord.ButtonStyle.blurple, row=1)
    async def back_to_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔎 Find Developers",
            description=(
                "Browse talented developers by their roles.\n"
                "Select a role below to filter, or use **All Roles** to see everyone.\n\n"
                f"📋 **{len(self.all_users)}** developers available"
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Tip: Use 🎲 Random Pick for a surprise!")
        view = RoleFilterView(self.all_users, self.author_id)
        await interaction.response.edit_message(embed=embed, view=view)

    async def _update_display(self, interaction: discord.Interaction):
        user = self.users[self.current_page]

        roles = user.get('roles', [])
        role_display = " ".join(f"{ROLES.get(r, '❓')} `{r}`" for r in roles) if roles else "`No roles set`"

        level = user.get('level', 1)
        rank = user.get('rank', 'Unranked')
        reputation = user.get('reputation', 0)

        # Progress bar
        progress = min(level / 50, 1.0)
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title=f"{user.get('username', 'Unknown')}",
            color=BOT_COLOR
        )
        embed.add_field(
            name="📊 Stats",
            value=f"```\nLevel: {level} [{bar}]\nRank:  {rank}\n```",
            inline=False
        )
        embed.add_field(name="⭐ Reputation", value=f"**{reputation}**", inline=True)
        embed.add_field(name="🏷️ Roles", value=role_display, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{user['_id']}`", inline=False)
        embed.set_footer(text=f"Result {self.current_page + 1} of {self.max_page + 1} • Filtered by {self.filter_label}")

        self._update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)


class RecruitmentCog(commands.Cog):
    """Recruitment and Team Finding Commands"""

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    @bot.tree.command(name="find", description="Find developers by role")
    async def find_cmd(interaction: discord.Interaction):
        await interaction.response.defer()

        all_users = await UserProfile.get_top_users(limit=100)

        if not all_users:
            embed = discord.Embed(
                title="😕 No Developers Found",
                description="There are no developers registered yet.\nBe the first to set up your profile!",
                color=discord.Color.from_rgb(255, 170, 50)
            )
            embed.set_footer(text="Use /setup to create your profile")
            await interaction.followup.send(embed=embed)
            return

        # Count roles for the overview
        role_counts = {}
        for user in all_users:
            for role in user.get('roles', []):
                role_counts[role] = role_counts.get(role, 0) + 1

        role_summary = "\n".join(
            f"{ROLES.get(role, '❓')} **{role}**: {count}"
            for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
        ) if role_counts else "No role data available"

        embed = discord.Embed(
            title="🔎 Find Developers",
            description=(
                "Browse talented developers by their roles.\n"
                "Select a role below to filter, or use **All Roles** to see everyone.\n\n"
                f"📋 **{len(all_users)}** developers available"
            ),
            color=BOT_COLOR
        )
        embed.add_field(name="📊 Role Breakdown", value=role_summary, inline=False)
        embed.set_footer(text="Tip: Use 🎲 Random Pick for a surprise!")

        view = RoleFilterView(all_users, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)

    await bot.add_cog(RecruitmentCog(bot))