import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import io
import random


class Valentine(commands.Cog):
    """Valentine's Day Heart Animation Cog ❤️"""

    def __init__(self, bot):
        self.bot = bot

    def generate_heart_frames(self, text="Happy Valentine's Day ❤️"):
        """Generate frames for an animated heart GIF."""
        frames = []
        width, height = 400, 400
        num_frames = 30

        # Color palette
        bg_color = (20, 0, 30)  # Dark purple-black background

        for frame_num in range(num_frames):
            img = Image.new("RGBA", (width, height), bg_color)
            draw = ImageDraw.Draw(img)

            # --- Background sparkles / particles ---
            random.seed(42)  # Fixed seed so sparkles are consistent across frames
            for _ in range(60):
                sx = random.randint(0, width)
                sy = random.randint(0, height)
                sparkle_size = random.uniform(1, 3)
                # Twinkle effect
                brightness = int(
                    128 + 127 * math.sin(frame_num * 0.3 + random.random() * 6.28)
                )
                brightness = max(0, min(255, brightness))
                sparkle_color = (255, brightness, 200, brightness)
                draw.ellipse(
                    [
                        sx - sparkle_size,
                        sy - sparkle_size,
                        sx + sparkle_size,
                        sy + sparkle_size,
                    ],
                    fill=sparkle_color,
                )

            # --- Beating heart effect ---
            # Heart "beats" using a sine wave for scale
            beat = 1.0 + 0.08 * math.sin(frame_num * (2 * math.pi / num_frames) * 2)

            # --- Draw the heart shape using parametric equation ---
            cx, cy = width // 2, height // 2 + 10
            scale = 10 * beat

            # Collect heart outline points
            heart_points = []
            for i in range(360):
                t = math.radians(i)
                x = 16 * math.sin(t) ** 3
                y = -(
                    13 * math.cos(t)
                    - 5 * math.cos(2 * t)
                    - 2 * math.cos(3 * t)
                    - math.cos(4 * t)
                )
                heart_points.append((cx + x * scale, cy + y * scale))

            # --- Gradient fill for the heart ---
            # Create a mask for the heart
            heart_mask = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(heart_mask)
            mask_draw.polygon(heart_points, fill=255)

            # Create gradient heart color (top to bottom: light pink -> deep red)
            gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            for y_pos in range(height):
                ratio = y_pos / height
                r = int(255)
                g = int(80 * (1 - ratio))
                b = int(100 * (1 - ratio) + 50 * ratio)
                a = 255
                for x_pos in range(width):
                    if heart_mask.getpixel((x_pos, y_pos)) > 0:
                        gradient.putpixel((x_pos, y_pos), (r, g, b, a))

            # Composite gradient heart onto main image
            img = Image.alpha_composite(img, gradient)
            draw = ImageDraw.Draw(img)

            # --- Glow effect around heart ---
            glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_alpha = int(40 + 25 * math.sin(frame_num * 0.4))
            glow_draw.polygon(heart_points, fill=(255, 50, 80, glow_alpha))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=15))
            img = Image.alpha_composite(img, glow_layer)
            draw = ImageDraw.Draw(img)

            # --- Heart outline with slight shimmer ---
            outline_brightness = int(
                200 + 55 * math.sin(frame_num * 0.5)
            )
            outline_color = (255, outline_brightness, outline_brightness, 255)
            # Draw outline by connecting points
            for i in range(len(heart_points)):
                p1 = heart_points[i]
                p2 = heart_points[(i + 1) % len(heart_points)]
                draw.line([p1, p2], fill=outline_color, width=2)

            # --- Floating mini hearts ---
            random.seed(123)
            for i in range(8):
                start_x = random.randint(50, width - 50)
                start_y = random.randint(100, height - 50)
                float_speed = random.uniform(2, 5)
                float_offset = random.uniform(0, 6.28)
                mini_size = random.uniform(3, 7)

                # Float upward over time
                current_y = (start_y - frame_num * float_speed) % height
                current_x = start_x + 15 * math.sin(
                    frame_num * 0.2 + float_offset
                )

                mini_alpha = int(
                    150 + 100 * math.sin(frame_num * 0.3 + float_offset)
                )
                mini_alpha = max(0, min(255, mini_alpha))
                mini_color = (
                    255,
                    random.randint(100, 200),
                    random.randint(150, 220),
                    mini_alpha,
                )

                # Draw tiny heart shape
                self._draw_mini_heart(
                    draw, current_x, current_y, mini_size, mini_color
                )

            # --- Text at the bottom ---
            try:
                font = ImageFont.truetype("arial.ttf", 22)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
                    )
                except (OSError, IOError):
                    font = ImageFont.load_default()

            # Text with pulsing glow
            text_display = text
            text_bbox = draw.textbbox((0, 0), text_display, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width - text_width) // 2
            text_y = height - 55

            # Text shadow/glow
            text_glow_alpha = int(
                150 + 100 * math.sin(frame_num * 0.3)
            )
            shadow_color = (255, 100, 150, text_glow_alpha)
            draw.text(
                (text_x - 1, text_y - 1),
                text_display,
                font=font,
                fill=shadow_color,
            )
            draw.text(
                (text_x + 1, text_y + 1),
                text_display,
                font=font,
                fill=shadow_color,
            )

            # Main text
            draw.text(
                (text_x, text_y),
                text_display,
                font=font,
                fill=(255, 255, 255, 255),
            )

            # Convert to RGB for GIF (P mode)
            rgb_frame = Image.new("RGB", (width, height), bg_color)
            rgb_frame.paste(img, mask=img.split()[3])
            frames.append(rgb_frame)

        return frames

    def _draw_mini_heart(self, draw, cx, cy, size, color):
        """Draw a tiny heart at the given position."""
        points = []
        for i in range(0, 360, 10):
            t = math.radians(i)
            x = 16 * math.sin(t) ** 3
            y = -(
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )
            points.append((cx + x * (size / 16), cy + y * (size / 16)))

        if len(points) >= 3:
            draw.polygon(points, fill=color)

    @commands.command(name="valentine", aliases=["vday", "love", "heart"])
    async def valentine_command(self, ctx, *, message: str = None):
        """
        Generate a beautiful animated heart for Valentine's Day! ❤️

        Usage:
            !valentine
            !valentine Happy Valentine's Day, my love!
            !heart
            !love
        """
        async with ctx.typing():
            text = message if message else "Happy Valentine's Day ❤️"

            # Truncate text if too long
            if len(text) > 40:
                text = text[:37] + "..."

            frames = self.generate_heart_frames(text)

            # Save as animated GIF
            gif_buffer = io.BytesIO()
            frames[0].save(
                gif_buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=80,  # ms per frame
                loop=0,       # loop forever
                optimize=True,
            )
            gif_buffer.seek(0)

            # Create embed
            embed = discord.Embed(
                title="💕 Valentine's Day 💕",
                description=f"*{text}*",
                color=discord.Color.from_rgb(255, 50, 100),
            )
            embed.set_image(url="attachment://valentine_heart.gif")
            embed.set_footer(text=f"With love, from {ctx.author.display_name} 💘")

            file = discord.File(gif_buffer, filename="valentine_heart.gif")
            await ctx.send(embed=embed, file=file)

    @commands.command(name="lovemsg")
    async def love_message(self, ctx, member: discord.Member = None):
        """
        Send a Valentine's heart to someone special! 💘

        Usage:
            !lovemsg @someone
        """
        if member is None:
            await ctx.send("💔 You need to mention someone! `!lovemsg @someone`")
            return

        if member.id == ctx.author.id:
            text = "Self-love is important! ❤️"
        else:
            text = f"{ctx.author.display_name} ❤️ {member.display_name}"

        async with ctx.typing():
            frames = self.generate_heart_frames(text)

            gif_buffer = io.BytesIO()
            frames[0].save(
                gif_buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=80,
                loop=0,
                optimize=True,
            )
            gif_buffer.seek(0)

            embed = discord.Embed(
                title="💘 A Valentine For You! 💘",
                description=f"**{ctx.author.display_name}** sends their love to **{member.display_name}**! 💕",
                color=discord.Color.from_rgb(255, 20, 80),
            )
            embed.set_image(url="attachment://valentine_heart.gif")
            embed.set_footer(text="Happy Valentine's Day! 🌹")

            file = discord.File(gif_buffer, filename="valentine_heart.gif")
            await ctx.send(
                content=f"{member.mention} 💌 You received a Valentine!",
                embed=embed,
                file=file,
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-respond when someone says it's Valentine's Day."""
        if message.author.bot:
            return

        content = message.content.lower()

        # Trigger phrases
        triggers = [
            "it's valentine",
            "its valentine",
            "happy valentine",
            "valentine's day",
            "valentines day",
        ]

        if any(trigger in content for trigger in triggers):
            async with message.channel.typing():
                frames = self.generate_heart_frames("Happy Valentine's Day! ❤️")

                gif_buffer = io.BytesIO()
                frames[0].save(
                    gif_buffer,
                    format="GIF",
                    save_all=True,
                    append_images=frames[1:],
                    duration=80,
                    loop=0,
                    optimize=True,
                )
                gif_buffer.seek(0)

                embed = discord.Embed(
                    title="💕 Happy Valentine's Day! 💕",
                    description="Love is in the air! Here's a heart just for you! 🌹✨",
                    color=discord.Color.from_rgb(255, 50, 100),
                )
                embed.set_image(url="attachment://valentine_heart.gif")
                embed.set_footer(text="Spread the love! Use !valentine or !lovemsg @someone 💘")

                file = discord.File(gif_buffer, filename="valentine_heart.gif")
                await message.channel.send(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(Valentine(bot))