import telebot
from flask import Flask, request
import re
import os
from yt_dlp import YoutubeDL
import threading
import time
import requests  # <-- جديد

API_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = '@JexMemes'
CHANNEL_LINK = 'https://t.me/JexMemes'
WEBHOOK_URL = 'https://jaxsaverbot.onrender.com/webhook'  # ✅ تم التعديل هنا

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# التأكد من مجلد التنزيل
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# التحقق من الاشتراك في القناة
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status != 'left'
    except Exception as e:
        print(f"[خطأ في التحقق من الاشتراك] {e}")
        return False

# تحميل الفيديو (مُحدّث لإضافة ملف الكوكيز)
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'cookies': 'cookies.txt',  # ← استخدم ملف الكوكيز
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[خطأ في التحميل] {e}")
        return None

# التعبيرات العادية
tiktok_regex = re.compile(r'https?://(www\.)?(vt\.)?tiktok\.com/.+')
instagram_regex = re.compile(r'https?://(www\.)?instagram\.com/.+')
twitter_regex = re.compile(r'https?://(www\.)?(twitter\.com|x\.com)/.+')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"""👋 أهلاً بك في بوت التحميل!

📥 أرسل رابط فيديو من:
• TikTok
• Instagram
• Twitter (X)

🔒 لاستخدام البوت، يجب الاشتراك في القناة:
{CHANNEL_LINK}
""")


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
        bot.reply_to(message, "❌ الرابط غير مدعوم. يرجى إرسال رابط من TikTok أو Instagram أو Twitter (X) فقط.")
        return

    file_path = download_video(text)
    if file_path:
        try:
            with open(file_path, 'rb') as video:
                bot.send_document(message.chat.id, video)
            os.remove(file_path)
        except Exception as e:
            print(f"[خطأ أثناء الإرسال] {e}")
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إرسال الفيديو.")
    else:
        bot.send_message(message.chat.id, "❌ فشل في تحميل الفيديو. تأكد من صحة الرابط.")

# نقاط الاتصال للويب هوك
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

# 🔄 وظيفة منع النوم
def keep_alive():
    while True:
        try:
            requests.get("https://jaxsaverbot.onrender.com")
        except Exception as e:
            print("Ping error:", e)
        time.sleep(300)  # كل 5 دقائق

threading.Thread(target=keep_alive).start()

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)