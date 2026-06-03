import telebot
from telebot import types
import sqlite3
import os
import subprocess
import threading
import datetime
import sys
import time
import signal
import psutil

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8497285305:AAHAHgmTUAgvZw4-FFUsI9uINdQRVmLFf-w"
CHANNEL_USERNAME = "@KINGxSPAM"
ADMIN_ID = 6026998790

UPLOAD_FOLDER = "user_files"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="Markdown"
)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "ishaaq_panel.db",
    check_same_thread=False
)

c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    plan TEXT DEFAULT 'free',
    files_limit INTEGER DEFAULT 3,
    vip_expiry TEXT,
    banned INTEGER DEFAULT 0
)
""")

# FILES
c.execute("""
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_name TEXT,
    file_path TEXT,
    status TEXT DEFAULT 'stopped',
    upload_time TEXT,
    process_pid INTEGER
)
""")

# LOGS
c.execute("""
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    log_text TEXT,
    timestamp TEXT
)
""")

conn.commit()

# =========================================================
# MALWARE DETECTION
# =========================================================

MALWARE_WORDS = [
    "os.system",
    "subprocess.Popen",
    "subprocess.call",
    "eval(",
    "exec(",
    "__import__",
    "shell=True",
    "pty.spawn",
    "socket.socket",
    "requests.post",
    "urllib.request",
]

# =========================================================
# ADMIN STATES
# =========================================================

admin_pending = {}

# =========================================================
# HELPERS
# =========================================================

def is_joined(user_id):

    try:

        member = bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except:
        return False


def is_banned(user_id):

    c.execute(
        "SELECT banned FROM users WHERE user_id=?",
        (user_id,)
    )

    res = c.fetchone()

    return bool(res and res[0] == 1)


def register_user(user_id, username):

    c.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username)
    VALUES (?, ?)
    """, (
        user_id,
        username
    ))

    conn.commit()


def check_vip(user_id):

    c.execute("""
    SELECT vip_expiry
    FROM users
    WHERE user_id=?
    """, (user_id,))

    res = c.fetchone()

    if res and res[0]:

        try:

            expiry = datetime.datetime.strptime(
                res[0],
                "%Y-%m-%d %H:%M:%S"
            )

            return expiry > datetime.datetime.now()

        except:
            return False

    return False


def get_limit(user_id):

    if check_vip(user_id):
        return 15

    return 3


def get_files_count(user_id):

    c.execute("""
    SELECT COUNT(*)
    FROM files
    WHERE user_id=?
    """, (user_id,))

    return c.fetchone()[0]


