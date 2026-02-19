

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

# ================= BOT CONFIG =================
BOT_TOKEN = "8564976780:AAF7qFJjOJe0SNSigbvaCoj_Df7FrErZzD4"
API_ID = 38063189
API_HASH = "1f5b2b7bd33615a2a3f34e406dd9ecab"
OWNER_ID = 8156670159
UPLOAD_DIR = "upl233o1ds"
DATA_FILE = "da73277a.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= SESSION =================
session_name = "Nex_HostBot_session"
bot = Client(session_name, api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= GLOBALS =================
active_scripts = {}  # user_id -> file_path -> process
logs_store = {}      # user_id -> file_path -> logs
referral_links = {}  # code -> user_id
bot_start_time = time.time()


# ================= VIP USERS =================
vip_users = set()  # store VIP user_ids in memory

# Save/load VIP users from JSON
VIP_FILE = "vip_users.json"

if os.path.exists(VIP_FILE):
    with open(VIP_FILE, "r") as f:
        vip_users = set(json.load(f))

def save_vip():
    with open(VIP_FILE, "w") as f:
        json.dump(list(vip_users), f)
        
# Load persistent users
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# ================= DATA UTIL =================
def save_data():
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(users, f)
    os.replace(temp_file, DATA_FILE)
    shutil.copy(DATA_FILE, DATA_FILE + ".backup")

def backup_data():
    if os.path.exists(DATA_FILE):
        shutil.copy(DATA_FILE, DATA_FILE + ".backup")

# ================= HELPERS =================
def uptime():
    s = int(time.time() - bot_start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

def user_folder(uid):
    path = os.path.join(UPLOAD_DIR, str(uid))
    os.makedirs(path, exist_ok=True)
    return path

def control_buttons():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🌎 Upload"), KeyboardButton("📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬")],
            [KeyboardButton("🆘 𝐇𝐞𝐥𝐩"), KeyboardButton("📊 𝐋𝐢𝐯𝐞 𝐋𝐨𝐠𝐬")],
            [KeyboardButton("🗑 𝐃𝐞𝐥𝐞𝐭𝐞"), KeyboardButton("🔄 𝐑𝐞𝐬𝐭𝐚𝐫𝐭")],
            [KeyboardButton("💔 𝐒𝐭𝐨𝐩"), KeyboardButton("⚡ 𝐒𝐩𝐞𝐞𝐝")],
            [KeyboardButton("🚀 𝐒𝐭𝐚𝐭𝐮𝐬"), KeyboardButton("🎫 𝐑𝐞𝐟𝐞𝐫𝐫𝐚𝐥")]
        ],
        resize_keyboard=True
    )

async def run_script(user_id, file_path):
    folder = user_folder(user_id)
    log_file = os.path.join(folder, os.path.basename(file_path) + ".log")
    
    while True:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, os.path.abspath(file_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        active_scripts.setdefault(user_id, {})[file_path] = proc
        logs_store.setdefault(user_id, {})[file_path] = []

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode().strip()
            logs_store[user_id][file_path].append(text)
            logs_store[user_id][file_path] = logs_store[user_id][file_path][-50:]
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(text + "\n")

        await proc.wait()
        active_scripts[user_id].pop(file_path, None)
        await asyncio.sleep(1)

def generate_referral(uid):
    code = ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))
    referral_links[code] = uid
    return f"https://t.me/Nex_HostBot?start={code}"

async def install_requirements(folder):
    req_file = os.path.join(folder, "requirements.txt")
    if os.path.exists(req_file):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])

# ================= SAFE RESTART =================
def safe_restart():
    save_data()  # Always save data before restart
    os.execv(sys.executable, [sys.executable] + sys.argv)
# ================= SIGNAL HANDLER =================
def handle_exit(sig, frame):
    save_data()  # Save data on Ctrl+C or Termux exit
    for uid, procs in active_scripts.items():
        for p in procs.values():
            p.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# ================= START COMMAND =================
