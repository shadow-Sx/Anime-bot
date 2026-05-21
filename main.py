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
BOT_USERNAME = os.getenv('BOT_USERNAME', 'SIZNING_BOT_USERNAME')

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

# =============== VAQTINCHALIK SAQLASH ===============
waiting_for = {}  # {user_id: 'state'}

# =============== YORDAMCHI FUNKSIYALAR ===============
def generate_code(length=6):
    chars = string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if animes_collection and not animes_collection.find_one({'code': code}):
            return code

def format_slug(text):
    text = text.replace("'", "").replace('"', "").replace("`", "").replace("ʻ", "")
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
    markup.add(types.KeyboardButton("⚙️ Anime sozlash"))
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
    args = message.text.split()
    
    if len(args) > 1:
        slug = args[1]
        anime = animes_collection.find_one({'slug': slug}) if animes_collection else None
        if anime:
            show_anime_info(message.chat.id, anime)
        else:
            bot.send_message(message.chat.id, "❌ Anime topilmadi!")
        return
    
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
    waiting_for.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "Asosiy menyu", reply_markup=asosiy_tugmalar(message.from_user.id))

# =============== ANIME QO'SHISH ===============
@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def anime_qoshish_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz!")
        return
    
    waiting_for[message.from_user.id] = 'waiting_anime_name'
    bot.send_message(message.chat.id, "📝 *Anime nomini kiriting:*", parse_mode="Markdown")

# =============== ANIME SOZLASH ===============
@bot.message_handler(func=lambda m: m.text == "⚙️ Anime sozlash")
def anime_sozlash_boshlash(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz!")
        return
    
    waiting_for[message.from_user.id] = 'waiting_anime_code'
    bot.send_message(message.chat.id, "🔑 *Anime kodini kiriting:*", parse_mode="Markdown")

# =============== XABARLARNI QABUL QILISH ===============
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    user_id = message.from_user.id
    state = waiting_for.get(user_id)
    
    if not state:
        bot.reply_to(message, "❌ Tushunmadim", reply_markup=asosiy_tugmalar(user_id))
        return
    
    # Anime nomini kutish
    if state == 'waiting_anime_name':
        anime_name = message.text.strip()
        slug = format_slug(anime_name)
        code = generate_code()
        
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
        
        bot_link = f"https://t.me/{BOT_USERNAME}?start={slug}"
        
        response = f"""
✅ *Anime qo'shildi!*

🔑 Kod: `{code}`
📺 Nomi: *{anime_name}*
🔗 Havola: {bot_link}

📌 Bu kodni faqat admin bilishi kerak!
"""
        waiting_for.pop(user_id, None)
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=admin_tugmalari())
    
    # Anime kodi kutish
    elif state == 'waiting_anime_code':
        code = message.text.strip()
        anime = animes_collection.find_one({'code': code}) if animes_collection else None
        
        if not anime:
            waiting_for.pop(user_id, None)
            bot.send_message(message.chat.id, "❌ Bunday kodli anime topilmadi!", reply_markup=admin_tugmalari())
            return
        
        waiting_for[user_id] = {'state': 'anime_settings', 'code': code}
        
        seasons_count = len(anime.get('seasons', []))
        movies_count = len(anime.get('movies', []))
        episodes_count = len(anime.get('episodes', []))
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📺 Fasl qo'shish", callback_data="add_season"),
            types.InlineKeyboardButton("🎬 Film qo'shish", callback_data="add_movie"),
            types.InlineKeyboardButton("📝 Qism qo'shish", callback_data="add_episode"),
            types.InlineKeyboardButton("❌ O'chirish", callback_data="delete_anime")
        )
        
        response = f"""
📺 *{anime['name']}*

📊 Statistika:
📺 Fasllar: {seasons_count} ta
🎬 Filmlar: {movies_count} ta
📝 Qismlar: {episodes_count} ta

Sozlamalarni tanlang:
"""
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)
    
    # Fasl qo'shish
    elif state == 'waiting_season_name':
        season_name = message.text.strip()
        user_data = waiting_for.get(user_id, {})
        anime_code = user_data.get('code')
        
        if animes_collection and anime_code:
            animes_collection.update_one(
                {'code': anime_code},
                {'$push': {'seasons': {'name': season_name, 'episodes': []}}}
            )
            bot.send_message(message.chat.id, f"✅ *{season_name}* fasl qo'shildi!", parse_mode="Markdown")
            waiting_for[user_id] = {'state': 'anime_settings', 'code': anime_code}
    
    # Film qo'shish
    elif state == 'waiting_movie_name':
        movie_name = message.text.strip()
        user_data = waiting_for.get(user_id, {})
        anime_code = user_data.get('code')
        
        if animes_collection and anime_code:
            animes_collection.update_one(
                {'code': anime_code},
                {'$push': {'movies': {'name': movie_name, 'file_id': None}}}
            )
            bot.send_message(message.chat.id, f"✅ *{movie_name}* film qo'shildi!", parse_mode="Markdown")
            waiting_for[user_id] = {'state': 'anime_settings', 'code': anime_code}
    
    # Qism qo'shish
    elif state == 'waiting_episode_name':
        episode_name = message.text.strip()
        user_data = waiting_for.get(user_id, {})
        anime_code = user_data.get('code')
        
        if animes_collection and anime_code:
            animes_collection.update_one(
                {'code': anime_code},
                {'$push': {'episodes': {'name': episode_name, 'file_id': None}}}
            )
            bot.send_message(message.chat.id, f"✅ *{episode_name}* qism qo'shildi!", parse_mode="Markdown")
            waiting_for[user_id] = {'state': 'anime_settings', 'code': anime_code}

