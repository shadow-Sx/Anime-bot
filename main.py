import os
import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime
from flask import Flask
import threading
import time

# =============== ENVIRONMENT VARIABLES ===============
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
MONGO_URI = os.getenv('MONGO_URI')

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")
if not MONGO_URI:
    raise ValueError("MONGO_URI topilmadi!")

# =============== FLASK (port ochish uchun) ===============
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot ishlamoqda!"

# =============== BOT ===============
bot = telebot.TeleBot(TOKEN)

# =============== MONGODB ===============
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    client.server_info()
    db = client['anime_bot']
    users_collection = db['users']
    animes_collection = db['animes']
    print("✅ MongoDB ga muvaffaqiyatli ulandi!")
except Exception as e:
    print(f"❌ MongoDB xatosi: {e}")
    db = None
    users_collection = None
    animes_collection = None

# =============== FOYDALANUVCHINI SAQLASH ===============
def save_user(message):
    if users_collection:
        try:
            user_id = message.from_user.id
            if not users_collection.find_one({'user_id': user_id}):
                users_collection.insert_one({
                    'user_id': user_id,
                    'first_name': message.from_user.first_name,
                    'username': message.from_user.username,
                    'joined_date': datetime.now(),
                    'last_active': datetime.now()
                })
            else:
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'last_active': datetime.now()}}
                )
        except:
            pass

# =============== ASOSIY TUGMALAR ===============
def asosiy_tugmalar(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("ℹ️ Yordam")
    markup.add(btn1)
    
    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("👨‍💻 Admin Panel")
        markup.add(btn_admin)
    
    return markup

# =============== START ===============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message)
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_text = f"""
🎬 Assalomu alaykum, {user_name}!

Anime Yuklovchi Botga xush kelibsiz!
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=asosiy_tugmalar(user_id))

# =============== HELP ===============
@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "📚 Yordam kerakmi?", reply_markup=asosiy_tugmalar(user_id))

# =============== TUGMALAR ===============
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    save_user(message)
    user_id = message.from_user.id
    
    if message.text == "👨‍💻 Admin Panel":
        if user_id == ADMIN_ID:
            admin_panel(message)
        else:
            bot.reply_to(message, "❌ Siz admin emassiz!")
    
    elif message.text == "ℹ️ Yordam":
        help_text = """
📚 Yordam:

/start - Botni ishga tushirish
/help - Yordam olish

Tez orada yangi funksiyalar qo'shiladi!
        """
        bot.reply_to(message, help_text)
    
    elif message.text == "🔙 Orqaga":
        bot.send_message(message.chat.id, "Asosiy menyu", reply_markup=asosiy_tugmalar(user_id))
    
    elif message.text == "➕ Anime qo'shish":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "📤 Anime qo'shish funksiyasi tez orada!")
    
    elif message.text == "📋 Anime ro'yxati":
        if user_id == ADMIN_ID:
            bot.reply_to(message, "📋 Anime ro'yxati tez orada!")
    
    elif message.text == "👥 Foydalanuvchilar":
        if user_id == ADMIN_ID:
            if users_collection:
                count = users_collection.count_documents({})
                bot.reply_to(message, f"👥 Jami foydalanuvchilar: {count} ta")
            else:
                bot.reply_to(message, "❌ Ma'lumotlar bazasiga ulanishda xatolik!")
    
    else:
        bot.reply_to(message, "❌ Tushunmadim", reply_markup=asosiy_tugmalar(user_id))

# =============== ADMIN PANEL ===============
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("➕ Anime qo'shish")
    btn2 = types.KeyboardButton("📋 Anime ro'yxati")
    btn3 = types.KeyboardButton("👥 Foydalanuvchilar")
    btn4 = types.KeyboardButton("🔙 Orqaga")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    
    users_count = users_collection.count_documents({}) if users_collection else 0
    animes_count = animes_collection.count_documents({}) if animes_collection else 0
    
    admin_text = f"""
👨‍💻 Admin Panel

📊 Statistika:
👥 Foydalanuvchilar: {users_count} ta
🎬 Animelar: {animes_count} ta
"""
    bot.send_message(message.chat.id, admin_text, reply_markup=markup)

# =============== BOTNI ISHGA TUSHIRISH ===============
def start_bot():
    print("🚀 Bot polling boshlandi...")
    bot.remove_webhook()  # Webhookni o'chiramiz
    time.sleep(1)  # 1 soniya kutish
    bot.infinity_polling()

# =============== MAIN ===============
if __name__ == "__main__":
    # Botni alohida thread'da ishga tushirish
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True  # Asosiy dastur yopilsa, bot ham yopiladi
    bot_thread.start()
    
    # Flask serverni ishga tushirish
    port = int(os.getenv('PORT', 10000))
    print(f"🌐 Flask server ishga tushdi: port {port}")
    app.run(host='0.0.0.0', port=port)
