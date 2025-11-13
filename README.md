# 🌸 Mitsukeru — Anime Scene Finder Bot

> **Developed by Zenyx for the _Otaku Enkai_ Discord Server.**  
> Mitsukeru (見つける) helps you identify anime scenes from screenshots instantly!

---

## ✨ Features

- 🖼️ Upload a screenshot → get the anime name, episode, time, and a preview clip!
- 🎬 Powered by the Trace Moe API  
- 💬 Friendly anime-style interactions  
- ⚙️ Slash command `/ping` for bot status & latency  
- ☁️ Hosted on Render for 24/7 uptime  
- 💎 Built with **Python + discord.py + aiohttp**

---

## 🚀 Setup & Deployment

### 1️⃣ Requirements
- Python 3.10+
- A Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- A [trace.moe](https://trace.moe/) API endpoint (free)

### 2️⃣ Local Setup (optional)
```bash
git clone https://github.com/<yourusername>/Mitsukeru.git
cd Mitsukeru
pip install -r requirements.txt
export DISCORD_TOKEN="your_bot_token_here"
python main.py
