#!/usr/bin/env python3
# =============================================================================
#  FINAL STORM HOSTING BOT - Full Admin Panel + Malware Protection
#  English Language + Emojis
# =============================================================================

import os
import sys
import time
import logging
import hashlib
import threading
import subprocess
import shutil
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ========================= CONFIGURATION =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8600120347:AAEGNoZ69H5iyNAec23O-canTHgy3TtfxB0")
ADMIN_IDS = [6026998790]                    # Add more admin IDs here

DB_PATH = "storm_hosting.db"
UPLOADS_DIR = "uploads"
LOGS_DIR = "logs"
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
FREE_SLOT_LIMIT = 3

# Expanded Dangerous / Malware Patterns
DANGEROUS_PATTERNS = [
    r"os\.system", r"subprocess\.", r"eval\s*\(", r"exec\s*\(", r"__import__",
    r"socket\.", r"open.*['\"]w['\"]", r"shutil\.rmtree", r"os\.remove",
    r"os\.unlink", r"os\.rmdir", r"requests\.get", r"urllib\.request",
    r"base64\.b64decode", r"pickle\.loads", r"execfile", r"compile.*exec",
    r"globals\(\)", r"locals\(\)", r"__builtins__", r"importlib"
]

# ========================= SETUP =========================
Path(UPLOADS_DIR).mkdir(exist_ok=True)
Path(LOGS_DIR).mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("StormHostingBot")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# In-memory running processes
running_processes = defaultdict(dict)
process_lock = threading.Lock()

# ========================= DATABASE =========================
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                join_date TEXT,
                last_active TEXT
            );
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT UNIQUE,
                filename TEXT,
                filepath TEXT,
                filesize INTEGER,
                upload_date TEXT,
                is_running INTEGER DEFAULT 0
            );
        """)
    logger.info("✅ Database initialized successfully.")

# ========================= HELPERS =========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def scan_for_malware(filepath: str) -> tuple[bool, str]:
    """Returns (is_safe, reason)"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Malware pattern detected: {pattern}"
        return True, "File is clean ✅"
    except Exception as e:
        return False, f"Scan error: {e}"

def generate_file_id(user_id: int, filename: str) -> str:
    raw = f"{user_id}_{filename}_{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("📤 Upload File"), KeyboardButton("📂 Check Files"))
    kb.add(KeyboardButton("📊 Statistics"))
    if is_admin(user_id):
        kb.add(KeyboardButton("👑 Admin Panel"))
    return kb

def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📂 All Files", "📊 Statistics")
    kb.add("🚫 Ban User", "🔓 Unban User")
    kb.add("📢 Broadcast", "🧾 Logs")
    kb.add("🔙 Back")
    return kb

# ========================= PROCESS MANAGEMENT =========================
def start_process(user_id: int, file_id: str, filepath: str):
    with process_lock:
        if file_id in running_processes.get(user_id, {}):
            return False, "⚠️ Process is already running!"

    try:
        log_file = open(f"{LOGS_DIR}/proc_{user_id}_{file_id}.log", "w")
        proc = subprocess.Popen(
            [sys.executable, filepath],
            stdout=log_file,
            stderr=log_file,
            cwd=os.path.dirname(filepath)
        )

        with process_lock:
            running_processes[user_id][file_id] = proc

        with get_db() as conn:
            conn.execute("UPDATE files SET is_running = 1 WHERE file_id = ?", (file_id,))

        logger.info(f"Process started - User: {user_id}, File: {file_id}")
        return True, f"✅ Process started successfully (PID: {proc.pid})"
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        return False, f"❌ Failed to start: {e}"

