import telebot
import requests
import json
import os
from flask import Flask
from threading import Thread
from telebot import types

# ===================================================
# ⚙️ কনফিগারেশন ভেরিয়েবল (আপনার দেওয়া তথ্য অনুযায়ী সেট করা)
# ===================================================
BOT_TOKEN = "8335679806:AAHXv7DzzaKzUnTmHf49835pFQX4ZCYPOHM"       
ADMIN_API_KEY = "akashdeveloper"  
WEBSITE_NAME = "UrlBotSot"
WEBSITE_URL = "https://urlbotsot.vercel.app/"
API_ENDPOINT = "https://urlbotsot.vercel.app/api"
DATA_FILE = "database.json"
# ===================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# --- রেন্ডারে বট সচল রাখার জন্য ওয়েব সার্ভার (Keep-alive) ---
@app.route('/')
def home():
    return "Bot is alive and running!"

def run_server():
    # Render সাধারণত 8080 পোর্টে রান করে
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- ডাটাবেস ম্যানেজমেন্ট ---
def get_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
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

# --- কমান্ড ও বাটন হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.chat.id)
    db = get_db()
    
    if user_id not in db:
        db[user_id] = {"api_key": None}
        save_db(db)
    
    welcome_msg = (f"আসসালামু আলাইকুম {message.from_user.first_name}!\n\n"
                   f"স্বাগতম **{WEBSITE_NAME}** এর অফিসিয়াল বটে।\n"
                   f"আপনি চাইলে নিজের API Key সেট করতে পারেন, অথবা সরাসরি যেকোনো লিঙ্ক পাঠিয়ে শর্ট করতে পারেন।")
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📝 Details")
def show_details(message):
    user_id = str(message.chat.id)
    db = get_db()
    user_api = db.get(user_id, {}).get("api_key")
    
    current_active_api = user_api if user_api else f"{ADMIN_API_KEY} (Default)"
    
    info_text = (
        f"📝 **আপনার ইনফরমেশন:**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 নাম: {message.from_user.first_name}\n"
        f"🆔 আইডি: `{user_id}`\n"
        f"🔑 এপিআই: `{current_active_api}`\n"
        f"🌐 সাইট: {WEBSITE_URL}\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda message: message.text == "⚙️ Set API")
def ask_api(message):
    msg = bot.send_message(message.chat.id, "আপনার পার্সোনাল API Key-টি নিচে লিখে পাঠান:")
    bot.register_next_step_handler(msg, update_user_api)

def update_user_api(message):
    user_id = str(message.chat.id)
    new_api = message.text.strip()
    
    if len(new_api) < 5:
        bot.reply_to(message, "❌ ভুল API! দয়া করে সঠিক কি (Key) দিন।")
        return

    db = get_db()
    db[user_id] = {"api_key": new_api}
    save_db(db)
    bot.send_message(message.chat.id, "✅ আপনার API Key সফলভাবে আপডেট করা হয়েছে!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🔗 Shorten Link")
def instruction(message):
    bot.send_message(message.chat.id, "লিঙ্ক শর্ট করতে সরাসরি আপনার লিঙ্কটি (URL) এখানে পাঠান।")

# --- অটোমেটিক লিঙ্ক শর্ট করার হ্যান্ডলার (কমান্ড ছাড়া) ---
@bot.message_handler(func=lambda message: True)
def auto_process_shorten(message):
    url = message.text.strip()
    
    # যদি মেসেজটি লিঙ্ক (http) দিয়ে শুরু হয় তবেই কাজ করবে
    if url.startswith("http"):
        user_id = str(message.chat.id)
        db = get_db()
        user_api = db.get(user_id, {}).get("api_key")
        
        # ইউজার এপিআই না থাকলে আপনার মাস্টার এপিআই ব্যবহার হবে
        final_api = user_api if user_api else ADMIN_API_KEY

        bot.send_chat_action(message.chat.id, 'typing')

        try:
            # সাইটের API কল
            params = {'api': final_api, 'url': url}
            res = requests.get(API_ENDPOINT, params=params, timeout=12)
            data = res.json()

            # লিঙ্ক খুঁজে বের করা
            short_link = data.get('shortenedUrl') or data.get('shortened_url') or data.get('link')

            if short_link:
                bot.send_message(message.chat.id, f"✅ **লিঙ্ক জেনারেট হয়েছে!**\n\n🔗 {short_link}")
            else:
                bot.reply_to(message, "❌ লিঙ্ক শর্ট করা যায়নি। আপনার এপিআই সঠিক আছে কি না চেক করুন।")
        except Exception as e:
            bot.reply_to(message, "⚠️ সার্ভারে সমস্যা হচ্ছে। কিছুক্ষণ পর আবার চেষ্টা করুন।")
    else:
        # যদি লিঙ্ক না হয় এবং বাটন টেক্সট না হয়, তবে কোনো মেসেজ দিবে না বা চাইলে হেল্প মেসেজ দিতে পারেন।
        pass

if __name__ == "__main__":
    keep_alive() # রেন্ডারের ওয়েব সার্ভার চালু
    print("Bot is started and running...")
    bot.infinity_polling() # বট সচল রাখবে
