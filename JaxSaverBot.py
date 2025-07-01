import telebot
from flask import Flask, request
import re
import os
from yt_dlp import YoutubeDL
import threading
import time
import sqlite3
import requests

# إعدادات البوت
API_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = '@JexMemes'
CHANNEL_LINK = 'https://t.me/JexMemes '
WEBHOOK_URL = 'https://jaxsaverbot.onrender.com/webhook '

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# إنشاء مجلد التنزيلات إذا لم يكن موجود
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# ====== DATABASE SETUP ======
DB_NAME = 'bot.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      user_id INTEGER PRIMARY KEY,
                      username TEXT,
                      first_seen TEXT,
                      downloads INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_user(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, first_seen) VALUES (?, ?, ?)",
                       (user_id, username, now))
    conn.commit()
    conn.close()

def increment_download(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT downloads FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# ====== END DATABASE ======

# التحقق من الاشتراك في القناة
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"[Error checking subscription] {e}")
        return False

# تحميل الفيديو باستخدام yt-dlp
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'mp4',
            'quiet': True,
        }

        # إذا كان ملف الكوكيز موجود، أضفه
        if os.path.exists("cookies.txt"):
            ydl_opts['cookiefile'] = "cookies.txt"

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[Download error] {e}")
        return None

# تعبيرات منتظمة للتعرف على الروابط
tiktok_regex = re.compile(r'https?://(www\.)?(vt\.)?tiktok\.com/.+')
instagram_regex = re.compile(r'https?://(www\.)?instagram\.com/.+')
twitter_regex = re.compile(r'https?://(www\.)?(twitter\.com|x\.com)/.+')

# ===== HANDLERS =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message)
    bot.reply_to(message, f"""👋 أهلاً بك في بوت التحميل!

📥 أرسل رابط فيديو من:
• TikTok
• Instagram
• Twitter (X)

🔒 لاستخدام البوت، يجب الاشتراك في القناة:
{CHANNEL_LINK}
""")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.reply_to(message, f"⚠️ يجب الاشتراك أولاً في القناة:\n{CHANNEL_LINK}")
        return

    count = get_stats(user_id)
    bot.reply_to(message, f"📊 لقد قمت بتنزيل {count} فيديو حتى الآن.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_subscribed(user_id):
        bot.reply_to(message, f"⚠️ يجب الاشتراك أولاً في القناة:\n{CHANNEL_LINK}")
        return

    if tiktok_regex.match(text):
        bot.reply_to(message, "📥 جارٍ تحميل الفيديو من TikTok...")
    elif instagram_regex.match(text):
        bot.reply_to(message, "📥 جارٍ تحميل الفيديو من Instagram...")
    elif twitter_regex.match(text):
        bot.reply_to(message, "📥 جارٍ تحميل الفيديو من Twitter (X)...")
    else:
        bot.reply_to(message, "❌ الرابط غير مدعوم. أرسل رابط من TikTok أو Instagram أو Twitter فقط.")
        return

    file_path = download_video(text)
    if file_path:
        try:
            with open(file_path, 'rb') as video:
                bot.send_document(message.chat.id, video)
            os.remove(file_path)
            increment_download(user_id)
        except Exception as e:
            print(f"[Send error] {e}")
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إرسال الفيديو.")
    else:
        bot.send_message(message.chat.id, "❌ فشل في تحميل الفيديو. تأكد من صحة الرابط أو جرب لاحقاً.")

# إعداد Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return 'Webhook has been set!'

# منع Render من النوم
def keep_alive():
    while True:
        try:
            requests.get("https://jaxsaverbot.onrender.com ")
        except Exception as e:
            print("Ping error:", e)
        time.sleep(300)

threading.Thread(target=keep_alive).start()

if __name__ == '__main__':
    init_db()  # تهيئة قاعدة البيانات عند تشغيل السيرفر
    app.run(host='0.0.0.0', port=10000)
