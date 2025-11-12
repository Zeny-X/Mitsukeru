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
    """Clean file-like titles and keep something readable."""
    if not raw:
        return "Unknown Title"
    cleaned = re.sub(r"[\[\(].*?[\]\)]", "", raw)
    cleaned = re.sub(r"[_\.]", " ", cleaned)
    cleaned = re.sub(r"(x264|aac|dvdrip|mp4|mkv|cht|chs|jpn|eng)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Try to keep at least one normal word
    if len(cleaned) < 2:
        # extract words from inside the brackets as fallback
        alt = re.findall(r"[A-Za-z0-9]+", raw)
        cleaned = " ".join([w for w in alt if len(w) > 2]) or "Unknown Title"
    return cleaned

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

    # ---- Greeting if just pinged ----
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
                embed.set_footer(text="Powered by trace.moe • Mitsukeru Bot")

                await message.channel.send(embed=embed)

                # ---- Try to send the preview clip as a file ----
                if video_url:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_url) as vid_resp:
                            if vid_resp.status == 200:
                                vid_data = await vid_resp.read()
                                if len(vid_data) < 8 * 1024 * 1024:  # under 8 MB
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
