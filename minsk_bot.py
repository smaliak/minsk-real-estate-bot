import os
import telebot
from telebot import types
import requests
import logging
import json
from flask import Flask, request

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_TOKEN = "7763479683:AAEiEsx4465ou4hQa6WjGTtHO0lIbDeYNr0"

# Инициализация Flask и бота
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)  # Отключаем threading

# Простой обработчик для проверки
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.debug("START handler called")
    try:
        # Простой ответ для тестирования
        bot.reply_to(message, "Тест бота. Сообщение получено.")
        logger.debug("Sent test response")
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}", exc_info=True)

# Обработчик для всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.debug("Default handler called")
    try:
        bot.reply_to(message, f"Вы написали: {message.text}")
        logger.debug("Sent echo response")
    except Exception as e:
        logger.error(f"Error in echo handler: {str(e)}", exc_info=True)

# Обработка вебхука
@app.route("/" + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    try:
        logger.debug("Webhook handler started")
        
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logger.debug(f"Webhook data: {json_string}")
            
            try:
                update = telebot.types.Update.de_json(json_string)
                logger.debug("Update object created")
                
                # Пробуем получить текст сообщения
                if update.message:
                    logger.debug(f"Message text: {update.message.text}")
                
                # Обработка обновления
                bot.process_new_updates([update])
                logger.debug("Update processed")
                
            except Exception as e:
                logger.error(f"Error processing update: {str(e)}", exc_info=True)
            
            return ''
    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}", exc_info=True)
        return 'Error in webhook handler'

@app.route("/")
def index():
    return "Bot is running"

# Обработка ошибок Flask
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"Flask error: {str(e)}", exc_info=True)
    return str(e), 500

if __name__ == "__main__":
    logger.info("Starting bot application")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
