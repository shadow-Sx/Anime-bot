import os
import telebot
from telebot import types

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = telebot.TeleBot(TOKEN)

# =============== ASOSIY TUGMALAR ===============
def asosiy_tugmalar(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("ℹ️ Yordam")
    markup.add(btn1)
    
    # Faqat admin ko'radi
    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("👨‍💻 Admin Panel")
        markup.add(btn_admin)
    
    return markup

# =============== START ===============
@bot.message_handler(commands=['start'])
def send_welcome(message):
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
    user_id = message.from_user.id
    
    # Admin Panel tugmasi
    if message.text == "👨‍💻 Admin Panel":
        if user_id == ADMIN_ID:
            admin_panel(message)
        else:
            bot.reply_to(message, "❌ Siz admin emassiz!")
    
    # Yordam tugmasi
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
    btn3 = types.KeyboardButton("🔙 Orqaga")
    
    markup.add(btn1, btn2)
    markup.add(btn3)
    
    bot.send_message(message.chat.id, "👨‍💻 Admin Panelga xush kelibsiz!", reply_markup=markup)

# =============== BOTNI ISHGA TUSHIRISH ===============
if __name__ == "__main__":
    print("🚀 Bot ishga tushdi...")
    bot.infinity_polling()
