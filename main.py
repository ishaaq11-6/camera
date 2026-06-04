# =========================================================
# 🔥 TELEGRAM NUMBER INFO BOT FINAL VERSION
# 🔥 FULL WORKING SYSTEM
# 🔥 PTB V21+
# 🔥 FORCE JOIN
# 🔥 PREMIUM EMOJIS
# 🔥 REDEEM SYSTEM
# 🔥 ADMIN PANEL
# 🔥 NO DATA = NO BALANCE CUT
# 🔥 CONTACT OWNER BUTTON
# =========================================================

import sqlite3
import logging
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8895530294:AAGvhK-amk6pjbxhcTWJ5oRiRQXqURh6hs8"

FORCE_CHANNEL = "@KINGxSPAM"

OWNER_USERNAME = "@KINGxISHAAQ"

IMAGE_URL = "https://iili.io/ByfKoOX.png"

API_URL = "https://nv6.ek4nsh.in/api/proxy?num={num}&key=ekku3012"

ADMIN_IDS = [6026998790]

PARSE = ParseMode.HTML

# =========================================================
# STATES
# =========================================================

(
    NUMBER_INPUT,
    REDEEM_INPUT,
    GEN_REDEEM_INPUT,
    ADD_BALANCE_INPUT,
    REMOVE_BALANCE_INPUT
) = range(5)

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

c = conn.cursor()

# =========================================================
# USERS TABLE
# =========================================================

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 5
)
""")

# =========================================================
# REDEEM TABLE
# =========================================================

c.execute("""
CREATE TABLE IF NOT EXISTS redeem_codes(
    code TEXT PRIMARY KEY,
    amount INTEGER,
    limit_uses INTEGER,
    used INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================================================
# PREMIUM EMOJIS
# =========================================================

PREMIUM_EMOJIS = {

    "verified": {
        "id": "6147565374289220368",
        "fallback": "✅"
    },

    "flex": {
        "id": "6147464060305676048",
        "fallback": "😎"
    },

    "blue_verification": {
        "id": "6147524086768604985",
        "fallback": "💎"
    },

    "frozen": {
        "id": "5449449325434266744",
        "fallback": "❄️"
    },

    "crying": {
        "id": "6273840152980755328",
        "fallback": "😭"
    },

    "smiling": {
        "id": "6276057176444246654",
        "fallback": "🙂"
    },

    "teeth": {
        "id": "6273726078649372769",
        "fallback": "😁"
    },

    "done": {
        "id": "6274007313107915274",
        "fallback": "👍"
    },

    "instagram": {
        "id": "5895297528106061174",
        "fallback": "🌐"
    },

    "telegram": {
        "id": "5895735846698487922",
        "fallback": "📱"
    },

    "whatsapp": {
        "id": "5895343514320899727",
        "fallback": "📞"
    },

    "india": {
        "id": "5913754823643107921",
        "fallback": "🇮🇳"
    },

    "dollar": {
        "id": "5197434882321567830",
        "fallback": "💵"
    },

    "top": {
        "id": "5463071033256848094",
        "fallback": "🔝"
    },

    "heart": {
        "id": "6147617184479711380",
        "fallback": "❤️"
    },

    "stars": {
        "id": "6235403472741603087",
        "fallback": "⭐"
    },

    "motion": {
        "id": "5971944878815317190",
        "fallback": "💫"
    },

    "butterfly": {
        "id": "6001449118000487326",
        "fallback": "🦋"
    },

    "reactor": {
        "id": "6001440193058444284",
        "fallback": "⚙️"
    },

    "sparkles": {
        "id": "6023660820544623088",
        "fallback": "✨"
    },

    "lightning": {
        "id": "6026367225466720832",
        "fallback": "⚡"
    },

    "bow": {
        "id": "6066395745139824604",
        "fallback": "🎀"
    },

    "skull": {
        "id": "6037570896766438989",
        "fallback": "💀"
    },

    "devil": {
        "id": "5352542184493031170",
        "fallback": "👿"
    },

    "black_heart": {
        "id": "5352918496642604333",
        "fallback": "🖤"
    },

    "purple_heart": {
        "id": "5999340396432333728",
        "fallback": "🔥"
    },

    "wolf": {
        "id": "6127636064610818291",
        "fallback": "🐺"
    },

    "warning": {
        "id": "5420323339723881652",
        "fallback": "⚠️"
    },

    "pulse": {
        "id": "5352727529511723136",
        "fallback": "🩸"
    },

    "ghost": {
        "id": "5253539825360843975",
        "fallback": "👻"
    },

    "cat": {
        "id": "6057466460886799210",
        "fallback": "😼"
    }
}

# =========================================================
# PREMIUM EMOJI PARSER
# =========================================================

def e(name):

    data = PREMIUM_EMOJIS.get(name)

    if not data:
        return "❓"

    return (
        f'<tg-emoji emoji-id="{data["id"]}">'
        f'{data["fallback"]}'
        f'</tg-emoji>'
    )

# =========================================================
# REGISTER USER
# =========================================================

def register_user(user_id):

    c.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    if not c.fetchone():

        c.execute(
            "INSERT INTO users(user_id) VALUES(?)",
            (user_id,)
        )

        conn.commit()

# =========================================================
# GET BALANCE
# =========================================================

def get_balance(user_id):

    register_user(user_id)

    c.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )

    return c.fetchone()[0]

