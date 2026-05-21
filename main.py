import os
import telebot
from telebot import types
from flask import Flask, request
from pymongo import MongoClient
from datetime import datetime
import re
import random
import string

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
MONGO_URI = os.getenv('MONGO_URI')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'SIZNING_BOT_USERNAME')  # Bot username

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

# =============== YORDAMCHI FUNKSIYALAR ===============
def generate_code(length=6):
    """Anime uchun unikal kod generatsiya qilish"""
    chars = string.digits  # Faqat raqamlar
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if animes_collection and not animes_collection.find_one({'code': code}):
            return code

def format_slug(text):
    """Anime nomini slug formatiga o'tkazish"""
    # Belgilarni olib tashlash
    text = text.replace("'", "").replace('"', "").replace("`", "").replace("ʻ", "")
    # Bo'shliqlarni - bilan almashtirish
    text = re.sub(r'\s+', '-', text.strip())
    return text

# =============== ASOSIY TUGMALAR ===============
def asosiy_tugmalar(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🗄️ Boshqarish"))
    return markup

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
    user_id = message.from_user.id
    
    # Deep link orqali kelgan anime kodini tekshirish
    args = message.text.split()
    if len(args) > 1:
        slug = args[1]
        anime = animes_collection.find_one({'slug': slug}) if animes_collection else None
        if anime:
            bot.send_message(
                message.chat.id,
                f"🎬 *{anime['name']}*\n\n"
                f"📝 {anime.get('description', 'Tavsif mavjud emas')}\n\n"
                f"🎥 Anime hozircha mavjud emas. Tez orada qo'shiladi!",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(message.chat.id, "❌ Anime topilmadi!", reply_markup=asosiy_tugmalar(user_id))
        return
    
    # Oddiy /start
    bot.send_message(
        message.chat.id,
        f"🎬 Assalomu alaykum, {message.from_user.first_name}!\nAnime Yuklovchi Botga xush kelibsiz!",
        reply_markup=asosiy_tugmalar(user_id)
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "📚 Yordam kerakmi?", reply_markup=asosiy_tugmalar(user_id))

# =============== BOSHQARISH ===============
@bot.message_handler(func=lambda m: m.text == "🗄️ Boshqarish")
def boshqarish(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👨‍💻 Admin Panel", reply_markup=admin_tugmalari())
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

@bot.message_handler(func=lambda m: m.text == "🔙 Chiqish")
def chiqish(message):
    bot.send_message(message.chat.id, "Asosiy menyu", reply_markup=asosiy_tugmalar(message.from_user.id))

# =============== ANIME QO'SHISH ===============
@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def anime_qoshish_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz!")
        return
    
    msg = bot.send_message(message.chat.id, "📝 *Anime nomini kiriting:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, anime_nomini_qabul_qilish)

def anime_nomini_qabul_qilish(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    anime_name = message.text.strip()
    slug = format_slug(anime_name)
    code = generate_code()
    
    # MongoDB'ga saqlash
    if animes_collection:
        animes_collection.insert_one({
            'name': anime_name,
            'slug': slug,
            'code': code,
            'added_by': ADMIN_ID,
            'added_date': datetime.now(),
            'seasons': [],
            'movies': [],
            'episodes': []
        })
    
    # Havola yaratish
    bot_link = f"https://t.me/{BOT_USERNAME}?start={slug}"
    
    response = f"""
✅ *Anime qo'shildi!*

🔑 Kod: `{code}`
📺 Nomi: *{anime_name}*
🔗 Havola: {bot_link}

📌 Bu kodni faqat admin bilishi kerak!
"""
    bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=admin_tugmalari())

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
