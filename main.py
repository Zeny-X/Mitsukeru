import discord
import aiohttp
import io
import os
import re
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN")       # your secret token in Replit
CHANNEL_NAME = "find-anime🔍"
TRACE_API_URL = "https://api.trace.moe/search"

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = discord.Client(intents=intents)

def clean_title(raw):
    """Remove junk like [Group] tags, file extensions, underscores."""
    if not raw:
        return "Unknown Title"
    # remove things in [brackets] or (parentheses)
    cleaned = re.sub(r"[\[\(].*?[\]\)]", "", raw)
    # replace underscores / dots with spaces
    cleaned = re.sub(r"[_\.]", " ", cleaned)
    # remove extra spaces and common encodings
    cleaned = re.sub(r"(x264|aac|dvdrip|mp4|mkv|cht|chs|jpn|eng)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "Unknown Title"

def sec_to_hms(seconds: float):
    """Convert seconds to H:MM:SS format."""
    return str(timedelta(seconds=int(seconds)))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user not in message.mentions:
        return
    if not message.attachments:
        await message.channel.send("👋 Please upload a screenshot of the anime when pinging me!")
        return
    if not hasattr(message.channel, "name"):
        await message.channel.send("❌ Please use me in a server channel, not DMs.")
        return
    if message.channel.name != CHANNEL_NAME:
        await message.channel.send(f"⚠️ Please use me in the #{CHANNEL_NAME} channel.")
        return

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image"):
            await message.channel.send("🔍 Searching for the anime... please wait!")
            try:
                img_bytes = await attachment.read()

                async with aiohttp.ClientSession() as session:
                    async with session.post(TRACE_API_URL, data={"image": img_bytes}) as resp:
                        if resp.status != 200:
                            await message.channel.send("❌ Error contacting trace.moe API.")
                            return
                        data = await resp.json()

                if not data.get("result"):
                    await message.channel.send("😢 Couldn't find any match.")
                    return

                result = data["result"][0]

                raw_title = (
                    result.get("anime")
                    or result.get("title")
                    or result.get("title_english")
                    or result.get("filename")
                )
                anime_title = clean_title(raw_title)
                episode = result.get("episode", "?")
                similarity = round(result.get("similarity", 0) * 100, 2)
                from_time = result.get("from", 0)
                video_url = result.get("video", None)
                image_url = result.get("image", None)

                time_str = sec_to_hms(from_time)

                # Create a nice embed
                embed = discord.Embed(
                    title=f"🎬 {anime_title}",
                    description=(
                        f"📺 **Episode:** {episode}\n"
                        f"⏱️ **Scene Time:** `{time_str}`\n"
                        f"🎯 **Similarity:** `{similarity}%`"
                    ),
                    color=discord.Color.blue()
                )

                if image_url:
                    embed.set_thumbnail(url=image_url)
                if video_url:
                    embed.add_field(name="🔗 Preview Clip", value=f"[Watch here]({video_url})", inline=False)

                embed.set_footer(text="Powered by trace.moe • Mitsukeru Bot")

                await message.channel.send(embed=embed)

            except Exception as e:
                await message.channel.send(f"⚠️ Oops! Something went wrong: `{e}`")

bot.run(TOKEN)
