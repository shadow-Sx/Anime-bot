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

# =============== MONGODB ===============
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['anime_bot']
    users_collection = db['users']
    animes_collection = db['animes']
    print("✅ MongoDB ulandi!")
except Exception as e:
    print(f"❌ MongoDB: {e}")
    users_collection = None
    animes_collection = None

# =============== FOYDALANUVCHI SAQLASH ===============
def save_user(message):
    if users_collection:
        try:
            user_id = message.from_user.id
            if not users_collection.find_one({'user_id': user_id}):
                users_collection.insert_one({
                    'user_id': user_id,
                    'first_name': message.from_user.first_name,
                    'username': message.from_user.username,
                    'joined_date': datetime.now()
                })
        except:
            pass

# =============== ASOSIY TUGMALAR ===============
def asosiy_tugmalar(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🗄️ Boshqarish"))
    
    return markup

# =============== ADMIN TUGMALARI ===============
def admin_tugmalari():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("➕ Anime qo'shish"))
    markup.add(types.KeyboardButton("🔙 Chiqish"))
    return markup

# =============== FLASK ===============
@app.route('/')
def home():
    return "🤖 Bot ishlamoqda!"

# =============== HANDLERLAR ===============
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message)
    user_id = message.from_user.id
    
    bot.send_message(
        message.chat.id,
        f"🎬 Assalomu alaykum, {message.from_user.first_name}!\nAnime Yuklovchi Botga xush kelibsiz!",
        reply_markup=asosiy_tugmalar(user_id)
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "📚 Yordam kerakmi?", reply_markup=asosiy_tugmalar(user_id))

# =============== TUGMALAR ===============
@bot.message_handler(func=lambda m: m.text == "🗄️ Boshqarish")
def boshqarish(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "👨‍💻 Admin Panelga xush kelibsiz!",
            reply_markup=admin_tugmalari()
        )
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def anime_qoshish(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "📤 Anime qo'shish uchun quyidagi ma'lumotlarni yuboring:\n\n"
            "Nomi, kod, tavsif va video fayl\n\n"
            "Bu funksiya tez orada to'liq ishlaydi!"
        )
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

@bot.message_handler(func=lambda m: m.text == "🔙 Chiqish")
def chiqish(message):
    bot.send_message(
        message.chat.id,
        "Asosiy menyuga qaytdingiz",
        reply_markup=asosiy_tugmalar(message.from_user.id)
    )

# =============== WEBHOOK ===============
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 403

# =============== ISHGA TUSHIRISH ===============
if __name__ == "__main__":
    bot.remove_webhook()
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        bot.set_webhook(url=f"{render_url}/webhook")
        print(f"✅ Webhook: {render_url}/webhook")
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
