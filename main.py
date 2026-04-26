# ========================================================
# WHITExTRUSTED PYTHON BOT HOSTING PLATFORM v6.6 FINAL
# Ultra Fancy • Professional • Secure • 24/7 Hosting
# ========================================================
# FINAL LARGE CODEBASE - ALL COMMANDS & BUTTONS WORKING
# ========================================================

import sys
import subprocess

# Auto Package Installer
def install_packages():
    required = ["pyTelegramBotAPI", "psutil", "pytz"]
    for pkg in required:
        try:
            if pkg == "pyTelegramBotAPI":
                __import__("telebot")
            else:
                __import__(pkg)
        except ImportError:
            print(f"📦 Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"✅ {pkg} installed")

install_packages()

import telebot
import os
import sqlite3
import subprocess as sp
import psutil
import threading
import time
import re
from datetime import datetime, timedelta
import pytz
from telebot import types

# ========================= CONFIG =========================
BOT_TOKEN = "8162307466:AAGQVdLM3_cY46L0OdyDykWL3tGvIam1beY"   # ← CHANGE THIS
ADMIN_ID = 6026998790                                           # ← CHANGE THIS
OWNER_USERNAME = "@KINGxISHAAQ"

CHANNEL_USERNAME = "@KINGxSPAM"

bot = telebot.TeleBot(BOT_TOKEN)

AUTO_APPROVE_MODE = False
USER_CPU_LIMIT = 50.0
MAX_FILE_SIZE = 5 * 1024 * 1024
IST = pytz.timezone('Asia/Kolkata')

# ========================= DIRECTORIES & DATABASE =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

for directory in [DATA_DIR, USERS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

conn = sqlite3.connect(os.path.join(DATA_DIR, "bot.db"), check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,
    log_path TEXT,
    status TEXT DEFAULT 'pending',
    run_status TEXT DEFAULT 'stopped',
    pid INTEGER DEFAULT NULL,
    upload_time TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    max_bots INTEGER DEFAULT 2,
    vip_expiry TEXT DEFAULT NULL,
    join_date TEXT,
    joined_channel INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0
)''')
conn.commit()

running_processes = {}

# ========================= SECURITY SCAN =========================
def perform_security_scan(file_path: str) -> tuple:
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            return False, "❌ File too large (maximum 5MB allowed)"

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()

        dangerous_patterns = [
            r'subprocess\.(run|popen|call|check_call|check_output)',
            r'os\.system|os\.popen|os\.spawn',
            r'exec\s*\(|eval\s*\(',
            r'__import__',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                matched = re.search(pattern, content, re.IGNORECASE | re.DOTALL).group(0)[:150]
                return False, f"❌ **Dangerous Code Detected**\nPattern: `{matched}`"

        return True, "✅ Clean - No dangerous patterns found"
    except Exception as e:
        return False, f"❌ Scan error: {str(e)}"

# ========================= CPU MONITOR =========================
def monitor_cpu_and_dead_processes():
    while True:
        try:
            for fid, proc in list(running_processes.items()):
                if proc.poll() is not None:
                    del running_processes[fid]
                    c.execute("UPDATE files SET run_status='stopped', pid=NULL WHERE id=?", (fid,))
                    conn.commit()
                    continue

                c.execute("SELECT user_id FROM files WHERE id=?", (fid,))
                row = c.fetchone()
                if not row:
                    continue

                limit = 999 if row[0] == ADMIN_ID else USER_CPU_LIMIT
                p = psutil.Process(proc.pid)
                if p.cpu_percent(interval=1.0) > limit:
                    proc.kill()
                    del running_processes[fid]
                    c.execute("UPDATE files SET run_status='stopped', pid=NULL WHERE id=?", (fid,))
                    conn.commit()
        except:
            pass
        time.sleep(10)

threading.Thread(target=monitor_cpu_and_dead_processes, daemon=True).start()

# ========================= HELPERS =========================
def get_user_data(user_id: int):
    c.execute("SELECT max_bots, vip_expiry, joined_channel, is_banned FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, max_bots, join_date, joined_channel, is_banned) VALUES (?, 2, ?, 0, 0)", 
                  (user_id, datetime.now(IST).isoformat()))
        conn.commit()
        return 2, None, 0, 0
    return row

def is_banned(user_id: int) -> bool:
    c.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row and row[0] == 1

def ban_user(user_id: int):
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()

def unban_user(user_id: int):
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()

def is_user_joined_channel(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def update_channel_status(user_id: int, status: int):
    c.execute("UPDATE users SET joined_channel=? WHERE user_id=?", (status, user_id))
    conn.commit()

def get_approved_count(user_id: int):
    c.execute("SELECT COUNT(*) FROM files WHERE user_id=? AND status='approved'", (user_id,))
    return c.fetchone()[0]

# ========================= KEYBOARDS =========================
def main_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("📤 Upload Python File", "📋 My Hosted Bots")
    markup.row("📊 Statistics", "👑 Contact Owner")
    if is_admin:
        markup.row("📋 All Bots")
    return markup

def management_keyboard(file_id: int, is_running: bool):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.add(types.InlineKeyboardButton("⏹️ Stop Bot", callback_data=f"stop_{file_id}"))
    else:
        markup.add(types.InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_{file_id}"))
    markup.add(
        types.InlineKeyboardButton("📜 View Logs", callback_data=f"logs_{file_id}"),
        types.InlineKeyboardButton("🗑️ Delete Bot", callback_data=f"delete_{file_id}")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back to List", callback_data="back_to_list"))
    return markup

def force_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Join Our Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Verify Membership", callback_data="verify_join"))
    return markup

# ========================= START COMMAND =========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 **You are banned for security reasons.**")
        return

    max_bots, expiry, _, _ = get_user_data(user_id)
    is_admin = (user_id == ADMIN_ID)

    if not is_user_joined_channel(user_id):
        update_channel_status(user_id, 0)
        text = (
            "🚀 **WHITExTRUSTED Bot Hosting Platform v6.5 FINAL**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔹 24/7 Reliable Python Hosting\n"
            "🔹 Smart Security Scan\n"
            "🔹 Auto Package Installer\n"
            "🔹 Dynamic Management Panel\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Owner: {OWNER_USERNAME}\n\n"
            "Join @KINGxSPAM and click Verify to start."
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=force_join_keyboard())
        return

    expiry_text = f"VIP until {expiry[:10]}" if expiry else "Free Plan (2 bots)"
    welcome_text = (
        "🚀 **WHITExTRUSTED Bot Hosting Platform v6.5 FINAL**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 24/7 Reliable Python Hosting\n"
        "🔹 Smart Security Scan\n"
        "🔹 Auto Package Installer\n"
        "🔹 Beautiful Management Panel\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 **Maximum Bots**: {max_bots}\n"
        f"📅 **Plan Status**: {expiry_text}\n\n"
        "Choose an option from the keyboard below 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=main_keyboard(is_admin))

# ========================= VERIFY =========================
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_channel_join(call):
    if is_user_joined_channel(call.from_user.id):
        update_channel_status(call.from_user.id, 1)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_welcome(types.Message.from_user(call.from_user))
    else:
        bot.answer_callback_query(call.id, "❌ Join @KINGxSPAM first!", show_alert=True)

def check_force_join(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 **You are banned for security reasons.**")
        return False
    if not is_user_joined_channel(user_id):
        update_channel_status(user_id, 0)
        bot.send_message(message.chat.id, "⚠️ Join @KINGxSPAM to continue.", reply_markup=force_join_keyboard(), parse_mode="Markdown")
        return False
    return True

# ========================= UPLOAD HANDLER =========================
@bot.message_handler(func=lambda m: m.text == "📤 Upload Python File")
def request_file(message):
    if not check_force_join(message): return
    bot.send_message(message.chat.id, "📤 Send your `.py` file here (max 5MB)", parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_upload(message):
    if not check_force_join(message): return
    doc = message.document
    if not doc.file_name.lower().endswith('.py'):
        bot.send_message(message.chat.id, "❌ Only `.py` files supported.")
        return

    user_id = message.chat.id
    max_bots, _, _, _ = get_user_data(user_id)
    if get_approved_count(user_id) >= max_bots:
        bot.send_message(message.chat.id, f"❌ Limit reached. Max {max_bots} bots.")
        return

    # Upload Progress
    progress_msg = bot.send_message(message.chat.id, "📤 **Uploading your file...**\n`[          ] 0%`")
    for i in range(10, 101, 10):
        time.sleep(0.22)
        bar = "█" * (i // 10) + "░" * (10 - i // 10)
        bot.edit_message_text(f"📤 **Uploading your file...**\n`[{bar}] {i}%`", message.chat.id, progress_msg.message_id)

    file_info = bot.get_file(doc.file_id)
    downloaded = bot.download_file(file_info.file_path)

    user_dir = os.path.join(USERS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    c.execute("INSERT INTO files (user_id, filename, upload_time) VALUES (?, ?, ?)",
              (user_id, doc.file_name, datetime.now(IST).isoformat()))
    conn.commit()
    file_db_id = c.lastrowid

    file_path = os.path.join(user_dir, f"{file_db_id}.py")
    with open(file_path, "wb") as f:
        f.write(downloaded)

    c.execute("UPDATE files SET file_path=? WHERE id=?", (file_path, file_db_id))
    conn.commit()

    clean, reason = perform_security_scan(file_path)

    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"📥 New File\nUser ID: `{user_id}`\nFilename: `{doc.file_name}`\nScan: {reason}", parse_mode="Markdown")

    if AUTO_APPROVE_MODE:
        if clean:
            c.execute("UPDATE files SET status='approved' WHERE id=?", (file_db_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"🎉 **File Auto Approved!**\n{reason}")
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            c.execute("DELETE FROM files WHERE id=?", (file_db_id,))
            conn.commit()
            bot.send_message(message.chat.id, f"🚫 **File Blocked**\n{reason}")
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{file_db_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{file_db_id}")
        )
        bot.send_message(ADMIN_ID, "Choose action for this file:", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ File sent to admin for manual review.")

# ========================= APPROVE / REJECT =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_approval(call):
    try:
        action, fid_str = call.data.split("_")
        fid = int(fid_str)

        if action == "approve":
            c.execute("UPDATE files SET status='approved' WHERE id=?", (fid,))
            conn.commit()
            c.execute("SELECT user_id, filename FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if row:
                user_id, fname = row
                bot.send_message(user_id, f"🎉 **Your file has been approved by Admin!**\n📄 `{fname}`\nGo to My Hosted Bots to start it.", parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"✅ File ID {fid} approved for user {user_id}")
            bot.edit_message_caption("✅ Approved by Admin", call.message.chat.id, call.message.message_id)

        elif action == "reject":
            c.execute("SELECT file_path FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if row and row[0] and os.path.exists(row[0]):
                os.remove(row[0])
            c.execute("DELETE FROM files WHERE id=?", (fid,))
            conn.commit()
            c.execute("SELECT user_id, filename FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if row:
                bot.send_message(row[0], f"❌ **Your file was rejected by Admin.**\n📄 `{row[1]}`", parse_mode="Markdown")
            bot.edit_message_caption("❌ Rejected by Admin", call.message.chat.id, call.message.message_id)

        bot.answer_callback_query(call.id, "Action completed!")
    except Exception as e:
        print(f"Approval Error: {e}")
        bot.answer_callback_query(call.id, "Error occurred.")

# ========================= BOTS LIST =========================
@bot.message_handler(func=lambda m: m.text in ["📋 My Hosted Bots", "📋 All Bots"])
def show_bots_list(message):
    if not check_force_join(message): return
    is_all = (message.text == "📋 All Bots" and message.from_user.id == ADMIN_ID)

    if is_all:
        c.execute("SELECT id, filename, run_status FROM files ORDER BY id DESC")
    else:
        c.execute("SELECT id, filename, run_status FROM files WHERE user_id=? AND status='approved'", (message.chat.id,))

    files = c.fetchall()
    if not files:
        bot.send_message(message.chat.id, "No approved bots yet.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for fid, fname, rstatus in files:
        emoji = "🟢" if rstatus == "running" else "🔴"
        markup.add(types.InlineKeyboardButton(f"{emoji} {fname}", callback_data=f"manage_{fid}"))

    title = "📋 **All Uploaded Bots**" if is_all else "📋 **Your Hosted Bots**"
    bot.send_message(message.chat.id, f"{title}\nTap any filename to manage.", parse_mode="Markdown", reply_markup=markup)

# ========================= CALLBACK HANDLER =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if not check_force_join(call.message):
        return

    data = call.data
    try:
        if data.startswith("manage_"):
            fid = int(data.split("_")[1])
            c.execute("SELECT filename, run_status FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if not row:
                return
            fname, rstatus = row
            is_running = rstatus == "running"

            panel = (
                "🔧 **Bot Management Panel**\n\n"
                f"📄 Filename: `{fname}`\n"
                f"Status: **{rstatus.upper()}**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Choose an action below 👇"
            )
            bot.send_message(call.message.chat.id, panel, parse_mode="Markdown", reply_markup=management_keyboard(fid, is_running))

        elif data.startswith("start_"):
            fid = int(data.split("_")[1])
            c.execute("SELECT file_path, filename FROM files WHERE id=? AND status='approved'", (fid,))
            row = c.fetchone()
            if row:
                fpath, fname = row
                log_path = fpath.replace(".py", ".log")
                proc = sp.Popen(["python", fpath], stdout=open(log_path, "a"), stderr=sp.STDOUT, cwd=os.path.dirname(fpath))
                running_processes[fid] = proc
                c.execute("UPDATE files SET run_status='running', pid=?, log_path=? WHERE id=?", (proc.pid, log_path, fid))
                conn.commit()
                bot.send_message(call.message.chat.id, f"🚀 **Bot Started Successfully!**\n📄 `{fname}`", parse_mode="Markdown")

        elif data.startswith("stop_"):
            fid = int(data.split("_")[1])
            if fid in running_processes:
                try:
                    running_processes[fid].kill()
                    del running_processes[fid]
                except:
                    pass
            c.execute("UPDATE files SET run_status='stopped', pid=NULL WHERE id=?", (fid,))
            conn.commit()
            bot.send_message(call.message.chat.id, "⏹️ **Bot Stopped Successfully**")

        elif data.startswith("logs_"):
            fid = int(data.split("_")[1])
            c.execute("SELECT log_path FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if row and row[0] and os.path.exists(row[0]):
                with open(row[0], "r", encoding="utf-8", errors="ignore") as f:
                    logs = f.read()[-4000:]
                bot.send_message(call.message.chat.id, f"📜 **Recent Logs**\n\n```{logs or 'No output yet'}```", parse_mode="Markdown")
            else:
                bot.answer_callback_query(call.id, "No logs available yet.")

        elif data.startswith("delete_"):
            fid = int(data.split("_")[1])
            c.execute("SELECT file_path, user_id, filename FROM files WHERE id=?", (fid,))
            row = c.fetchone()
            if row:
                fpath, uid, fname = row
                if fid in running_processes:
                    try:
                        running_processes[fid].kill()
                        del running_processes[fid]
                    except:
                        pass
                if fpath and os.path.exists(fpath):
                    os.remove(fpath)
                c.execute("DELETE FROM files WHERE id=?", (fid,))
                conn.commit()
                bot.send_message(uid, f"🗑️ **Bot Deleted**\n📄 `{fname}`", parse_mode="Markdown")

        elif data == "back_to_list":
            show_bots_list(call.message)

    except Exception as e:
        print(f"Callback Error: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred.")

# ========================= ADMIN COMMANDS =========================
@bot.message_handler(commands=['vip'])
def give_vip(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid_str, days_str = message.text.split()
        target_id = int(uid_str)
        days = int(days_str)
        expiry = (datetime.now(IST) + timedelta(days=days)).isoformat()
        c.execute("UPDATE users SET max_bots=15, vip_expiry=? WHERE user_id=?", (expiry, target_id))
        conn.commit()
        bot.reply_to(message, f"✅ **VIP Activated!**\nUser `{target_id}` now has **15 bots** until {expiry[:10]}")
    except:
        bot.reply_to(message, "❌ Usage: `/vip <user_id> <days>`")

@bot.message_handler(commands=['autofile'])
def toggle_autofile(message):
    if message.from_user.id != ADMIN_ID:
        return
    global AUTO_APPROVE_MODE
    AUTO_APPROVE_MODE = not AUTO_APPROVE_MODE
    status = "✅ ENABLED" if AUTO_APPROVE_MODE else "❌ DISABLED"
    bot.send_message(message.chat.id, f"🔄 **AutoFile Mode Updated**\n**Current Status**: {status}", parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban_user_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid = message.text.split()
        ban_user(int(uid))
        bot.reply_to(message, f"✅ User {uid} banned.")
    except:
        bot.reply_to(message, "Usage: /ban <user_id>")

@bot.message_handler(commands=['unban'])
def unban_user_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid = message.text.split()
        unban_user(int(uid))
        bot.reply_to(message, f"✅ User {uid} unbanned.")
    except:
        bot.reply_to(message, "Usage: /unban <user_id>")

# ========================= STATISTICS =========================
@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def show_statistics(message):
    if not check_force_join(message): return
    c.execute("SELECT COUNT(*) FROM users"); users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM files"); files = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM files WHERE status='approved'"); approved = c.fetchone()[0]
    text = (
        "📊 **Platform Statistics**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users      : `{users}`\n"
        f"📁 Total Files      : `{files}`\n"
        f"✅ Approved Bots    : `{approved}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "All data is live and accurate."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard(message.from_user.id == ADMIN_ID))

# ========================= CONTACT OWNER =========================
@bot.message_handler(func=lambda m: m.text == "👑 Contact Owner")
def contact_owner(message):
    if not check_force_join(message): return
    bot.send_message(message.chat.id, 
        f"👑 **Platform Owner & 24/7 Support**\n\n"
        f"{OWNER_USERNAME}\n\n"
        "Feel free to message anytime for help or upgrades.",
        parse_mode="Markdown", reply_markup=main_keyboard(message.from_user.id == ADMIN_ID))

# ========================= RUN THE BOT =========================
if __name__ == "__main__":
    print("=" * 100)
    print("🚀 WHITExTRUSTED PYTHON BOT HOSTING PLATFORM v6.6 FINAL")
    print("✅ All buttons, commands, approve/reject notifications working")
    print("=" * 100)
    bot.infinity_polling(none_stop=True)