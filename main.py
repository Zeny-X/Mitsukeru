import discord
import aiohttp
import io
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Your bot token in Secrets
CHANNEL_NAME = "find-anime🔍"  # your channel name
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
    # Ignore bot messages
    if message.author == bot.user:
        return

    # Only react if the bot is mentioned
    if bot.user not in message.mentions:
        return

    # Ignore if no attachments
    if not message.attachments:
        await message.channel.send("👋 Please upload a screenshot of the anime when pinging me!")
        return

    # Make sure it's in a server channel (not DMs)
    if not hasattr(message.channel, "name"):
        await message.channel.send("❌ Please use me in a server channel, not DMs.")
        return

    # Optional: limit to specific channel name
    if message.channel.name != CHANNEL_NAME:
        await message.channel.send(f"⚠️ Please use me in the #{CHANNEL_NAME} channel.")
        return

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image"):
            await message.channel.send("🔍 Searching for the anime... please wait!")

            try:
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

                        if not data.get("result"):
                            await message.channel.send("😢 Couldn't find any match.")
                            return

                        result = data["result"][0]

                        # Safely get anime title
                        anime_title = (
                            result.get("anime")
                            or result.get("title")
                            or result.get("title_english")
                            or result.get("filename")
                            or "Unknown Title"
                        )

                        episode = result.get("episode", "?")
                        similarity = round(result.get("similarity", 0) * 100, 2)
                        from_time = result.get("from", 0)
                        video_url = result.get("video", "No video available")
                        image_url = result.get("image", None)

                        msg = (
                            f"🎬 **Anime:** {anime_title}\n"
                            f"📺 **Episode:** {episode}\n"
                            f"⏱️ **Scene Time:** {from_time:.1f} sec\n"
                            f"🎯 **Similarity:** {similarity}%\n"
                            f"🔗 [Preview Clip]({video_url})"
                        )

                        await message.channel.send(msg)
                        if image_url:
                            await message.channel.send(image_url)

            except Exception as e:
                await message.channel.send(f"⚠️ Oops! Something went wrong: `{e}`")

# ✅ Don't forget this line to actually start the bot!
bot.run(TOKEN)