def add_log(file_id, text):

    c.execute("""
    INSERT INTO logs
    (file_id, log_text, timestamp)
    VALUES (?, ?, ?)
    """, (
        file_id,
        text[:4000],
        datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()


# =========================================================
# AUTO PACKAGE INSTALLER
# =========================================================

def install_packages(file_path):

    packages = []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            content = f.read().lower()

        # =================================================
        # PACKAGE DETECTION
        # =================================================

        if "import requests" in content:
            packages.append("requests")

        if "import aiohttp" in content:
            packages.append("aiohttp")

        if "import flask" in content:
            packages.append("flask")

        if "import telebot" in content:
            packages.append("pyTelegramBotAPI")

        if "import bs4" in content:
            packages.append("beautifulsoup4")

        if "import fake_useragent" in content:
            packages.append("fake-useragent")

        if "import colorama" in content:
            packages.append("colorama")

        if "import pyrogram" in content:
            packages.append("pyrogram")

        if "import tgcrypto" in content:
            packages.append("tgcrypto")

        if "import telethon" in content:
            packages.append("telethon")

        if "import pytz" in content:
            packages.append("pytz")

        if "import motor" in content:
            packages.append("motor")

        if "import pymongo" in content:
            packages.append("pymongo")

        if "import instaloader" in content:
            packages.append("instaloader")

        if "import numpy" in content:
            packages.append("numpy")

        if "import pandas" in content:
            packages.append("pandas")

        if "import PIL" in content:
            packages.append("pillow")

        # =================================================
        # INSTALL
        # =================================================

        for pkg in packages:

            try:

                __import__(pkg.replace("-", "_"))

            except:

                subprocess.call([
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    pkg
                ])

    except:
        pass


# =========================================================
# FILE RUNNER
# =========================================================

def run_user_file(file_id, file_path):

    try:

        install_packages(file_path)

        process = subprocess.Popen(
            [sys.executable, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        c.execute("""
        UPDATE files
        SET status=?, process_pid=?
        WHERE file_id=?
        """, (
            "running",
            process.pid,
            file_id
        ))

        conn.commit()

        for line in iter(
            process.stdout.readline,
            ""
        ):

            if line.strip():

                add_log(
                    file_id,
                    line.strip()
                )

        process.wait()

        c.execute("""
        UPDATE files
        SET status=?, process_pid=?
        WHERE file_id=?
        """, (
            "stopped",
            None,
            file_id
        ))

        conn.commit()

    except Exception as e:

        add_log(
            file_id,
            f"ERROR: {str(e)}"
        )


# =========================================================
# KEYBOARDS
# =========================================================

def main_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "🚀 Deploy",
        "📁 My Files"
    )

    markup.row(
        "👤 Profile",
        "📊 Statics"
    )

    markup.row(
        "👑 Owner"
    )

    return markup


def admin_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "🔨 Ban User",
        "✅ Unban User"
    )

    markup.row(
        "💎 Give VIP",
        "🔄 Restart Bot"
    )

    markup.row(
        "🔙 Back"
    )

    return markup


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.chat.id

    username = (
        message.from_user.username
        or "NoUsername"
    )

    if is_banned(user_id):

        bot.send_message(
            user_id,
            "🚫 You Are Banned"
        )

        return

    register_user(
        user_id,
        username
    )

    if not is_joined(user_id):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "🔗 Join Channel",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "✅ I Joined",
                callback_data="check_join"
            )
        )

        bot.send_message(
            user_id,
            "👋 Welcome To Ishaaq Hosting Panel\n\nJoin Channel First",
            reply_markup=markup
        )

        return

    bot.send_message(
        user_id,
        f"✅ Welcome {message.from_user.first_name}",
        reply_markup=main_menu()
    )


