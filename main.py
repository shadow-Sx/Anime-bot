import os
import telebot
from telebot import types
from pymongo import MongoClient
from datetime import datetime

# =============== ENVIRONMENT VARIABLES ===============
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
MONGO_URI = os.getenv('MONGO_URI')  # MongoDB connection string

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")
if not MONGO_URI:
    raise ValueError("MONGO_URI topilmadi!")

bot = telebot.TeleBot(TOKEN)

# =============== MONGODB ULANISH ===============
try:
    client = MongoClient(MONGO_URI)
    db = client['anime_bot']  # Database nomi
    users_collection = db['users']  # Foydalanuvchilar
    animes_collection = db['animes']  # Animelar
    print("✅ MongoDB ga muvaffaqiyatli ulandi!")
except Exception as e:
    print(f"❌ MongoDB ulanishda xatolik: {e}")

# =============== FOYDALANUVCHINI SAQLASH ===============
def save_user(message):
    user_id = message.from_user.id
    user_data = {
        'user_id': user_id,
        'first_name': message.from_user.first_name,
        'username': message.from_user.username,
        'joined_date': datetime.now(),
        'last_active': datetime.now()
    }
    
    # Agar foydalanuvchi bo'lmasa, qo'shish
    if not users_collection.find_one({'user_id': user_id}):
        users_collection.insert_one(user_data)
        print(f"👤 Yangi foydalanuvchi: {message.from_user.first_name}")
    else:
        # Oxirgi faollikni yangilash
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_active': datetime.now()}}
        )

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
    save_user(message)  # Foydalanuvchini saqlash
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

# =============== TUGMALAR BOSILGANDA ===============
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    save_user(message)  # Har safar faollikni yangilash
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
    
    # Statistikani ko'rsatish
    users_count = users_collection.count_documents({})
    animes_count = animes_collection.count_documents({})
    
    admin_text = f"""
👨‍💻 Admin Panel

📊 Statistika:
👥 Foydalanuvchilar: {users_count} ta
🎬 Animelar: {animes_count} ta
"""
    bot.send_message(message.chat.id, admin_text, reply_markup=markup)

# =============== BOTNI ISHGA TUSHIRISH ===============
if __name__ == "__main__":
    print("🚀 Bot ishga tushdi...")
    bot.infinity_polling()
