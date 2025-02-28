import os
import telebot
from telebot import types
import requests
import logging
from flask import Flask, request

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_TOKEN = "7763479683:AAEiEsx4465ou4hQa6WjGTtHO0lIbDeYNr0"
ABACUS_DEPLOYMENT_ID = "2f66f5efc"  # Новый деплоймент
ABACUS_API_URL = "https://api.abacus.ai/api/v0/deployment/predict"
ABACUS_TOKEN = "004a4ac2c18144cda4198ce9a964d26d"  # Новый токен

# История чатов пользователей
user_histories = {}

# Инициализация Flask и бота
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def get_ai_response(user_id, message_text):
    """Получение ответа от Abacus AI"""
    try:
        logger.debug(f"Получаем ответ AI для пользователя {user_id}")
        
        # Инициализация истории чата для нового пользователя
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        # Подготовка данных для запроса
        data = {
            "deployment_id": ABACUS_DEPLOYMENT_ID,
            "prediction_input": {
                "question": message_text,
                "chat_history": user_histories[user_id]
            }
        }
        
        logger.debug("Отправляем запрос к Abacus AI")
        response = requests.post(
            ABACUS_API_URL,
            json=data,
            headers={
                "Authorization": f"Bearer {ABACUS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        logger.debug(f"Статус ответа API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result["prediction"]["answer"]
            
            # Обновляем историю чата
            user_histories[user_id].append({"role": "user", "content": message_text})
            user_histories[user_id].append({"role": "assistant", "content": answer})
            
            # Ограничиваем историю последними 20 сообщениями
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][-20:]
            
            logger.debug("Ответ AI получен успешно")
            return answer
        else:
            logger.error(f"Ошибка API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении ответа AI: {str(e)}")
        return None

def create_keyboard():
    """Создание клавиатуры с кнопками"""
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
    """Обработчик команды /start"""
    logger.debug("Получена команда /start")
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
            reply_markup=create_keyboard()
        )
        logger.debug("Отправлено приветственное сообщение")
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработчик текстовых сообщений"""
    try:
        logger.debug(f"Получено сообщение: {message.text}")
        
        # Отправляем "печатает..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от AI
        ai_response = get_ai_response(message.from_user.id, message.text)
        
        if ai_response:
            bot.reply_to(message, ai_response)
            logger.debug("Отправлен ответ AI")
        else:
            error_message = "Извините, произошла ошибка. Попробуйте переформулировать вопрос."
            bot.reply_to(message, error_message)
            logger.warning("Отправлено сообщение об ошибке (ответ AI не получен)")

    except Exception as e:
        logger.error(f"Ошибка в обработчике сообщений: {str(e)}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз.")

@app.route("/" + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    try:
        logger.debug("Получен вебхук")
        
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logger.debug("Получены данные вебхука")
            
            update = telebot.types.Update.de_json(json_string)
            logger.debug("Создан объект Update")
            
            bot.process_new_updates([update])
            logger.debug("Обработано обновление")
            
            return ''
        else:
            logger.warning("Получен запрос с неверным content-type")
            return 'Error: wrong content-type'
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике вебхука: {str(e)}")
        return 'Error in webhook handler'

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    logger.info("Запуск приложения бота")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
