import telebot
import requests
import json
import os
from flask import Flask
from threading import Thread
from telebot import types

# ===================================================
# ⚙️ ভেরিএবল কনফিগারেশন (আপনার তথ্য এখানে দিন)
# ===================================================
BOT_TOKEN = "আপনার_বট_টোকেন_এখানে_দিন"
ADMIN_API_KEY = "আপনার_মাস্টার_API_KEY_এখানে_দিন" 
WEBSITE_NAME = "URL Shortener" 
WEBSITE_URL = "https://urlbotsot.vercel.app/"
API_ENDPOINT = "https://urlbotsot.vercel.app/api"
DATA_FILE = "database.json"
# ===================================================

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask('')

# --- রেন্ডারে বট সচল রাখার জন্য ওয়েব সার্ভার ---
@server.route('/')
def home():
    return "Bot is Online!"

def run_server():
    # রেন্ডার সাধারণত ৮০৮০ পোর্ট ব্যবহার করে
    server.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- ডাটাবেস ম্যানেজমেন্ট ---
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- বাটন মেনু ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔗 Shorten Link"), types.KeyboardButton("⚙️ Set API"))
    markup.add(types.KeyboardButton("📝 Details"))
    return markup

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.chat.id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {"api_key": None}
        save_db(db)
    
    msg = (f"আসসালামু আলাইকুম {message.from_user.first_name}!\n\n"
           f"এটি **{WEBSITE_NAME}** এর অফিসিয়াল বট।\n"
           f"আপনি নিজের API সেট না করা পর্যন্ত আমাদের ডিফল্ট API দিয়ে সব কাজ হবে।")
    bot.send_message(user_id, msg, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📝 Details")
def show_details(message):
    user_id = str(message.chat.id)
    db = load_db()
    user_api = db.get(user_id, {}).get("api_key")
    
    current_api = user_api if user_api else f"{ADMIN_API_KEY} (Default)"
    
    detail_text = (
        f"📝 **ইউজার ডিটেইলস:**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 নাম: {message.from_user.first_name}\n"
        f"🆔 আইডি: `{user_id}`\n"
        f"🔑 সেট করা API: `{current_api}`\n"
        f"🌐 সাইট ইউআরএল: {WEBSITE_URL}\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(user_id, detail_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda message: message.text == "⚙️ Set API")
def set_api_step(message):
    msg = bot.send_message(message.chat.id, "আপনার পার্সোনাল API Key-টি লিখে পাঠান:")
    bot.register_next_step_handler(msg, save_user_api)

def save_user_api(message):
    user_id = str(message.chat.id)
    new_api = message.text.strip()
    
    if len(new_api) < 5:
        bot.reply_to(message, "❌ ভুল API Key! দয়া করে সঠিক কি (Key) দিন।")
        return

    db = load_db()
    db[user_id] = {"api_key": new_api}
    save_db(db)
    bot.send_message(user_id, "✅ আপনার API Key সফলভাবে আপডেট করা হয়েছে!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🔗 Shorten Link")
def instruction(message):
    bot.send_message(message.chat.id, "লিংকটি (URL) পাঠান যা শর্ট করতে চান।")

@bot.message_handler(func=lambda message: True)
def auto_shorten(message):
    url = message.text.strip()
    if not url.startswith("http"): return # মেনু বাটনগুলোকে ইগনোর করবে

    user_id = str(message.chat.id)
    db = load_db()
    user_api = db.get(user_id, {}).get("api_key")
    
    # ইউজার এপিআই না থাকলে এডমিন এপিআই ব্যবহার হবে
    final_api = user_api if user_api else ADMIN_API_KEY

    bot.send_chat_action(user_id, 'typing')

    try:
        params = {'api': final_api, 'url': url}
        response = requests.get(API_ENDPOINT, params=params, timeout=15)
        res_data = response.json()

        short_url = res_data.get('shortenedUrl') or res_data.get('shortened_url') or res_data.get('link')
        
        if short_url:
            bot.send_message(user_id, f"✅ **লিঙ্ক শর্ট করা হয়েছে!**\n\n🔗 {short_url}")
        else:
            bot.reply_to(message, "❌ শর্ট লিঙ্ক পাওয়া যায়নি। আপনার API কি চেক করুন।")
    except Exception as e:
        bot.reply_to(message, "⚠️ সার্ভারে সমস্যা হচ্ছে। পরে চেষ্টা করুন।")

# --- রান বট ---
if __name__ == "__main__":
    keep_alive() # ওয়েব সার্ভার চালু করা
    print("Bot is Starting...")
    bot.infinity_polling() # বট সচল রাখবে
