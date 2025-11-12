import discord
from discord import app_commands
import aiohttp
import io
import os
import re
import time
from datetime import timedelta
from keep_alive import keep_alive   # make sure keep_alive.py is in the same folder

TOKEN = os.getenv("DISCORD_TOKEN")        # your bot token in Replit Secrets
CHANNEL_NAME = "find-anime🔍"
TRACE_API_URL = "https://api.trace.moe/search"
BOT_VERSION = "1.0.0"
START_TIME = time.time()

# ---------- Discord setup ----------
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

class MitsukeruBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"✅ Logged in as {self.user}")

bot = MitsukeruBot()

# ---------- Helpers ----------
def clean_title(raw):
    if not raw:
        return "Unknown Title"
    cleaned = re.sub(r"[\[\(].*?[\]\)]", "", raw)
    cleaned = re.sub(r"[_\.]", " ", cleaned)
    cleaned = re.sub(r"(x264|aac|dvdrip|mp4|mkv|cht|chs|jpn|eng)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) < 2:
        alt = re.findall(r"[A-Za-z0-9]+", raw)
        cleaned = " ".join([w for w in alt if len(w) > 2]) or "Unknown Title"
    return cleaned

def sec_to_hms(seconds: float):
    return str(timedelta(seconds=int(seconds)))

# ---------- /ping ----------
@bot.tree.command(name="ping", description="Check Mitsukeru’s connection and latency.")
async def ping(interaction: discord.Interaction):
    start = time.perf_counter()
    await interaction.response.defer(thinking=True)
    end = time.perf_counter()
    system_ping = round((end - start) * 1000, 2)

    ws_latency = round(bot.latency * 1000, 2)
    uptime_sec = time.time() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime_sec)))

    embed = discord.Embed(
        title="🌸 Mitsukeru Status 🌸",
        description="**Mitsukeru is online and running smoothly!**",
        color=discord.Color.green()
    )
    embed.add_field(name="🧩 Version", value=f"`{BOT_VERSION}`", inline=True)
    embed.add_field(name="🕐 Last Restart", value=f"`{uptime_str}` ago", inline=True)
    embed.add_field(name="📡 Ping", value=f"`{system_ping}ms`", inline=False)
    embed.add_field(name="└─ WebSocket", value=f"`{ws_latency}ms`", inline=True)
    embed.add_field(name="└─ System", value=f"`{system_ping}ms`", inline=True)
    embed.set_footer(text="Mitsukeru Bot • discord.py v2.x • Powered by Zenyx & Otaku Enkai")

    await interaction.followup.send(embed=embed)

# ---------- on_message (anime search + ping mention) ----------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user not in message.mentions:
        return

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
                embed.set_footer(text="Powered by Otaku Enkai • Mitsukeru Bot")

                await message.channel.send(embed=embed)

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

# ---------- Run ----------
keep_alive()
bot.run(TOKEN)
