# ================================
# Telegram Hosting Bot + Website
# ================================

import os, subprocess, asyncio, json
from pyrogram import Client, filters
from flask import Flask, render_template_string
import threading

# ----------------------
# CONFIG
# ----------------------
API_ID = 38063189  # Replace with your Telegram API ID
API_HASH = "1f5b2b7bd33615a2a3f34e406dd9ecab"
BOT_TOKEN = "8321025665:AAH_yqtXQtYVAGuqKlRv4xSQXbSrUefzay0"
OWNER_ID = 6349871017  # Your Telegram ID

PACKAGE_FILE = "installed_packages.json"
RECOMMENDED_PACKAGES = ["requests", "flask", "aiohttp"]

# ----------------------
# INIT BOT
# ----------------------
app_bot = Client("HostingBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

async def install_package(package_name):
    """Install a Python package and update state"""
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
    flask_app.run(host="0.0.0.0", port=5000)  # Accessible on local network

# ----------------------
# BOT COMMANDS
# ----------------------
@app_bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "🚀 Hosting Bot Started!\n\n"
        "Commands:\n"
        "/install <package> - Install Python package\n"
        "/packages - List installed packages\n"
        "/website - Get website URL"
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
    # Start Flask in a separate thread
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
