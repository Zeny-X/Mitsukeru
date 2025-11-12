import discord
import aiohttp
import io
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # We'll add this later in Secrets
CHANNEL_NAME = "find-anime"
TRACE_API_URL = "https://api.trace.moe/search"

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != CHANNEL_NAME:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image"):
                await message.channel.send("🔍 Searching for the anime... please wait!")

                img_bytes = await attachment.read()

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        TRACE_API_URL,
                        data={'image': img_bytes}
                    ) as resp:
                        if resp.status != 200:
                            await message.channel.send("❌ Error contacting trace.moe API.")
                            return

                        data = await resp.json()

                        if not data["result"]:
                            await message.channel.send("😢 Couldn't find any match.")
                            return

                        result = data["result"][0]
                        anime_title = result["anime"]
                        episode = result.get("episode", "?")
                        similarity = round(result["similarity"] * 100, 2)
                        from_time = result["from"]
                        video_url = result["video"]
                        image_url = result["image"]

                        msg = (
                            f"🎬 **Anime:** {anime_title}\n"
                            f"📺 **Episode:** {episode}\n"
                            f"⏱️ **Scene Time:** {from_time:.1f} sec\n"
                            f"🎯 **Similarity:** {similarity}%\n"
                            f"🔗 [Preview Clip]({video_url})"
                        )

                        await message.channel.send(msg)
                        await message.channel.send(image_url)

bot.run(TOKEN)
