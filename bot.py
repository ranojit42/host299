# ================= CONFIG & IMPORTS =================
import sys, subprocess, os, asyncio, time
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream, InputAudioStream
from youtubesearchpython import VideosSearch
import yt_dlp

# ================= AUTO-INSTALL FUNCTION =================
def auto_install(packages):
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"⚠ Installing {pkg} ...")
            if pkg.lower() == "pytgcalls":
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "tgcalls==2.0.0"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pytgcalls==2.1.0"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", pkg])

auto_install([
    "pyrogram",
    "yt-dlp",
    "ffmpeg-python",
    "tgcrypto",
    "pytgcalls",
    "youtube-search-python"
])

# ================= BOT CONFIG =================
API_ID = int(os.getenv("API_ID", "38354931"))
API_HASH = os.getenv("API_HASH", "244144c713cc8da9b582e40f14857216")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8464629559:AAEIV-XPJzJ4JAPTbNUkx5edddwj-CPtZh8")
OWNER_ID = int(os.getenv("OWNER_ID", "8156670159"))

bot = Client("vc_music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
vc = PyTgCalls(bot)

# ================= GLOBALS =================
queues = {}  # {chat_id: [urls]}
playing = {} # {chat_id: current_url}

# ================= UTILS =================
async def search_song(query):
    results = VideosSearch(query, limit=1).result()
    if results['result']:
        return results['result'][0]['link']
    return None

# ================= COMMANDS =================
@bot.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(
        "🎵 **VC MUSIC BOT**\n\n"
        "Use `/song <song name>` to play music in your group VC.\n"
        "Commands:\n"
        "`/song <songname>` - play song\n"
        "`/skip` - skip current\n"
        "`/stop` - stop playback"
    )

@bot.on_message(filters.command("song") & filters.group)
async def song(_, message: Message):
    chat_id = message.chat.id
    query = " ".join(message.text.split()[1:])
    if not query:
        return await message.reply_text("❌ Please provide a song name")

    url = await search_song(query)
    if not url:
        return await message.reply_text("❌ Song not found")

    if chat_id not in queues:
        queues[chat_id] = []
    queues[chat_id].append(url)
    await message.reply_text(f"✅ Added to queue: {url}")

    if chat_id not in playing or playing[chat_id] is None:
        await start_playback(chat_id)

async def start_playback(chat_id):
    if not queues.get(chat_id):
        playing[chat_id] = None
        return

    url = queues[chat_id].pop(0)
    playing[chat_id] = url
    file_path = f"{chat_id}_{int(time.time())}.mp3"

    ydl_opts = {"format": "bestaudio/best", "outtmpl": file_path, "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    await vc.join_group_call(chat_id, InputStream(InputAudioStream(file_path)))
    await asyncio.sleep(1)
    await asyncio.sleep(5)

    if os.path.exists(file_path):
        os.remove(file_path)

    playing[chat_id] = None
    if queues.get(chat_id):
        await start_playback(chat_id)

@bot.on_message(filters.command("skip") & filters.group)
async def skip(_, message):
    chat_id = message.chat.id
    await vc.leave_group_call(chat_id)
    playing[chat_id] = None
    if queues.get(chat_id):
        await start_playback(chat_id)
    await message.reply_text("⏭ Skipped current track")

@bot.on_message(filters.command("stop") & filters.group)
async def stop(_, message):
    chat_id = message.chat.id
    await vc.leave_group_call(chat_id)
    queues[chat_id] = []
    playing[chat_id] = None
    await message.reply_text("⏹ Stopped playback and cleared queue")

# ================= RUN BOT =================
print("🤖 VC MUSIC BOT STARTED")
bot.run()
