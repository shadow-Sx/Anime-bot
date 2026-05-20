import os
import telebot
from telebot import types

# Environment variables
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Admin ID raqamingiz

# Tokenni tekshirish
if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render'da Environment Variables ga qo'shing")

bot = telebot.TeleBot(TOKEN)

# =============== START ===============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = f"""
🎬 Assalomu alaykum, {user_name}!

Anime Yuklovchi Botga xush kelibsiz!

📌 Mavjud buyruqlar:
/start - Botni ishga tushirish
/help - Yordam olish

👨‍💻 Admin bilan bog'lanish: @admin_username
    """
    bot.reply_to(message, welcome_text)

# =============== HELP ===============
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 Yordam:

/start - Botni ishga tushirish
/help - Yordam olish

Tez orada qo'shiladi:
🎥 Anime yuklash
🔑 Kod orqali anime ochish
    """
    bot.reply_to(message, help_text)

# =============== ADMIN BUYRUQLARI ===============
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        admin_text = """
👨‍💻 Admin Panel:

/anime_qosh - Yangi anime qo'shish
/anime_ochir - Anime o'chirish
/anime_list - Anime ro'yxati
        """
        bot.reply_to(message, admin_text)
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

# =============== ODDIY XABARLAR ===============
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "❌ Noma'lum buyruq. /help orqali yordam oling.")

# =============== BOTNI ISHGA TUSHIRISH ===============
if __name__ == "__main__":
    print("🚀 Bot ishga tushdi...")
    bot.infinity_polling()
