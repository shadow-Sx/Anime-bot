import os
import telebot
from telebot import types
from flask import Flask, request
from pymongo import MongoClient
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
MONGO_URI = os.getenv('MONGO_URI')

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['anime_bot']
    print("✅ MongoDB ulandi!")
except Exception as e:
    print(f"❌ MongoDB: {e}")

@app.route('/')
def home():
    return "🤖 Bot ishlamoqda!"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🗄️ Boshqarish"))
    
    bot.send_message(message.chat.id, f"Salom {message.from_user.first_name}! 🎬", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🗄️ Boshqarish")
def boshqarish(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("➕ Anime qo'shish"))
        markup.add(types.KeyboardButton("🔙 Chiqish"))
        bot.send_message(message.chat.id, "👨‍💻 Admin Panel", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 Chiqish")
def chiqish(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🗄️ Boshqarish"))
    bot.send_message(message.chat.id, "Asosiy menyu", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def anime_qoshish(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "📤 Anime qo'shish funksiyasi tez orada!")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 403

if __name__ == "__main__":
    bot.remove_webhook()
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        bot.set_webhook(url=f"{render_url}/webhook")
        print(f"✅ Webhook: {render_url}/webhook")
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