@bot.on_message(filters.command("start") & filters.private)
async def start(_, m):
    uid = m.from_user.id
    users.setdefault(uid, {"tier": "FREE", "files": [], "referrals": 0})
    if uid == OWNER_ID:
        users[uid]["tier"] = "OWNER"
    save_data()

    # Handle referral code if present
    if len(m.command) > 1:
        ref_code = m.command[1]
        if ref_code in referral_links:
            ref_user = referral_links[ref_code]
            if ref_user != uid:
                users.setdefault(ref_user, {"tier": "FREE", "files": [], "referrals": 0})
                users[ref_user]["referrals"] += 1
                try:
                    await bot.send_message(ref_user, "🎉 New referral joined! Upload slot increased.")
                except:
                    pass
                save_data()

    # Build welcome text
    welcome_text = (
"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
"┃   🚀 𝐒𝐄𝐗𝐓𝐘 𝐇𝐎𝐒𝐓𝐈𝐍𝐆   ┃\n"
"┃      𝐕𝐄𝐑𝐒𝐈𝐎𝐍 3.1     ┃\n"
"┗━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
f"👤 𝐖𝐞𝐥𝐜𝐨𝐦𝐞, {m.from_user.first_name}!\n"
f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: {uid}\n"
f"🎫 𝐓𝐢𝐞𝐫: {users[uid]['tier']}" + (" 🔥 VIP" if uid in vip_users else "") + "\n"
f"📁 𝐅𝐢𝐥𝐞𝐬: {len(users[uid]['files'])}\n\n"
f"📊 𝐑𝐞𝐟𝐞𝐫𝐫𝐚𝐥𝐬: {users[uid]['referrals']}\n\n"
"📢 𝐔𝐩𝐝𝐚𝐭𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥: @SEXTYMODS\n"
"👥 𝐉𝐨𝐢𝐧 𝐆𝐫𝐨𝐮𝐩: https://t.me/+kxmchJsseDxjYzhl\n\n"
"⚡ 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:\n"
"• 𝐀𝐮𝐭𝐨-𝐑𝐞𝐜𝐨𝐯𝐞𝐫𝐲 𝐒𝐲𝐬𝐭𝐞𝐦\n"
"• 𝐓𝐢𝐞𝐫-𝐁𝐚𝐬𝐞𝐝 𝐇𝐨𝐬𝐭𝐢𝐧𝐠\n"
"• 𝐏𝐲𝐭𝐡𝐨𝐧/𝐉𝐒 𝐒𝐮𝐩𝐩𝐨𝐫𝐭\n"
"• 𝐑𝐞𝐚𝐥-𝐓𝐢𝐦𝐞 𝐌𝐨𝐧𝐢𝐭𝐨𝐫𝐢𝐧𝐠\n\n"
"𝐔𝐬𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐛𝐞𝐥𝐨𝐰 𝐭𝐨 𝐧𝐚𝐯𝐢𝐠𝐚𝐭𝐞."
)

    # Try to send profile photo if exists
    try:
        photo_id = None
        async for photo in bot.get_chat_photos(uid, limit=1):
            photo_id = photo.file_id  # Get the first photo's file_id
            break  # only need one

        if photo_id:
            await bot.send_photo(
                chat_id=uid,
                photo=photo_id,
                caption=welcome_text,
                reply_markup=control_buttons()
            )
            return  # Photo sent, stop here
    except Exception as e:
        print("Error fetching profile photo:", e)

    # Fallback: just text if no photo
    await m.reply_text(welcome_text, reply_markup=control_buttons())