def stop_process(user_id: int, file_id: str):
    with process_lock:
        proc = running_processes.get(user_id, {}).pop(file_id, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except:
                proc.kill()
    
    with get_db() as conn:
        conn.execute("UPDATE files SET is_running = 0 WHERE file_id = ?", (file_id,))

def delete_file(user_id: int, file_id: str):
    stop_process(user_id, file_id)
    with get_db() as conn:
        row = conn.execute("SELECT filepath FROM files WHERE file_id = ?", (file_id,)).fetchone()
        if row:
            shutil.rmtree(os.path.dirname(row['filepath']), ignore_errors=True)
            conn.execute("DELETE FROM files WHERE file_id = ?", (file_id,))

# ========================= FORWARD FILE TO ADMINS =========================
def forward_to_admins(filepath: str, user_id: int, filename: str, status: str):
    caption = f"📤 File Upload Report\n\n" \
              f"👤 User ID: <code>{user_id}</code>\n" \
              f"📁 File: <b>{filename}</b>\n" \
              f"📌 Status: {status}"
    
    for admin_id in ADMIN_IDS:
        try:
            with open(filepath, "rb") as f:
                bot.send_document(admin_id, f, caption=caption)
        except Exception as e:
            logger.error(f"Failed to forward file to admin {admin_id}: {e}")

# ========================= UPLOAD HANDLER =========================
@bot.message_handler(content_types=['document'])
def handle_upload(message):
    user_id = message.from_user.id
    doc = message.document

    if not doc.file_name.lower().endswith('.py'):
        bot.reply_to(message, "❌ Only `.py` Python files are allowed!")
        return

    if doc.file_size > MAX_FILE_SIZE_BYTES:
        bot.reply_to(message, f"❌ File too large! Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")
        return

    # Check slot limit for normal users
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,)).fetchone()[0]
    if count >= FREE_SLOT_LIMIT and not is_admin(user_id):
        bot.reply_to(message, f"❌ Free users can only upload {FREE_SLOT_LIMIT} files.")
        return

    try:
        file_id = generate_file_id(user_id, doc.file_name)
        user_dir = Path(UPLOADS_DIR) / str(user_id) / file_id
        user_dir.mkdir(parents=True, exist_ok=True)
        filepath = user_dir / doc.file_name

        # Download file
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open(filepath, "wb") as f:
            f.write(downloaded)

        # Malware Scan
        is_safe, scan_reason = scan_for_malware(str(filepath))

        # Forward file to admins regardless of scan result
        status = "✅ Accepted" if is_safe else "❌ Blocked (Malware Detected)"
        forward_to_admins(str(filepath), user_id, doc.file_name, status)

        if not is_safe:
            shutil.rmtree(user_dir, ignore_errors=True)
            bot.reply_to(message, f"❌ **File Blocked by Security Scanner!**\nReason: {scan_reason}")
            logger.warning(f"Malware blocked from user {user_id}: {scan_reason}")
            return

        # Save to database if safe
        with get_db() as conn:
            conn.execute("""
                INSERT INTO files (user_id, file_id, filename, filepath, filesize, upload_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, file_id, doc.file_name, str(filepath), doc.file_size, datetime.now().isoformat()))

        bot.reply_to(message, "✅ File uploaded successfully and passed security check!", 
                     reply_markup=main_menu(user_id))

    except Exception as e:
        logger.error(f"Upload error: {e}")
        bot.reply_to(message, f"❌ Upload failed: {e}")

# ========================= CHECK FILES =========================
@bot.message_handler(func=lambda m: m.text == "📂 Check Files")
def check_files(message):
    user_id = message.from_user.id
    with get_db() as conn:
        files = conn.execute("SELECT * FROM files WHERE user_id = ? ORDER BY upload_date DESC", 
                           (user_id,)).fetchall()

    if not files:
        bot.send_message(user_id, "📂 You have not uploaded any files yet.", reply_markup=main_menu(user_id))
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for f in files:
        status = "🟢" if f["is_running"] else "🔴"
        markup.add(InlineKeyboardButton(f"{status} {f['filename']}", callback_data=f"manage:{f['file_id']}"))

    bot.send_message(user_id, "📂 **Your Uploaded Files**\nTap a file to manage it:", reply_markup=markup)

# ========================= INLINE BUTTON HANDLER =========================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("manage:"):
        file_id = data.split(":")[1]
        with get_db() as conn:
            file_data = conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()

        if not file_data:
            bot.answer_callback_query(call.id, "File not found!")
            return

        running = bool(file_data["is_running"])
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("▶️ Start" if not running else "⏹ Stop", 
                               callback_data=f"{'stop' if running else 'start'}:{file_id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"delete:{file_id}")
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📁 <b>{file_data['filename']}</b>\n\n"
                 f"Status: {'🟢 Running' if running else '🔴 Stopped'}",
            reply_markup=markup
        )

    elif data.startswith("start:"):
        file_id = data.split(":")[1]
        with get_db() as conn:
            f = conn.execute("SELECT filepath FROM files WHERE file_id = ?", (file_id,)).fetchone()
        success, msg = start_process(user_id, file_id, f['filepath'])
        bot.answer_callback_query(call.id, msg[:100])

    elif data.startswith("stop:"):
        file_id = data.split(":")[1]
        stop_process(user_id, file_id)
        bot.answer_callback_query(call.id, "⏹ Process stopped successfully")

    elif data.startswith("delete:"):
        file_id = data.split(":")[1]
        delete_file(user_id, file_id)
        bot.answer_callback_query(call.id, "🗑 File deleted successfully")
        bot.delete_message(call.message.chat.id, call.message.message_id)

# ========================= ADMIN PANEL =========================
@bot.message_handler(func=lambda m: m.text == "👑 Admin Panel")
def open_admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "👑 <b>Admin Control Panel</b>\nChoose an option:", 
                     reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "📂 All Files")
def admin_all_files(message):
    if not is_admin(message.from_user.id): return
    with get_db() as conn:
        files = conn.execute("""
            SELECT f.*, u.name, u.username 
            FROM files f 
            JOIN users u ON f.user_id = u.user_id 
            ORDER BY f.upload_date DESC
        """).fetchall()

    if not files:
        bot.send_message(message.chat.id, "No files found on server.")
        return

    text = "<b>📂 All Files on Server:</b>\n\n"
    for f in files[:25]:
        status = "🟢 Running" if f["is_running"] else "🔴 Stopped"
        text += f"• <b>{f['filename']}</b>\n   User: {f['user_id']} | {status}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🚫 Ban User")
def ban_user_start(message):
    if not is_admin(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "Enter the User ID you want to ban:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(message):
    if not is_admin(message.from_user.id): return
    try:
        target_id = int(message.text.strip())
        with get_db() as conn:
            conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        bot.send_message(message.chat.id, f"🚫 User <code>{target_id}</code> has been banned.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid User ID.")

@bot.message_handler(func=lambda m: m.text == "🔓 Unban User")
def unban_user_start(message):
    if not is_admin(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "Enter the User ID you want to unban:")
    bot.register_next_step_handler(msg, process_unban)

def process_unban(message):
    if not is_admin(message.from_user.id): return
    try:
        target_id = int(message.text.strip())
        with get_db() as conn:
            conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        bot.send_message(message.chat.id, f"✅ User <code>{target_id}</code> has been unbanned.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid User ID.")

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast_start(message):
    if not is_admin(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "Write the message you want to broadcast to all users:")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(message):
    if not is_admin(message.from_user.id): return
    with get_db() as conn:
        users = conn.execute("SELECT user_id FROM users").fetchall()
    
    success = 0
    for user in users:
        try:
            bot.send_message(user['user_id'], f"📢 <b>Announcement from Admin:</b>\n\n{message.text}")
            success += 1
            time.sleep(0.05)
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Broadcast completed!\nSent to {success} users.")

@bot.message_handler(func=lambda m: m.text == "🧾 Logs")
def show_logs(message):
    if not is_admin(message.from_user.id): return
    log_files = list(Path(LOGS_DIR).glob("*.log"))[:10]
    text = "<b>📜 Recent Log Files:</b>\n\n"
    for lf in log_files:
        text += f"• {lf.name}\n"
    bot.send_message(message.chat.id, text or "No logs found.")

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def show_statistics(message):
    with get_db() as conn:
        total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        running_files = conn.execute("SELECT COUNT(*) FROM files WHERE is_running = 1").fetchone()[0]

    text = f"<b>📊 Bot Statistics</b>\n\n" \
           f"Total Files Uploaded: <b>{total_files}</b>\n" \
           f"Currently Running: <b>{running_files}</b>\n" \
           f"Free Slot Limit: <b>{FREE_SLOT_LIMIT}</b> files per user"

    reply_markup = admin_menu() if is_admin(message.from_user.id) else main_menu(message.from_user.id)
    bot.send_message(message.chat.id, text, reply_markup=reply_markup)

@bot.message_handler(func=lambda m: m.text == "🔙 Back")
def back_to_menu(message):
    bot.send_message(message.chat.id, "Returning to main menu.", reply_markup=main_menu(message.from_user.id))

# ========================= START COMMAND =========================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    with get_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, name, username, join_date, last_active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, message.from_user.first_name, message.from_user.username,
              datetime.now().isoformat(), datetime.now().isoformat()))

    bot.send_message(
        message.chat.id,
        "⚡ <b>Welcome to Ishaaq Hosting Bot</b>\n\n"
        "Upload your Python bots and host them easily.",
        reply_markup=main_menu(user_id)
    )

# ========================= RUN THE BOT =========================
if __name__ == "__main__":
    init_db()
    logger.info("🚀 Storm Hosting Bot Started Successfully")
    bot.infinity_polling()