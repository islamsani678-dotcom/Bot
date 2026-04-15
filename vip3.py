import telebot
import sqlite3
import time
from telebot import types

BOT_TOKEN = "8647373567:AAFhBObiZr738fZ82FZQPD8-DqmNYilT7qs"
BOT_USERNAME = "VIP_HACKING_CORSE_BOT"

ADMINS = [8210146346, 2104373286]

PUBLIC_CHANNEL = "@bpccoures"

CHANNEL_LINKS = [
    "https://t.me/+Hu9DA6oTPORjYjI1",
    "https://t.me/+xHEtgPp46RIyMmM1"
]

bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrals INTEGER DEFAULT 0,
    used_apk INTEGER DEFAULT 0,
    used_course INTEGER DEFAULT 0,
    referred_by INTEGER,
    banned INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS apk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    file_id TEXT,
    link TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    link TEXT
)""")

conn.commit()

# ================= UTIL =================
last_used = {}

def is_spam(uid):
    now = time.time()
    if uid in last_used and now - last_used[uid] < 1:
        return True
    last_used[uid] = now
    return False

def is_banned(uid):
    cursor.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    d = cursor.fetchone()
    return d and d[0] == 1

def check_public_join(user_id):
    try:
        member = bot.get_chat_member(PUBLIC_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= REFERRAL =================
def handle_referral(user_id, message):
    ref_id = None
    if len(message.text.split()) > 1:
        ref_id = message.text.split()[1]

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        if ref_id and ref_id.isdigit() and int(ref_id) != user_id:
            cursor.execute(
                "INSERT INTO users (user_id, referred_by) VALUES (?,?)",
                (user_id, int(ref_id))
            )
            cursor.execute(
                "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
                (int(ref_id),)
            )
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id

    if is_spam(uid): return
    if is_banned(uid):
        return bot.send_message(uid, "❌ আপনি ব্যান হয়েছেন")

    handle_referral(uid, message)

    m = types.InlineKeyboardMarkup()

    for link in CHANNEL_LINKS:
        m.add(types.InlineKeyboardButton("📢 চ্যানেল জয়েন করুন", url=link))

    m.add(types.InlineKeyboardButton(
        "📣 মেইন চ্যানেল",
        url=f"https://t.me/{PUBLIC_CHANNEL.replace('@','')}"
    ))

    m.add(types.InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify"))

    bot.send_message(uid, "সব চ্যানেল জয়েন করে ভেরিফাই চাপুন", reply_markup=m)

# ================= VERIFY =================
@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify_user(c):
    uid = c.message.chat.id

    if not check_public_join(uid):
        return bot.answer_callback_query(c.id, "❌ আগে চ্যানেল জয়েন করুন!", show_alert=True)

    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))
        conn.commit()

    main_menu(uid)

# ================= MAIN MENU =================
def main_menu(uid):
    ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🔗 আমার লিংক", "👥 আমার রেফার")
    m.add("📱 APK", "🎓 কোর্স")
    m.add("📞 অ্যাডমিন")

    bot.send_message(uid, f"স্বাগতম!\n\nআপনার লিংক:\n{ref_link}", reply_markup=m)

# ================= ADMIN PANEL =================
@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.chat.id not in ADMINS:
        return bot.send_message(message.chat.id, "❌ অনুমতি নেই")

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("➕ APK যোগ", "➕ কোর্স যোগ")
    m.add("📊 স্ট্যাটস", "🚫 ব্যান", "✅ আনব্যান")
    m.add("📢 ব্রডকাস্ট")
    m.add("🔙 বের হন")

    bot.send_message(message.chat.id, "👑 অ্যাডমিন প্যানেল", reply_markup=m)

# ================= USER + ADMIN =================
@bot.message_handler(func=lambda m: True)
def buttons(message):
    uid = message.chat.id
    text = message.text

    # USER
    if text == "🔗 আমার লিংক":
        bot.send_message(uid, f"https://t.me/{BOT_USERNAME}?start={uid}")

    elif text == "👥 আমার রেফার":
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
        bot.send_message(uid, f"আপনার রেফার: {cursor.fetchone()[0]}")

    elif text == "📱 APK":
        show_apk(uid)

    elif text == "🎓 কোর্স":
        show_course(uid)

    elif text == "📞 অ্যাডমিন":
        bot.send_message(uid, "Admin: @jiolinhacker")

    # ADMIN
    elif text == "➕ APK যোগ" and uid in ADMINS:
        bot.send_message(uid, "APK ফাইল পাঠান (caption = নাম) অথবা name | link দিন")

    elif text == "➕ কোর্স যোগ" and uid in ADMINS:
        bot.send_message(uid, "name | link")
        bot.register_next_step_handler(message, save_course)

    elif text == "📊 স্ট্যাটস" and uid in ADMINS:
        cursor.execute("SELECT COUNT(*) FROM users")
        bot.send_message(uid, f"মোট ইউজার: {cursor.fetchone()[0]}")

    elif text == "🚫 ব্যান" and uid in ADMINS:
        bot.send_message(uid, "User ID দিন")
        bot.register_next_step_handler(message, ban_user)

    elif text == "✅ আনব্যান" and uid in ADMINS:
        bot.send_message(uid, "User ID দিন")
        bot.register_next_step_handler(message, unban_user)

    elif text == "📢 ব্রডকাস্ট" and uid in ADMINS:
        bot.send_message(uid, "মেসেজ পাঠান")
        bot.register_next_step_handler(message, broadcast)

    elif text == "🔙 বের হন":
        main_menu(uid)

# ================= APK FILE RECEIVE =================
@bot.message_handler(content_types=['document'])
def handle_apk_file(message):
    uid = message.chat.id

    if uid not in ADMINS:
        return

    name = message.caption if message.caption else "নাম নেই APK"
    file_id = message.document.file_id

    cursor.execute("INSERT INTO apk (name,file_id) VALUES (?,?)",
                   (name, file_id))
    conn.commit()

    bot.send_message(uid, "✅ APK সেভ হয়েছে")

# ================= COURSE =================
def save_course(message):
    try:
        name, link = message.text.split("|")
        cursor.execute("INSERT INTO courses (name,link) VALUES (?,?)",
                       (name.strip(), link.strip()))
        conn.commit()
        bot.send_message(message.chat.id, "✅ সেভ হয়েছে")
    except:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট")

# ================= BAN =================
def ban_user(message):
    cursor.execute("UPDATE users SET banned=1 WHERE user_id=?", (int(message.text),))
    conn.commit()
    bot.send_message(message.chat.id, "🚫 ব্যান করা হয়েছে")

def unban_user(message):
    cursor.execute("UPDATE users SET banned=0 WHERE user_id=?", (int(message.text),))
    conn.commit()
    bot.send_message(message.chat.id, "✅ আনব্যান করা হয়েছে")

# ================= BROADCAST =================
def broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    for u in cursor.fetchall():
        try:
            bot.send_message(u[0], message.text)
        except:
            pass
    bot.send_message(message.chat.id, "✅ পাঠানো শেষ")

# ================= APK =================
def show_apk(uid):
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone()[0] < 2:
        return bot.send_message(uid, "❌ ২টি রেফার লাগবে")

    cursor.execute("SELECT id,name FROM apk")
    m = types.InlineKeyboardMarkup()
    for i,n in cursor.fetchall():
        m.add(types.InlineKeyboardButton(n, callback_data=f"apk_{i}"))

    bot.send_message(uid, "APK নির্বাচন করুন", reply_markup=m)

@bot.callback_query_handler(func=lambda c: c.data.startswith("apk_"))
def get_apk(c):
    cursor.execute("SELECT name,file_id,link FROM apk WHERE id=?", (int(c.data.split("_")[1]),))
    n,f,l = cursor.fetchone()

    if f:
        bot.send_document(c.message.chat.id, f, caption=n)
    else:
        bot.send_message(c.message.chat.id, f"{n}\n{l}")

# ================= COURSE =================
def show_course(uid):
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone()[0] < 5:
        return bot.send_message(uid, "❌ ৫টি রেফার লাগবে")

    cursor.execute("SELECT id,name FROM courses")
    m = types.InlineKeyboardMarkup()
    for i,n in cursor.fetchall():
        m.add(types.InlineKeyboardButton(n, callback_data=f"course_{i}"))

    bot.send_message(uid, "কোর্স নির্বাচন করুন", reply_markup=m)

@bot.callback_query_handler(func=lambda c: c.data.startswith("course_"))
def get_course(c):
    cursor.execute("SELECT name,link FROM courses WHERE id=?", (int(c.data.split("_")[1]),))
    n,l = cursor.fetchone()
    bot.send_message(c.message.chat.id, f"{n}\n{l}")

# ================= RUN =================
print("BOT RUNNING...")
bot.infinity_polling()