# =============== CALLBACK HANDLERLAR ===============
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return
    
    user_id = call.from_user.id
    user_data = waiting_for.get(user_id, {})
    anime_code = user_data.get('code') if isinstance(user_data, dict) else None
    
    if call.data == "add_season":
        waiting_for[user_id] = {'state': 'waiting_season_name', 'code': anime_code}
        bot.send_message(call.message.chat.id, "📺 *Fasl nomini kiriting:*", parse_mode="Markdown")
    
    elif call.data == "add_movie":
        waiting_for[user_id] = {'state': 'waiting_movie_name', 'code': anime_code}
        bot.send_message(call.message.chat.id, "🎬 *Film nomini kiriting:*", parse_mode="Markdown")
    
    elif call.data == "add_episode":
        waiting_for[user_id] = {'state': 'waiting_episode_name', 'code': anime_code}
        bot.send_message(call.message.chat.id, "📝 *Qism nomini kiriting:*", parse_mode="Markdown")
    
    elif call.data == "delete_anime":
        if animes_collection and anime_code:
            animes_collection.delete_one({'code': anime_code})
        waiting_for.pop(user_id, None)
        bot.send_message(call.message.chat.id, "✅ Anime o'chirildi!", reply_markup=admin_tugmalari())
    
    bot.answer_callback_query(call.id)

# =============== ANIME MA'LUMOTLARINI KO'RSATISH ===============
def show_anime_info(chat_id, anime):
    seasons = anime.get('seasons', [])
    movies = anime.get('movies', [])
    episodes = anime.get('episodes', [])
    
    response = f"🎬 *{anime['name']}*\n\n"
    
    if seasons:
        response += "📺 *Fasllar:*\n"
        for i, season in enumerate(seasons, 1):
            response += f"  {i}. {season['name']}\n"
    
    if movies:
        response += "\n🎬 *Filmlar:*\n"
        for i, movie in enumerate(movies, 1):
            response += f"  {i}. {movie['name']}\n"
    
    if episodes:
        response += "\n📝 *Qismlar:*\n"
        for i, ep in enumerate(episodes, 1):
            response += f"  {i}. {ep['name']}\n"
    
    if not seasons and not movies and not episodes:
        response += "\n❌ Hozircha kontent qo'shilmagan!"
    
    bot.send_message(chat_id, response, parse_mode="Markdown")

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
