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
ABACUS_DEPLOYMENT_ID = "dc537f08c"
ABACUS_API_URL = "https://api.abacus.ai/api/v0/deployment/predict"
ABACUS_TOKEN = "s2_eb0c25c11860486f8e807780c18941e1"

# История чатов пользователей
user_histories = {}

# Инициализация Flask и бота
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def get_ai_response(user_id, message_text):
    """Получение ответа от Abacus AI"""
    try:
        logger.debug(f"Getting AI response for user {user_id}")
        
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        data = {
            "deployment_id": ABACUS_DEPLOYMENT_ID,
            "prediction_input": {
                "question": message_text,
                "chat_history": user_histories[user_id]
            }
        }
        
        logger.debug("Sending request to Abacus AI")
        response = requests.post(
            ABACUS_API_URL,
            json=data,
            headers={
                "Authorization": f"Bearer {ABACUS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        logger.debug(f"Abacus AI response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result["prediction"]["answer"]
            
            user_histories[user_id].append({"role": "user", "content": message_text})
            user_histories[user_id].append({"role": "assistant", "content": answer})
            
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][-20:]
            
            logger.debug("AI response received successfully")
            return answer
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
        return None

def create_keyboard():
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
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.debug("START handler called")
    welcome_text = """👋 Здравствуйте! Я AI-консультант по недвижимости в Минске.

Чем могу помочь?
• Оценка стоимости квартиры
• Помощь с покупкой/продажей
• Информация о районах
• Консультация по документам

Выберите тему в меню или задайте вопрос ⬇️"""
    
    try:
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=create_keyboard(),
            parse_mode='HTML'
        )
        logger.debug("Welcome message sent")
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}", exc_info=True)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        logger.debug(f"Received message: {message.text}")
        
        # Сначала отправляем подтверждение
        bot.reply_to(message, "Секунду, формирую ответ...")
        logger.debug("Sent confirmation message")
        
        # Получаем ответ от AI
        bot.send_chat_action(message.chat.id, 'typing')
        ai_response = get_ai_response(message.from_user.id, message.text)
        
        if ai_response:
            bot.reply_to(message, ai_response)
            logger.debug("Sent AI response")
        else:
            error_message = "Извините, произошла ошибка. Попробуйте переформулировать вопрос."
            bot.reply_to(message, error_message)
            logger.warning("Sent error message (AI response failed)")

    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}", exc_info=True)
        bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

@app.route("/" + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    try:
        logger.debug("Webhook handler started")
        
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logger.debug("Received webhook data")
            
            update = telebot.types.Update.de_json(json_string)
            logger.debug("Created Update object")
            
            bot.process_new_updates([update])
            logger.debug("Processed update")
            
            return ''
        else:
            logger.warning("Received request with wrong content-type")
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
