import discord
import aiohttp
import io
import os
import re
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_NAME = "find-anime🔍"
TRACE_API_URL = "https://api.trace.moe/search"

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
bot = discord.Client(intents=intents)

def clean_title(raw):
    """Remove junk from filenames and keep readable anime name."""
    if not raw:
        return "Unknown Title"
    # Remove brackets, parentheses, underscores, dots
    cleaned = re.sub(r"[\[\(].*?[\]\)]", "", raw)
    cleaned = re.sub(r"[_\.]", " ", cleaned)
    # Remove junk like codec tags, numbers, episode codes
    cleaned = re.sub(r"\b(x264|aac|dvdrip|mp4|mkv|cht|chs|jpn|eng|1080p|720p|480p)\b", "", cleaned, flags=re.I)
    # Remove long numbers or episode-like fragments
    cleaned = re.sub(r"\b\d{2,4}\b", "", cleaned)
    # Trim and fix spacing
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Capitalize first letters properly
    cleaned = cleaned.title()
    # Fallback
    return cleaned or "Unknown Title"

def sec_to_hms(seconds: float):
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

    # ---- Greeting when just pinged ----
    if not message.attachments:
        greet = (
            "👋 **Konnichiwa!** I’m **Mitsukeru** by **Zenyx**!\n"
            "Want to find an anime name or which episode it’s from?\n"
            "Just upload the screenshot and ping me!! ✨"
        )
        await message.channel.send(greet)
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

                # Extract all possible title fields
                raw_title = result.get("filename") or "Unknown Title"
                anime_title = clean_title(result.get("anime") or raw_title)
                romaji_title = result.get("title_romaji") or anime_title
                english_title = result.get("title_english") or clean_title(raw_title)

                episode = result.get("episode", "?")
                similarity = round(result.get("similarity", 0) * 100, 2)
                from_time = result.get("from", 0)
                video_url = result.get("video", None)
                image_url = result.get("image", None)
                time_str = sec_to_hms(from_time)

                # Create Embed
                embed = discord.Embed(
                    title="🎬 Anime Found!",
                    description=(
                        f":flag_jp: **Romanji:** {romaji_title}\n"
                        f":flag_us: **English:** {english_title}\n\n"
                        f"📺 **Episode:** {episode}\n"
                        f"⏱️ **Scene Time:** `{time_str}`\n"
                        f"🎯 **Similarity:** `{similarity}%`"
                    ),
                    color=discord.Color.blue()
                )

                if image_url:
                    embed.set_thumbnail(url=image_url)
                embed.set_footer(text="Powered by trace.moe • Mitsukeru Bot")

                await message.channel.send(embed=embed)

                # ---- Send preview clip ----
                if video_url:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_url) as vid_resp:
                            if vid_resp.status == 200:
                                vid_data = await vid_resp.read()
                                if len(vid_data) < 8 * 1024 * 1024:
                                    await message.channel.send(
                                        file=discord.File(io.BytesIO(vid_data), filename="preview.mp4")
                                    )
                                else:
                                    await message.channel.send(f"🎞️ Preview too large, watch here: {video_url}")
                            else:
                                await message.channel.send(f"🎞️ [Preview Clip Link]({video_url})")

            except Exception as e:
                await message.channel.send(f"⚠️ Oops! Something went wrong: `{e}`")

bot.run(TOKEN)
