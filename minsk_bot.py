import os
import telebot
from telebot import types
import requests
import logging
import json
from flask import Flask, request

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменили уровень на DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_TOKEN = "7763479683:AAEiEsx4465ou4hQa6WjGTtHO0lIbDeYNr0"
ABACUS_DEPLOYMENT_ID = "dc537f08c"
ABACUS_API_URL = "https://api.abacus.ai/api/v0/deployment/predict"
ABACUS_TOKEN = "s2_eb0c25c11860486f8e807780c18941e1"

# История чатов пользователей
user_histories = {}

# Инициализация Flask и бота
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.debug(f"Received /start command from user {message.from_user.id}")
    try:
        # Сначала отправляем простое сообщение
        bot.reply_to(message, "Привет! Подождите секунду...")
        logger.debug("Sent initial response")
        
        # Затем отправляем полное приветствие с меню
        welcome_text = """👋 Здравствуйте! Я AI-консультант по недвижимости в Минске.

Чем могу помочь?
• Оценка стоимости квартиры
• Помощь с покупкой/продажей
• Информация о районах
• Консультация по документам"""

        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = [
            "💰 Оценить квартиру",
            "🏠 Купить квартиру",
            "🔑 Продать квартиру",
            "🗺 Районы Минска",
            "📋 Документы",
            "❓ Помощь"
        ]
        keyboard.add(*[types.KeyboardButton(text) for text in buttons])
        
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=keyboard
        )
        logger.debug("Sent welcome message with keyboard")
        
    except Exception as e:
        logger.error(f"Error in send_welcome: {str(e)}", exc_info=True)
        bot.reply_to(message, "Произошла ошибка при запуске. Попробуйте позже.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    logger.debug(f"Received message: {message.text} from user {message.from_user.id}")
    try:
        # Сразу отправляем подтверждение получения
        bot.reply_to(message, "Получил ваше сообщение, обрабатываю...")
        logger.debug("Sent confirmation message")
        
    except Exception as e:
        logger.error(f"Error in handle_text: {str(e)}", exc_info=True)
        bot.reply_to(message, f"Ошибка: {str(e)}")

# Обработка вебхука
@app.route("/" + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    try:
        logger.debug("Webhook received request")
        logger.debug(f"Headers: {request.headers}")
        
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logger.debug(f"Received webhook data: {json_string}")
            
            update = telebot.types.Update.de_json(json_string)
            logger.debug("Created Update object")
            
            bot.process_new_updates([update])
            logger.debug("Processed update")
            
            return ''
        else:
            logger.warning(f"Received request with wrong content-type: {request.headers.get('content-type')}")
            return 'Error: wrong content-type'
    
    except Exception as e:
        logger.error(f"Error in webhook handler: {str(e)}", exc_info=True)
        return 'Error in webhook handler'

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    logger.info("Starting bot application")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
