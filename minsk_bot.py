import os
import telebot
from telebot import types
import requests
import logging
from flask import Flask, request

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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

def get_ai_response(user_id, message_text):
    """Получение ответа от Abacus AI"""
    try:
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        # Формируем запрос к API
        data = {
            "deployment_id": ABACUS_DEPLOYMENT_ID,
            "prediction_input": {
                "question": message_text,
                "chat_history": user_histories[user_id]
            }
        }
        
        # Отправляем запрос
        response = requests.post(
            ABACUS_API_URL,
            json=data,
            headers={
                "Authorization": f"Bearer {ABACUS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["prediction"]["answer"]
            
            # Сохраняем историю
            user_histories[user_id].append({"role": "user", "content": message_text})
            user_histories[user_id].append({"role": "assistant", "content": answer})
            
            # Ограничиваем историю
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][-20:]
                
            return answer
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
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
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        # Показываем "печатает..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от AI
        ai_response = get_ai_response(message.from_user.id, message.text)
        
        if ai_response:
            bot.reply_to(message, ai_response)
        else:
            bot.reply_to(message, "Извините, произошла ошибка. Попробуйте переформулировать вопрос.")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        bot.reply_to(message, "Извините, произошла ошибка. Попробуйте еще раз.")

# Обработка вебхука
@app.route("/" + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Error: wrong content-type'

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    # Запуск Flask приложения
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