# =========================================================
# UPDATE BALANCE
# =========================================================

def update_balance(user_id, amount):

    c.execute(
        "UPDATE users SET balance=? WHERE user_id=?",
        (amount, user_id)
    )

    conn.commit()

# =========================================================
# FORCE JOIN CHECK
# =========================================================

async def check_join(user_id, context):

    try:

        member = await context.bot.get_chat_member(
            FORCE_CHANNEL,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except:
        return False

# =========================================================
# SAFE EDIT
# =========================================================

async def safe_edit(query, text, keyboard=None):

    try:

        await query.edit_message_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode=PARSE
        )

    except:

        try:

            await query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=PARSE
            )

        except:
            pass

# =========================================================
# CLEAN API DATA
# =========================================================

def clean_data(data):

    try:

        results = None

        if isinstance(data, dict):

            if data.get("results"):
                results = data["results"]

            elif data.get("data"):
                results = data["data"]

            elif data.get("result"):
                results = data["result"]

            elif data.get("list"):
                results = data["list"]

        if not results:
            return None

        text = ""

        for item in results[:10]:

            text += f"""
━━━━━━━━━━━━━━━━━━

{e("verified")} <b>Name:</b>
<code>{item.get("name","N/A")}</code>

{e("telegram")} <b>Mobile:</b>
<code>{item.get("mobile","N/A")}</code>

{e("flex")} <b>Father:</b>
<code>{item.get("fname","N/A")}</code>

{e("india")} <b>Address:</b>
<code>{item.get("address","N/A")}</code>

{e("motion")} <b>Circle:</b>
<code>{item.get("circle","N/A")}</code>

{e("sparkles")} <b>Email:</b>
<code>{item.get("email","N/A")}</code>
"""

        return text

    except Exception as error:

        print(error)

        return None

# =========================================================
# MAIN MENU
# =========================================================

async def main_menu(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "🔍 Num Info",
                callback_data="num_info"
            ),

            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "🎟 Redeem",
                callback_data="redeem"
            ),

            InlineKeyboardButton(
                "👑 Owner",
                callback_data="owner"
            )
        ],

        [
            InlineKeyboardButton(
                "🤖 Make Your Own Bot",
                url=f"https://t.me/{OWNER_USERNAME.replace('@','')}"
            )
        ]
    ]

    if update.effective_user.id in ADMIN_IDS:

        keyboard.append([
            InlineKeyboardButton(
                "⚙️ Admin Panel",
                callback_data="admin_panel"
            )
        ])

    text = f"""
{e("sparkles")} <b>WELCOME TO NUMBER INFO BOT</b>

{e("verified")} Premium Emojis Enabled
{e("motion")} Fast API Connected
{e("lightning")} PTB V21 Running
{e("heart")} Secure System Active
"""

    markup = InlineKeyboardMarkup(keyboard)

    try:

        if update.callback_query:

            await update.callback_query.edit_message_caption(
                caption=text,
                reply_markup=markup,
                parse_mode=PARSE
            )

        else:

            await update.message.reply_photo(
                photo=IMAGE_URL,
                caption=text,
                reply_markup=markup,
                parse_mode=PARSE
            )

    except:
        pass

# =========================================================
# START
# =========================================================

