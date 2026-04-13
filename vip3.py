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
        return bot.send_message(uid, "❌ আপনি ব্যানড")

    handle_referral(uid, message)

    m = types.InlineKeyboardMarkup()

    for link in CHANNEL_LINKS:
        m.add(types.InlineKeyboardButton("🔒 প্রাইভেট চ্যানেল জয়েন", url=link))

    m.add(types.InlineKeyboardButton(
        "📢 পাবলিক চ্যানেল জয়েন",
        url=f"https://t.me/{PUBLIC_CHANNEL.replace('@','')}"
    ))

    m.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))

    bot.send_message(uid, "সব চ্যানেল জয়েন করে VERIFY চাপুন", reply_markup=m)

# ================= VERIFY =================
@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify_user(c):
    uid = c.message.chat.id

    if not check_public_join(uid):
        return bot.answer_callback_query(c.id, "আগে চ্যানেল জয়েন করুন!", show_alert=True)

    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))
        conn.commit()

    main_menu(uid)

# ================= MAIN MENU =================
def main_menu(uid):
    ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("👥 রেফারেল", "📊 স্ট্যাটাস")
    m.add("📱 APK নিন", "🎓 কোর্স নিন")
    m.add("📞 এডমিনে যোগাযোগ")

    bot.send_message(uid, f"স্বাগতম!\n\nআপনার লিংক:\n{ref_link}", reply_markup=m)

# ================= ADMIN PANEL =================
@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.chat.id not in ADMINS:
        return bot.send_message(message.chat.id, "❌ আপনি এডমিন না")

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("➕ APK Add", "➕ Course Add")
    m.add("📊 Stats", "🚫 Ban User", "✅ Unban User")
    m.add("📢 Broadcast")
    m.add("❌ Exit Admin")

    bot.send_message(message.chat.id, "⚙️ Admin Panel", reply_markup=m)

# ================= USER + ADMIN =================
@bot.message_handler(func=lambda m: True)
def buttons(message):
    uid = message.chat.id
    text = message.text

    # USER
    if text == "👥 রেফারেল":
        bot.send_message(uid, f"https://t.me/{BOT_USERNAME}?start={uid}")

    elif text == "📊 স্ট্যাটাস":
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
        bot.send_message(uid, f"Referral: {cursor.fetchone()[0]}")

    elif text == "📱 APK নিন":
        show_apk(uid)

    elif text == "🎓 কোর্স নিন":
        show_course(uid)

    elif text == "📞 এডমিনে যোগাযোগ":
        bot.send_message(uid, "Admin: @jiolinhacker")

    # ADMIN
    elif text == "➕ APK Add" and uid in ADMINS:
        bot.send_message(uid, "APK file দিন বা লিখুন:\nname | link")
        bot.register_next_step_handler(message, apk_add)

    elif text == "➕ Course Add" and uid in ADMINS:
        bot.send_message(uid, "name | link")
        bot.register_next_step_handler(message, save_course)

    elif text == "📊 Stats" and uid in ADMINS:
        cursor.execute("SELECT COUNT(*) FROM users")
        bot.send_message(uid, f"Total Users: {cursor.fetchone()[0]}")

    elif text == "🚫 Ban User" and uid in ADMINS:
        bot.send_message(uid, "User ID দিন")
        bot.register_next_step_handler(message, ban_user)

    elif text == "✅ Unban User" and uid in ADMINS:
        bot.send_message(uid, "User ID দিন")
        bot.register_next_step_handler(message, unban_user)

    elif text == "📢 Broadcast" and uid in ADMINS:
        bot.send_message(uid, "Message দিন")
        bot.register_next_step_handler(message, broadcast)

    elif text == "❌ Exit Admin":
        main_menu(uid)

# ================= APK ADD =================
def apk_add(message):
    uid = message.chat.id

    if message.document:
        cursor.execute("INSERT INTO apk (name,file_id) VALUES (?,?)",
                       (message.caption, message.document.file_id))
        conn.commit()
        bot.send_message(uid, "APK Saved ✅")
    else:
        try:
            name, link = message.text.split("|")
            cursor.execute("INSERT INTO apk (name,link) VALUES (?,?)",
                           (name.strip(), link.strip()))
            conn.commit()
            bot.send_message(uid, "APK Link Saved ✅")
        except:
            bot.send_message(uid, "Wrong format ❌")

# ================= COURSE =================
def save_course(message):
    try:
        name, link = message.text.split("|")
        cursor.execute("INSERT INTO courses (name,link) VALUES (?,?)",
                       (name.strip(), link.strip()))
        conn.commit()
        bot.send_message(message.chat.id, "Saved ✅")
    except:
        bot.send_message(message.chat.id, "Error ❌")

# ================= BAN =================
def ban_user(message):
    cursor.execute("UPDATE users SET banned=1 WHERE user_id=?", (int(message.text),))
    conn.commit()
    bot.send_message(message.chat.id, "Banned ✅")

def unban_user(message):
    cursor.execute("UPDATE users SET banned=0 WHERE user_id=?", (int(message.text),))
    conn.commit()
    bot.send_message(message.chat.id, "Unbanned ✅")

# ================= BROADCAST =================
def broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    for u in cursor.fetchall():
        try:
            bot.send_message(u[0], message.text)
        except:
            pass
    bot.send_message(message.chat.id, "Done ✅")

# ================= APK =================
def show_apk(uid):
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone()[0] < 2:
        return bot.send_message(uid, "Need 2 referrals ❌")

    cursor.execute("SELECT id,name FROM apk")
    m = types.InlineKeyboardMarkup()
    for i,n in cursor.fetchall():
        m.add(types.InlineKeyboardButton(n, callback_data=f"apk_{i}"))

    bot.send_message(uid, "Select APK", reply_markup=m)

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
        return bot.send_message(uid, "Need 5 referrals ❌")

    cursor.execute("SELECT id,name FROM courses")
    m = types.InlineKeyboardMarkup()
    for i,n in cursor.fetchall():
        m.add(types.InlineKeyboardButton(n, callback_data=f"course_{i}"))

    bot.send_message(uid, "Select Course", reply_markup=m)

@bot.callback_query_handler(func=lambda c: c.data.startswith("course_"))
def get_course(c):
    cursor.execute("SELECT name,link FROM courses WHERE id=?", (int(c.data.split("_")[1]),))
    n,l = cursor.fetchone()
    bot.send_message(c.message.chat.id, f"{n}\n{l}")

# ================= RUN =================
print("BOT RUNNING...")
bot.infinity_polling()