# =========================================================
# CALLBACKS
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    user_id = call.message.chat.id

    data = call.data

    # =====================================================
    # JOIN CHECK
    # =====================================================

    if data == "check_join":

        if is_joined(user_id):

            bot.edit_message_text(
                "✅ Verification Successful",
                user_id,
                call.message.message_id
            )

            bot.send_message(
                user_id,
                "Choose Option Below",
                reply_markup=main_menu()
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Join Channel First",
                show_alert=True
            )

    # =====================================================
    # APPROVE FILE
    # =====================================================

    elif data.startswith("approve_"):

        file_path = data.split("_", 1)[1]

        file_name = os.path.basename(
            file_path
        )

        try:

            real_name = "_".join(
                file_name.split("_")[2:]
            )

            uploader_id = int(
                file_name.split("_")[0]
            )

        except:

            bot.answer_callback_query(
                call.id,
                "Invalid File"
            )

            return

        c.execute("""
        INSERT INTO files
        (
            user_id,
            file_name,
            file_path,
            upload_time
        )
        VALUES (?, ?, ?, ?)
        """, (
            uploader_id,
            real_name,
            file_path,
            datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()

        bot.edit_message_caption(
            caption="✅ File Approved",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        bot.send_message(
            uploader_id,
            f"✅ Your File `{real_name}` Approved"
        )

    # =====================================================
    # DECLINE FILE
    # =====================================================

    elif data.startswith("decline_"):

        file_path = data.split("_", 1)[1]

        file_name = os.path.basename(
            file_path
        )

        try:

            uploader_id = int(
                file_name.split("_")[0]
            )

        except:

            uploader_id = None

        if os.path.exists(file_path):

            os.remove(file_path)

        bot.edit_message_caption(
            caption="❌ File Declined",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        if uploader_id:

            bot.send_message(
                uploader_id,
                "❌ Your File Declined"
            )

    # =====================================================
    # MANAGE FILE
    # =====================================================

    elif data.startswith("manage_"):

        file_id = int(
            data.split("_")[1]
        )

        c.execute("""
        SELECT file_name, status
        FROM files
        WHERE file_id=?
        """, (file_id,))

        res = c.fetchone()

        if not res:
            return

        file_name, status = res

        markup = types.InlineKeyboardMarkup()

        if status == "running":

            markup.add(
                types.InlineKeyboardButton(
                    "⏹ Stop",
                    callback_data=f"toggle_{file_id}"
                )
            )

        else:

            markup.add(
                types.InlineKeyboardButton(
                    "▶️ Start",
                    callback_data=f"toggle_{file_id}"
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "📜 Logs",
                callback_data=f"logs_{file_id}"
            ),

            types.InlineKeyboardButton(
                "🗑 Delete",
                callback_data=f"delete_{file_id}"
            )
        )

        bot.edit_message_text(
            f"📄 File: `{file_name}`\n"
            f"📊 Status: `{status.upper()}`",
            user_id,
            call.message.message_id,
            reply_markup=markup
        )

    # =====================================================
    # START / STOP
    # =====================================================

    elif data.startswith("toggle_"):

        file_id = int(
            data.split("_")[1]
        )

        c.execute("""
        SELECT status, file_path, process_pid
        FROM files
        WHERE file_id=?
        """, (file_id,))

        res = c.fetchone()

        if not res:
            return

        status, path, pid = res

        # =================================================
        # START
        # =================================================

        if status == "stopped":

            threading.Thread(
                target=run_user_file,
                args=(file_id, path),
                daemon=True
            ).start()

            bot.answer_callback_query(
                call.id,
                "✅ Started"
            )

        # =================================================
        # STOP
        # =================================================

        else:

            try:

                if pid:

                    parent = psutil.Process(pid)

                    for child in parent.children(
                        recursive=True
                    ):

                        child.kill()

                    parent.kill()

            except:
                pass

            c.execute("""
            UPDATE files
            SET status=?, process_pid=?
            WHERE file_id=?
            """, (
                "stopped",
                None,
                file_id
            ))

            conn.commit()

            bot.answer_callback_query(
                call.id,
                "⏹ Stopped"
            )

    # =====================================================
    # LOGS
    # =====================================================

    elif data.startswith("logs_"):

        file_id = int(
            data.split("_")[1]
        )

        c.execute("""
        SELECT log_text, timestamp
        FROM logs
        WHERE file_id=?
        ORDER BY log_id DESC
        LIMIT 10
        """, (file_id,))

        logs = c.fetchall()

        text = "📜 Last 10 Logs\n\n"

        if not logs:

            text += "No Logs Found"

        else:

            for log in logs:

                text += (
                    f"⏰ `{log[1]}`\n"
                    f"`{log[0][:500]}`\n\n"
                )

        bot.edit_message_text(
            text,
            user_id,
            call.message.message_id
        )

    # =====================================================
    # DELETE FILE
    # =====================================================

    elif data.startswith("delete_"):

        file_id = int(
            data.split("_")[1]
        )

        c.execute("""
        SELECT file_path, process_pid
        FROM files
        WHERE file_id=?
        """, (file_id,))

        res = c.fetchone()

        if res:

            path, pid = res

            try:

                if pid:

                    parent = psutil.Process(pid)

                    for child in parent.children(
                        recursive=True
                    ):

                        child.kill()

                    parent.kill()

            except:
                pass

            if os.path.exists(path):

                os.remove(path)

        c.execute("""
        DELETE FROM files
        WHERE file_id=?
        """, (file_id,))

        conn.commit()

        bot.edit_message_text(
            "🗑 File Deleted",
            user_id,
            call.message.message_id
        )


# =========================================================
# DEPLOY
# =========================================================

@bot.message_handler(func=lambda m: m.text == "🚀 Deploy")
def deploy(message):

    user_id = message.chat.id

    if is_banned(user_id):

        bot.send_message(
            user_id,
            "🚫 You Are Banned"
        )

        return

    limit = get_limit(user_id)

    count = get_files_count(user_id)

    if count >= limit:

        bot.send_message(
            user_id,
            f"❌ Limit Reached ({limit})"
        )

        return

    msg = bot.send_message(
        user_id,
        "📤 Send Your .py File"
    )

    bot.register_next_step_handler(
        msg,
        process_file_upload
    )


# =========================================================
# FILE UPLOAD
# =========================================================

def process_file_upload(message):

    user_id = message.chat.id

    if not message.document:

        bot.send_message(
            user_id,
            "❌ Send Python File"
        )

        return

    if not message.document.file_name.endswith(".py"):

        bot.send_message(
            user_id,
            "❌ Only .py Allowed"
        )

        return

    try:

        file_info = bot.get_file(
            message.document.file_id
        )

        downloaded = bot.download_file(
            file_info.file_path
        )

        original_name = (
            message.document.file_name
        )

        safe_name = (
            f"{user_id}_{int(time.time())}_{original_name}"
        )

        file_path = os.path.join(
            UPLOAD_FOLDER,
            safe_name
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(downloaded)

        # =================================================
        # MALWARE CHECK
        # =================================================

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            content = f.read().lower()

        malware = any(
            word in content
            for word in MALWARE_WORDS
        )

        # =================================================
        # SAFE FILE
        # =================================================

        if not malware:

            c.execute("""
            INSERT INTO files
            (
                user_id,
                file_name,
                file_path,
                upload_time
            )
            VALUES (?, ?, ?, ?)
            """, (
                user_id,
                original_name,
                file_path,
                datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))

            conn.commit()

            with open(file_path, "rb") as f:

                bot.send_document(
                    ADMIN_ID,
                    f,
                    caption=(
                        f"✅ Safe File Uploaded\n\n"
                        f"👤 User: {user_id}\n"
                        f"📄 File: {original_name}"
                    )
                )

            bot.send_message(
                user_id,
                f"✅ `{original_name}` Uploaded"
            )

        # =================================================
        # MALWARE FILE
        # =================================================

        else:

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{file_path}"
                ),

                types.InlineKeyboardButton(
                    "❌ Decline",
                    callback_data=f"decline_{file_path}"
                )
            )

            with open(file_path, "rb") as f:

                bot.send_document(
                    ADMIN_ID,
                    f,
                    caption=(
                        f"⚠️ Malware Detected\n\n"
                        f"👤 User: {user_id}\n"
                        f"📄 File: {original_name}"
                    ),
                    reply_markup=markup
                )

            bot.send_message(
                user_id,
                "⚠️ Malware Found\nSent For Approval"
            )

    except Exception as e:

        bot.send_message(
            user_id,
            f"❌ Upload Error\n\n`{str(e)}`"
        )


# =========================================================
# MY FILES
# =========================================================

@bot.message_handler(func=lambda m: m.text == "📁 My Files")
def my_files(message):

    user_id = message.chat.id

    c.execute("""
    SELECT file_id, file_name, status
    FROM files
    WHERE user_id=?
    """, (user_id,))

    files = c.fetchall()

    if not files:

        bot.send_message(
            user_id,
            "📭 No Files Uploaded"
        )

        return

    for file in files:

        file_id, file_name, status = file

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                f"📄 {file_name}",
                callback_data=f"manage_{file_id}"
            )
        )

        bot.send_message(
            user_id,
            f"🆔 File ID: `{file_id}`\n"
            f"📊 Status: `{status.upper()}`",
            reply_markup=markup
        )


# =========================================================
# PROFILE
# =========================================================

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):

    user_id = message.chat.id

    limit = get_limit(user_id)

    count = get_files_count(user_id)

    plan = (
        "VIP"
        if check_vip(user_id)
        else "FREE"
    )

    text = (
        f"👤 Profile\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💎 Plan: `{plan}`\n"
        f"📁 Files: `{count}/{limit}`"
    )

    bot.send_message(
        user_id,
        text
    )