async def start(update: Update, context):

    user_id = update.effective_user.id

    register_user(user_id)

    joined = await check_join(
        user_id,
        context
    )

    if not joined:

        keyboard = [

            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"
                )
            ],

            [
                InlineKeyboardButton(
                    "✅ Verify",
                    callback_data="verify"
                )
            ]
        ]

        await update.message.reply_photo(
            photo=IMAGE_URL,
            caption=f"""
{e("warning")} <b>JOIN CHANNEL FIRST</b>
""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=PARSE
        )

        return

    await main_menu(update, context)

# =========================================================
# BUTTON HANDLER
# =========================================================

async def buttons(update: Update, context):

    query = update.callback_query

    await query.answer()

    data = query.data

    # =====================================================
    # VERIFY
    # =====================================================

    if data == "verify":

        joined = await check_join(
            query.from_user.id,
            context
        )

        if not joined:

            await query.answer(
                "Join Channel First",
                show_alert=True
            )

            return

        await main_menu(update, context)

    # =====================================================
    # BACK
    # =====================================================

    elif data == "back":

        await main_menu(update, context)

    # =====================================================
    # NUMBER INPUT
    # =====================================================

    elif data == "num_info":

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                ),

                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="back"
                )
            ]
        ])

        await safe_edit(
            query,
            f"""
{e("telegram")} <b>SEND 10 DIGIT NUMBER</b>

<code>9876543210</code>
""",
            keyboard
        )

        return NUMBER_INPUT

    # =====================================================
    # BALANCE
    # =====================================================

    elif data == "balance":

        balance = get_balance(
            query.from_user.id
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            ]
        ])

        await safe_edit(
            query,
            f"""
{e("dollar")} <b>YOUR BALANCE</b>

<code>{balance}</code>
""",
            keyboard
        )

    # =====================================================
    # REDEEM
    # =====================================================

    elif data == "redeem":

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                ),

                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="back"
                )
            ]
        ])

        await safe_edit(
            query,
            f"""
{e("stars")} <b>SEND REDEEM CODE</b>
""",
            keyboard
        )

        return REDEEM_INPUT

    # =====================================================
    # OWNER
    # =====================================================

    elif data == "owner":

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            ]
        ])

        await safe_edit(
            query,
            f"""
{e("heart")} <b>BOT OWNER</b>

{OWNER_USERNAME}
""",
            keyboard
        )

# =========================================================
# PROCESS NUMBER
# =========================================================

async def process_number(update: Update, context):

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:

        await update.message.reply_text(
            f"{e('warning')} Invalid Number",
            parse_mode=PARSE
        )

        return NUMBER_INPUT

    user_id = update.effective_user.id

    balance = get_balance(user_id)

    if balance < 1:

        await update.message.reply_text(
            f"{e('warning')} Insufficient Balance",
            parse_mode=PARSE
        )

        return ConversationHandler.END

    wait = await update.message.reply_text(
        f"{e('motion')} Searching Data...",
        parse_mode=PARSE
    )

    try:

        response = requests.get(
            API_URL.format(num=number),
            timeout=30
        )

        data = response.json()

        result = clean_data(data)

        # =================================================
        # NO DATA FOUND
        # =================================================

        if not result:

            await wait.delete()

            await update.message.reply_text(
                f"""
{e("warning")} <b>NO DATA FOUND</b>

{e("done")} Balance Not Deducted
""",
                parse_mode=PARSE
            )

            return ConversationHandler.END

        # =================================================
        # DEDUCT BALANCE
        # =================================================

        new_balance = balance - 1

        update_balance(
            user_id,
            new_balance
        )

        await wait.delete()

        await update.message.reply_photo(
            photo=IMAGE_URL,
            caption=f"""
{e("sparkles")} <b>SEARCH COMPLETE</b>

{result}

━━━━━━━━━━━━━━━━━━

{e("dollar")} <b>Balance Left:</b>

<code>{new_balance}</code>
""",
            parse_mode=PARSE
        )

    except Exception as error:

        await update.message.reply_text(
            f"""
{e("warning")} API Error

<code>{error}</code>
""",
            parse_mode=PARSE
        )

    return ConversationHandler.END

# =========================================================
# PROCESS REDEEM
# =========================================================

async def process_redeem(update: Update, context):

    code = update.message.text.strip().upper()

    c.execute(
        """
        SELECT amount, limit_uses, used
        FROM redeem_codes
        WHERE code=?
        """,
        (code,)
    )

    data = c.fetchone()

    if not data:

        await update.message.reply_text(
            "❌ Invalid Code"
        )

        return ConversationHandler.END

    amount, limit_uses, used = data

    if used >= limit_uses:

        await update.message.reply_text(
            "❌ Code Limit Reached"
        )

        return ConversationHandler.END

    current_balance = get_balance(
        update.effective_user.id
    )

    update_balance(
        update.effective_user.id,
        current_balance + amount
    )

    c.execute(
        """
        UPDATE redeem_codes
        SET used=used+1
        WHERE code=?
        """,
        (code,)
    )

    conn.commit()

    await update.message.reply_text(
        f"""
{e("done")} <b>REDEEM SUCCESS</b>

{e("dollar")} Added:
<code>{amount}</code>
""",
        parse_mode=PARSE
    )

    return ConversationHandler.END

# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(update: Update, context):

    query = update.callback_query

    if query.from_user.id not in ADMIN_IDS:
        return

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🎟 Generate Redeem",
                callback_data="gen_redeem"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ Add Balance",
                callback_data="add_balance"
            ),

            InlineKeyboardButton(
                "➖ Remove Balance",
                callback_data="remove_balance"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="back"
            )
        ]
    ])

    await safe_edit(
        query,
        "⚙️ <b>ADMIN PANEL</b>",
        keyboard
    )

# =========================================================
# CONVERSATION HANDLER
# =========================================================

def conv_handler():

    return ConversationHandler(

        per_message=True,

        entry_points=[
            CallbackQueryHandler(buttons)
        ],

        states={

            NUMBER_INPUT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    process_number
                )
            ],

            REDEEM_INPUT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    process_redeem
                )
            ]
        },

        fallbacks=[
            CommandHandler(
                "start",
                start
            )
        ]
    )

# =========================================================
# MAIN
# =========================================================

def main():

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_panel,
            pattern="admin_panel"
        )
    )

    app.add_handler(
        conv_handler()
    )

    print("🚀 BOT STARTED")

    app.run_polling(
        drop_pending_updates=True
    )

# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    main()