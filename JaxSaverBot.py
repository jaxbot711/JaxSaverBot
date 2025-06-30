import telebot
from flask import Flask, request
import re
import os
from yt_dlp import YoutubeDL
import threading
import time
import requests

API_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = '@JexMemes'
CHANNEL_LINK = 'https://t.me/JexMemes'
WEBHOOK_URL = 'https://jaxsaverbot.onrender.com/webhook'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# إنشاء مجلد التنزيل إذا لم يكن موجوداً
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# تحميل الفيديو باستخدام yt-dlp مع الكوكيز
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'cookiefile': 'cookies.txt',
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[خطأ في التحميل] {e}")
        return None

# التحقق من الاشتراك في القناة
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status != 'left'
    except Exception as e:
        print(f"[خطأ التحقق من الاشتراك] {e}")
        return False

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
        bot.reply_to(message, "❌ الرابط غير مدعوم. أرسل رابط من TikTok أو Instagram أو Twitter فقط_