# =========================================================
# STATICS
# =========================================================

@bot.message_handler(func=lambda m: m.text == "📊 Statics")
def statics(message):

    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

    c.execute("""
    SELECT COUNT(*)
    FROM files
    WHERE status='running'
    """)

    running = c.fetchone()[0]

    text = (
        f"📊 Bot Statistics\n\n"
        f"👥 Users: `{users}`\n"
        f"⚡ Running Files: `{running}`"
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# OWNER
# =========================================================

@bot.message_handler(func=lambda m: m.text == "👑 Owner")
def owner(message):

    bot.send_message(
        message.chat.id,
        "👑 Owner: @KINGxISHAAQ"
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@bot.message_handler(commands=["panel"])
def panel(message):

    if message.chat.id != ADMIN_ID:
        return

    bot.send_message(
        ADMIN_ID,
        "🛠 Admin Panel",
        reply_markup=admin_menu()
    )


# =========================================================
# ADMIN BUTTONS
# =========================================================

@bot.message_handler(func=lambda m: m.text in [
    "🔨 Ban User",
    "✅ Unban User",
    "💎 Give VIP",
    "🔄 Restart Bot"
])
def admin_buttons(message):

    if message.chat.id != ADMIN_ID:
        return

    action = message.text

    # =====================================================
    # RESTART
    # =====================================================

    if action == "🔄 Restart Bot":

        bot.send_message(
            ADMIN_ID,
            "🔄 Restarting..."
        )

        python = sys.executable

        os.execl(
            python,
            python,
            *sys.argv
        )

        return

    admin_pending[ADMIN_ID] = action

    # =====================================================
    # VIP
    # =====================================================

    if action == "💎 Give VIP":

        bot.send_message(
            ADMIN_ID,
            "Send:\n\n123456789 30"
        )

    # =====================================================
    # BAN / UNBAN
    # =====================================================

    else:

        bot.send_message(
            ADMIN_ID,
            "Send User ID"
        )


# =========================================================
# ADMIN INPUT
# =========================================================

@bot.message_handler(
    func=lambda m: m.chat.id == ADMIN_ID
)
def admin_inputs(message):

    if ADMIN_ID not in admin_pending:
        return

    action = admin_pending[ADMIN_ID]

    try:

        # =================================================
        # GIVE VIP
        # =================================================

        if action == "💎 Give VIP":

            data = message.text.split()

            if len(data) != 2:

                bot.send_message(
                    ADMIN_ID,
                    "❌ Invalid Format"
                )

                return

            uid = int(data[0])

            days = int(data[1])

            expiry = (
                datetime.datetime.now()
                + datetime.timedelta(days=days)
            ).strftime("%Y-%m-%d %H:%M:%S")

            c.execute("""
            UPDATE users
            SET
                plan='vip',
                vip_expiry=?,
                files_limit=15
            WHERE user_id=?
            """, (
                expiry,
                uid
            ))

            conn.commit()

            bot.send_message(
                ADMIN_ID,
                f"✅ VIP Added\n\n"
                f"👤 User: `{uid}`\n"
                f"📅 Days: `{days}`"
            )

            try:

                bot.send_message(
                    uid,
                    f"🎉 VIP Activated For {days} Days"
                )

            except:
                pass

        # =================================================
        # BAN USER
        # =================================================

        elif action == "🔨 Ban User":

            uid = int(message.text)

            c.execute("""
            UPDATE users
            SET banned=1
            WHERE user_id=?
            """, (uid,))

            conn.commit()

            bot.send_message(
                ADMIN_ID,
                f"🚫 User `{uid}` Banned"
            )

        # =================================================
        # UNBAN USER
        # =================================================

        elif action == "✅ Unban User":

            uid = int(message.text)

            c.execute("""
            UPDATE users
            SET banned=0
            WHERE user_id=?
            """, (uid,))

            conn.commit()

            bot.send_message(
                ADMIN_ID,
                f"✅ User `{uid}` Unbanned"
            )

    except Exception as e:

        bot.send_message(
            ADMIN_ID,
            f"❌ Error\n\n`{str(e)}`"
        )

    if ADMIN_ID in admin_pending:

        del admin_pending[ADMIN_ID]


# =========================================================
# RUN BOT
# =========================================================

print("✅ Ishaaq Hosting Panel Started")

while True:

    try:

        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print("Polling Error:", e)

        time.sleep(5)