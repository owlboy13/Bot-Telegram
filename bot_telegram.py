import telebot
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_TOKEN_ANDERSON')

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá eu sou o Bot que bota, como posso te ajudar?")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling(timeout=10)