# ================= KEYBOARD HANDLER =================
@bot.on_message(filters.text & filters.private)
async def keyboard_handler(_, m):
    uid = m.from_user.id
    text = m.text
    user_data = users.setdefault(uid, {"tier":"FREE","files":[],"referrals":0})

    # --------------- BUTTON LOGIC ---------------
    if text.startswith("🌎"):
        await m.reply_text("📤 Send your .py, .zip, .txt file now.")

    elif text.startswith("📁"):
        files = user_data["files"]
        if not files:
            return await m.reply_text("❌ No uploaded files.")
        buttons = [[InlineKeyboardButton(f"{f}", callback_data=f"file_{f}")] for f in files]
        await m.reply_text("📁 Your Files:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text.startswith("🆘"):
        await m.reply_text("🤖 𝐒𝐄𝐗𝐓𝐘 𝐇𝐎𝐒𝐓𝐈𝐍𝐆 𝐁𝐎𝐓 𝐇𝐄𝐋𝐏\n\n𝐁𝐚𝐬𝐢𝐜 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:\n/𝐬𝐭𝐚𝐫𝐭 - 𝐒𝐭𝐚𝐫𝐭 𝐭𝐡𝐞 𝐛𝐨𝐭\n/𝐡𝐞𝐥𝐩 - 𝐒𝐡𝐨𝐰 𝐭𝐡𝐢𝐬 𝐡𝐞𝐥𝐩 𝐦𝐞𝐬𝐬𝐚𝐠𝐞\n/𝐫𝐞𝐟𝐞𝐫 - 𝐆𝐞𝐭 𝐲𝐨𝐮𝐫 𝐫𝐞𝐟𝐞𝐫𝐫𝐚𝐥 𝐥𝐢𝐧𝐤\n/𝐬𝐭𝐚𝐭𝐬 - 𝐒𝐡𝐨𝐰 𝐛𝐨𝐭 𝐬𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬\n\n𝐔𝐩𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐅𝐢𝐥𝐞𝐬:\n• 𝐒𝐞𝐧𝐝 𝐚 .𝐩𝐲, .𝐣𝐬, 𝐨𝐫 .𝐳𝐢𝐩 𝐟𝐢𝐥𝐞\n• 𝐁𝐨𝐭 𝐰𝐢𝐥𝐥 𝐚𝐮𝐭𝐨-𝐢𝐧𝐬𝐭𝐚𝐥𝐥 𝐝𝐞𝐩𝐞𝐧𝐝𝐞𝐧𝐜𝐢𝐞𝐬\n• 𝐘𝐨𝐮𝐫 𝐬𝐜𝐫𝐢𝐩𝐭 𝐰𝐢𝐥𝐥 𝐬𝐭𝐚𝐫𝐭 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐚𝐥𝐥𝐲\n\n𝐀𝐮𝐭𝐨-𝐑𝐞𝐬𝐭𝐚𝐫𝐭 𝐒𝐲𝐬𝐭𝐞𝐦:\n• 𝐏𝐫𝐞𝐦𝐢𝐮𝐦/𝐎𝐰𝐧𝐞𝐫: ✅ 𝐀𝐥𝐰𝐚𝐲𝐬 𝐞𝐧𝐚𝐛𝐥𝐞𝐝\n• 𝐅𝐫𝐞𝐞: 𝐄𝐧𝐚𝐛𝐥𝐞 𝐛𝐲 𝐫𝐞𝐟𝐞𝐫𝐫𝐢𝐧𝐠 𝟑 𝐟𝐫𝐢𝐞𝐧𝐝𝐬\n\n𝐑𝐞𝐟𝐞𝐫𝐫𝐚𝐥 𝐒𝐲𝐬𝐭𝐞𝐦:\n1. 𝐆𝐞𝐭 𝐲𝐨𝐮𝐫 𝐫𝐞𝐟𝐞𝐫𝐫𝐚𝐥 𝐥𝐢𝐧𝐤 𝐯𝐢𝐚 /𝐫𝐞𝐟𝐞𝐫\n2. 𝐒𝐡𝐚𝐫𝐞 𝐰𝐢𝐭𝐡 𝐟𝐫𝐢𝐞𝐧𝐝𝐬\n3. 𝐄𝐚𝐜𝐡 𝐫𝐞𝐟𝐞𝐫𝐫𝐚𝐥 𝐛𝐫𝐢𝐧𝐠𝐬 𝐲𝐨𝐮 𝐜𝐥𝐨𝐬𝐞𝐫 𝐭𝐨 𝐚𝐮𝐭𝐨-𝐫𝐞𝐬𝐭𝐚𝐫𝐭\n4. 𝐀𝐟𝐭𝐞𝐫 𝟑 𝐫𝐞𝐟𝐞𝐫𝐫𝐚𝐥𝐬, 𝐚𝐮𝐭𝐨-𝐫𝐞𝐬𝐭𝐚𝐫𝐭 𝐢𝐬 𝐞𝐧𝐚𝐛𝐥𝐞𝐝!\n5. 𝐂𝐨𝐦𝐩𝐞𝐭𝐞 𝐨𝐧 𝐭𝐡𝐞 🏆 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝\n\n𝐒𝐮𝐩𝐩𝐨𝐫𝐭:\n📢 𝐔𝐩𝐝𝐚𝐭𝐞𝐬:@SEXTYMODS\n👥 𝐉𝐨𝐢𝐧 𝐆𝐫𝐨𝐮𝐩:https://t.me/+kxmchJsseDxjYzhl\n👤 𝐂𝐨𝐧𝐭𝐚𝐜𝐭: @SEXTYMODS")

    elif text.startswith("📊"):
        user_logs = logs_store.get(uid, {})
        if not user_logs:
            return await m.reply_text("❌ No active logs.")
        msg_list = []
        for file, logs in user_logs.items():
            last_logs = logs[-15:]
            escaped_logs = "\n".join(log.replace("`","'") for log in last_logs)
            msg_list.append(f"📜 Logs for {file}:\n```\n{escaped_logs}\n```")
        full_msg = "\n\n".join(msg_list)
        if len(full_msg) > 4000: full_msg = full_msg[:4000] + "\n…(truncated)"
        await m.reply_text(full_msg)

    elif text.startswith("🗑"):
        files = user_data["files"]
        if not files: return await m.reply_text("❌ No files to delete.")
        buttons = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"del_{f}")] for f in files]
        await m.reply_text("🗑 Select file to delete:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text.startswith("🔄"):
        if uid == OWNER_ID:
            await m.reply_text("🔄 Restarting bot...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            await m.reply_text("❌ Owner only")

    elif text.startswith("💔"):
        procs = active_scripts.get(uid, {})
        for p in procs.values():
            p.kill()
        active_scripts[uid] = {}
        await m.reply_text("💔 Scripts stopped")

    elif text.startswith("⚡"):
        await m.reply_text("⚡ Fast mode active")

    elif text.startswith("🚀"):
        await m.reply_text(f"Uptime: {uptime()}")

    elif text.startswith("🎫"):
        ref_link = generate_referral(uid)
        await m.reply_text(f"🎫 Referral Link:\n{ref_link}")

# ================= FILE HANDLER =================
@bot.on_message(filters.document & filters.private)
async def file_handler(_, m: Message):
    uid = m.from_user.id
    user_data = users.setdefault(uid, {"tier":"FREE","files":[],"referrals":0})

    # File limit for non-owners
    if user_data["tier"] not in ["OWNER","VIP"] and len(user_data["files"]) >= 5:
        return await m.reply_text("❌ File limit reached. Use referral to unlock more slots.")

    file = m.document
    filename = file.file_name
    if not filename.endswith((".py",".zip",".txt")):
        return await m.reply_text("❌ Only .py, .zip, .txt allowed.")

    save_path = os.path.join(user_folder(uid), filename)
    msg = await m.reply_text("⬇ Downloading file…")
    await m.download(file_name=save_path)

    # Add file to user JSON
    if filename not in user_data["files"]:
        user_data["files"].append(filename)
        save_data()

    # -------------------- ZIP --------------------
    if filename.endswith(".zip"):
        folder = user_folder(uid)

        # Step 1: Pretend install
        await msg.edit("⬇ Downloaded ZIP… Installing dependencies ⏳")
        await asyncio.sleep(2)

        # Step 2: Extracting animation
        await msg.edit("📦 Extracting ZIP file…")
        anim = ["▖","▘","▝","▗"]
        for i in range(8):
            await msg.edit(f"📦 Extracting ZIP file {anim[i % 4]}")
            await asyncio.sleep(0.5)

        # Step 3: Extract and install
        with zipfile.ZipFile(save_path, 'r') as zip_ref:
            zip_ref.extractall(folder)
        await install_requirements(folder)

        # Step 4: Run first .py in ZIP
        for f in os.listdir(folder):
            if f.endswith(".py"):
                asyncio.create_task(run_script(uid, os.path.join(folder, f)))
                await msg.edit(f"⚡ ZIP extracted. Running {f}…")
                return

    # -------------------- TXT --------------------
    elif filename.endswith(".txt"):
        await install_requirements(user_folder(uid))
        await msg.edit("📦 Requirements installed.")

    # -------------------- PY --------------------
    elif filename.endswith(".py"):
        # Step 1: Pretend install
        await msg.edit("⬇ Installing required packages… ⏳")
        await asyncio.sleep(2)

        # Step 2: Loading animation
        loading_msg = "⬇ Installing required packages"
        for i in range(3):
            await msg.edit(f"{loading_msg}{'.'*(i+1)}")
            await asyncio.sleep(0.7)

        # Step 3: Run script
        await msg.edit(f"⚡ Running {filename}…")
        asyncio.create_task(run_script(uid, save_path))

# ================= CALLBACK HANDLER =================
@bot.on_callback_query()
async def callback_handler(_, query: CallbackQuery):
    uid = query.from_user.id
    user_data = users.setdefault(uid, {"files":[]})
    data = query.data

    # --------------- DELETE ----------------
    if data.startswith("del_"):
        filename = data[4:]
        path = os.path.join(user_folder(uid), filename)
        if os.path.exists(path): os.remove(path)
        if filename in user_data["files"]: user_data["files"].remove(filename)
        save_data()
        await query.answer(f"🗑 {filename} deleted ✅")
        remaining_files = user_data["files"]
        if remaining_files:
            buttons = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"del_{f}")] for f in remaining_files]
            await query.message.edit_text("🗑 Select file to delete:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await query.message.edit_text("✅ All files deleted.")

    # --------------- FILE ACTION MENU ----------------
    elif data.startswith("file_"):
        filename = data[5:]
        path = os.path.join(user_folder(uid), filename)
        file_ext = os.path.splitext(filename)[1][1:] or "unknown"
        is_running = path in active_scripts.get(uid,{})
        status = "🟢 𝐑𝐮𝐧𝐧𝐢𝐧𝐠" if is_running else "🔴 𝐒𝐭𝐨𝐩𝐩𝐞𝐝"

        msg_text = f"⚙️ 𝐂𝐨𝐧𝐭𝐫𝐨𝐥𝐬 𝐟𝐨𝐫: {filename}\n📁 𝐓𝐲𝐩𝐞: {file_ext}\n📊 𝐒𝐭𝐚𝐭𝐮𝐬: {status}"
        buttons = [
            [InlineKeyboardButton("▶ Run", callback_data=f"run_{filename}"),
             InlineKeyboardButton("💔 Stop", callback_data=f"stop_{filename}")],
            [InlineKeyboardButton("🔄 Reset Bot", callback_data="restart")],
            [InlineKeyboardButton("📊 Live Logs", callback_data=f"logs_{filename}")],
            [InlineKeyboardButton("🗑 Delete", callback_data=f"del_{filename}")],
            [InlineKeyboardButton("⬅ Back", callback_data="myfiles")]
        ]
        await query.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons))

    # BACK TO FILE LIST
    elif data=="myfiles":
        files = user_data["files"]
        if not files: return await query.message.edit_text("❌ No files uploaded.")
        buttons = [[InlineKeyboardButton(f"{f}", callback_data=f"file_{f}")] for f in files]
        await query.message.edit_text("📁 Your Files:", reply_markup=InlineKeyboardMarkup(buttons))

    # RUN
    elif data.startswith("run_"):
        filename = data[4:]
        path = os.path.join(user_folder(uid), filename)
        if os.path.exists(path):
            asyncio.create_task(run_script(uid, path))
            await query.answer(f"▶ {filename} started")
        else:
            await query.answer("❌ File not found")

    # STOP
    elif data.startswith("stop_"):
        filename = data[5:]
        path = os.path.join(user_folder(uid), filename)
        proc = active_scripts.get(uid, {}).get(path)
        if proc:
            proc.kill()
            active_scripts[uid].pop(path, None)
            await query.answer(f"💔 {filename} stopped")
        else:
            await query.answer("❌ Script not running")

    # LIVE LOGS
    elif data.startswith("logs_"):
        filename = data[5:]
        path = os.path.join(user_folder(uid), filename)
        logs = logs_store.get(uid, {}).get(path, [])
        if logs:
            last_logs = logs[-15:]
            escaped_logs = "\n".join(log.replace("`","'") for log in last_logs)
            log_msg = f"📜 Logs for {filename}:\n```\n{escaped_logs}\n```"
            await query.answer()
            await query.message.reply_text(log_msg)
        else:
            await query.answer("❌ No logs available", show_alert=True)

    # RESET BOT
    elif data=="restart":
        await query.answer("🔄 Restarting bot...")
        os.execv(sys.executable, [sys.executable]+sys.argv)

