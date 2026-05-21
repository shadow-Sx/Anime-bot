import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "🤖 Bot ishlamoqda!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Salom {message.from_user.first_name}! 🎬")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "/start /help")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, f"Siz yozdingiz: {message.text}")

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
