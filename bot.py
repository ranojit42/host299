# ================================
# Telegram Hosting Bot + Run Uploaded Py Files
# Python 3.14+ Compatible
# ================================

import os
import subprocess
import asyncio
import json
import threading

from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, render_template_string

# ----------------------
# CONFIG
# ----------------------
API_ID = 38063189  # Replace with your Telegram API ID
API_HASH = "1f5b2b7bd33615a2a3f34e406dd9ecab"
BOT_TOKEN = "8321025665:AAH_yqtXQtYVAGuqKlRv4xSQXbSrUefzay0"
OWNER_ID = 6349871017  # Your Telegram ID

PACKAGE_FILE = "installed_packages.json"
RECOMMENDED_PACKAGES = ["requests", "flask", "aiohttp"]
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------
# ENSURE EVENT LOOP EXISTS (Python 3.14+ fix)
# ----------------------
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ----------------------
# INIT BOT
# ----------------------
app_bot = Client("HostingBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Load installed packages
if os.path.exists(PACKAGE_FILE):
    with open(PACKAGE_FILE, "r") as f:
        installed_packages = json.load(f)
else:
    installed_packages = {}

# ----------------------
# HELPER FUNCTIONS
# ----------------------
def save_packages():
    with open(PACKAGE_FILE, "w") as f:
        json.dump(installed_packages, f)

async def install_package(package_name: str):
    try:
        process = subprocess.run(
            [os.sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True
        )
        if process.returncode == 0:
            installed_packages[package_name] = "Installed"
            save_packages()
            return True, process.stdout
        else:
            return False, process.stderr
    except Exception as e:
        return False, str(e)

# ----------------------
# FLASK WEBSITE
# ----------------------
flask_app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hosting Bot Status</title>
    <style>
        body { font-family: Arial; background:#f0f0f0; padding:20px; }
        h1 { color:#333; }
        ul { background:#fff; padding:20px; border-radius:10px; }
        li { margin-bottom:5px; }
    </style>
</head>
<body>
    <h1>Hosting Bot Status</h1>
    <ul>
    {% for pkg, status in packages.items() %}
        <li>{{ pkg }}: {{ status }}</li>
    {% endfor %}
    </ul>
</body>
</html>
"""

@flask_app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, packages=installed_packages)

def run_flask():
    asyncio.set_event_loop(asyncio.new_event_loop())
    flask_app.run(host="0.0.0.0", port=5000)

# ----------------------
# TELEGRAM BOT COMMANDS
# ----------------------
@app_bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "🚀 Hosting Bot Started!\n\n"
        "Commands:\n"
        "/install <package> - Install Python package\n"
        "/packages - List installed packages\n"
        "/website - Get website URL\n"
        "📄 Send me a .py file and I will run it automatically!"
    )

@app_bot.on_message(filters.command("install"))
async def install_handler(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only owner can install packages.")
    try:
        package_name = message.text.split(maxsplit=1)[1]
    except IndexError:
        return await message.reply_text("Usage: /install <package>")

    msg = await message.reply_text(f"⚡ Installing `{package_name}` ...")
    success, output = await install_package(package_name)

    if success:
        await msg.edit(f"✅ Package `{package_name}` installed successfully!")
    else:
        await msg.edit(f"❌ Failed to install `{package_name}`:\n{output}")

@app_bot.on_message(filters.command("packages"))
async def list_packages(client, message):
    if not installed_packages:
        return await message.reply_text("No packages installed yet.")
    msg = "📦 Installed Packages:\n"
    for pkg, status in installed_packages.items():
        msg += f"- {pkg}: {status}\n"
    await message.reply_text(msg)

@app_bot.on_message(filters.command("website"))
async def website_handler(client, message):
    await message.reply_text("🌐 Website running at `http://<your-ip>:5000`")

# ----------------------
# RUN PYTHON FILES SENT TO BOT
# ----------------------
@app_bot.on_message(filters.document & filters.document.file_extension(".py"))
async def handle_py_file(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only owner can send files.")
    
    # Save file
    file_path = os.path.join(UPLOAD_FOLDER, message.document.file_name)
    await message.document.download(file_path)
    
    msg = await message.reply_text(f"⚡ Running `{message.document.file_name}` ...")
    
    try:
        process = subprocess.run(
            [os.sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=120  # prevent very long runs
        )
        output = process.stdout + process.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n...Output truncated..."
        await msg.edit(f"✅ `{message.document.file_name}` finished!\n\nOutput:\n{output}")
    except Exception as e:
        await msg.edit(f"❌ Error running `{message.document.file_name}`:\n{e}")

# ----------------------
# AUTO INSTALL RECOMMENDED PACKAGES
# ----------------------
async def auto_install_packages():
    for pkg in RECOMMENDED_PACKAGES:
        if pkg not in installed_packages:
            success, _ = await install_package(pkg)
            print(f"Auto-installed {pkg}: {success}")

# ----------------------
# RUN EVERYTHING
# ----------------------
async def main():
    # Start Flask website in separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask website running on port 5000")

    # Auto-install recommended packages
    await auto_install_packages()

    # Start Telegram bot
    await app_bot.start()
    print("🤖 Telegram Bot running...")

    # Keep running
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