# ================= VIP USERS =================

vip_users = set()
OWNER_ID = 8156670159  # replace with your Telegram ID

@bot.on_message(filters.command("addvip") & filters.private)
async def add_vip(_, m):
    if m.from_user.id != OWNER_ID:
        await m.reply_text("❌ Only owner can use this command.")
        return

    if len(m.command) < 2:
        await m.reply_text("Usage: /addvip <user_id>")
        return

    try:
        uid_to_add = int(m.command[1])
        vip_users.add(uid_to_add)
        await m.reply_text(f"🔥 User {uid_to_add} added to VIP successfully!")
    except Exception as e:
        await m.reply_text("❌ Invalid user ID.")
        print("Error in /addvip:", e)

@bot.on_message(filters.command("removevip") & filters.private)
async def remove_vip(_, m):
    if m.from_user.id != OWNER_ID:
        await m.reply_text("❌ Only owner can use this command.")
        return

    if len(m.command) < 2:
        await m.reply_text("Usage: /removevip <user_id>")
        return

    try:
        uid_to_remove = int(m.command[1])
        vip_users.discard(uid_to_remove)
        await m.reply_text(f"❌ User {uid_to_remove} removed from VIP successfully!")
    except:
        await m.reply_text("❌ Invalid user ID.")
# ================= RUN BOT =================
# ================= AUTO RESUME LAST RUNNING SCRIPTS =================
# ================= RUN BOT =================
print("🤖 Hosting Bot Started")  # Render supports basic emoji, but safer without

