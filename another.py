import telebot
import requests
import subprocess
import logging
import time
import os
from playwright.sync_api import sync_playwright

# ==============================
# Logging Configuration
# ==============================
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==============================
# Bot Configuration
# ==============================
API_TOKEN = '7270490911:AAER3DaUlCoddCxkUILKRsuCcX5OBhDEelg'
bot = telebot.TeleBot(API_TOKEN)

# ==============================
# Welcome Message
# ==============================
WELCOME_MESSAGE = """
👋 Welcome to Pinterest Video Downloader Bot! 🎥

Send a Pinterest video link, and I'll download it for you in the best quality! 🔥

⚡ Fast & Reliable
📥 Direct Download
🛠️ 24/7 Auto-Fix on Errors
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, WELCOME_MESSAGE)

# ==============================
# Function to Extract M3U8 URL
# ==============================
def get_m3u8_url(video_url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            m3u8_url = None

            def intercept_response(response):
                nonlocal m3u8_url
                if ".m3u8" in response.url:
                    m3u8_url = response.url  # Capture the first .m3u8 link

            page.on("response", intercept_response)
            page.goto(video_url, timeout=60000)
            time.sleep(5)  # Wait for responses to load

            browser.close()
            return m3u8_url
    except Exception as e:
        logging.error(f"Error extracting m3u8: {e}")
        return None


# ==============================
# Function to Download Video
# ==============================
def download_video(m3u8_url, output_filename='video.mp4'):
    try:
        command = [
            "ffmpeg", "-headers", "User-Agent: Mozilla/5.0", "-i", m3u8_url,
            "-c", "copy", "-y", output_filename
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(output_filename)
    except Exception as e:
        logging.error(f"FFmpeg error: {e}")
        return False

# ==============================
# Bot Handler for Video Download
# ==============================
@bot.message_handler(func=lambda message: True)
def handle_pinterest_url(message):
    url = message.text.strip()
    
    bot_msg = bot.send_message(message.chat.id, "🔍 Fetching video, please wait...")
    
    m3u8_url = get_m3u8_url(url)
    if not m3u8_url:
        bot.edit_message_text("❌ Unable to extract video. Pinterest might be blocking requests.", message.chat.id, bot_msg.message_id)
        return
    
    bot.edit_message_text("🎥 Downloading video in best quality...", message.chat.id, bot_msg.message_id)
    
    if download_video(m3u8_url):
        with open("video.mp4", "rb") as video:
            try:
                bot.send_video(message.chat.id, video)
                bot.edit_message_text("✅ Video sent successfully!", message.chat.id, bot_msg.message_id)
            except Exception as e:
                logging.error(f"Error sending video: {e}")
                bot.edit_message_text("⚠️ Facing some issues. Will fix within 24 hours!", message.chat.id, bot_msg.message_id)
        os.remove("video.mp4")
    else:
        bot.edit_message_text("❌ Failed to download video.", message.chat.id, bot_msg.message_id)

# ==============================
# Start the Bot with Auto-Restart
# ==============================
if __name__ == "__main__":
    while True:
        try:
            logging.info("Bot is starting...")
            bot.infinity_polling()
        except Exception as e:
            logging.error(f"Bot crashed: {e}")
            time.sleep(5)
