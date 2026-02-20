# Telegram VC Music Bot

🎵 Play music in Telegram Group Voice Chats.

## Commands
- `/song <songname>` - play song in VC
- `/skip` - skip current song
- `/stop` - stop playback

## Deploy on Render
1. Push this repo to GitHub.
2. Create a **Python** service on Render.
3. Set Environment Variables (`API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`) in Render.
4. Set **Start Command**: `bash start.sh`
5. Deploy! Bot will run 24/7.