async def load_and_resume_scripts():
    """
    1. Load existing .py files from UPLOAD_DIR into users JSON.
    2. Set OWNER tier correctly.
    3. Resume all .py scripts automatically.
    """
    updated = False
    for uid_str in os.listdir(UPLOAD_DIR):
        folder = os.path.join(UPLOAD_DIR, uid_str)
        if not os.path.isdir(folder):
            continue
        uid = int(uid_str)
        user_data = users.setdefault(uid, {"tier":"FREE","files":[],"referrals":0})
        if uid == OWNER_ID:
            user_data["tier"] = "OWNER"
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                path = os.path.join(folder, filename)
                if filename not in user_data["files"]:
                    user_data["files"].append(filename)
                    updated = True
                    print(f"Added {filename} to users JSON for user {uid}")
                # Resume script
                asyncio.create_task(run_script(uid, path))
                print(f"Resuming {filename} for user {uid}...")
    if updated:
        save_data()

# ------------------- RUN BOT -------------------
if __name__ == "__main__":
    import asyncio

    # Create new event loop for Python 3.14
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Load and resume scripts
    loop.run_until_complete(load_and_resume_scripts())

    # Start the bot
    loop.run_until_complete(bot.start())
    print("Bot is now running...")

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Stopping bot...")
        loop.run_until_complete(bot.stop())
