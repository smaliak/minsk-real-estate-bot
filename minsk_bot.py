import os
import telebot
from telebot import types
import requests
import logging
import json
from flask import Flask, request

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_TOKEN = "7763479683:AAEiEsx4465ou4hQa6WjGTtHO0lIbDeYNr0"
ABACUS_DEPLOYMENT_ID = "2f66f5efc"
ABACUS_API_URL = "https://app.abacus.ai/api/v0/deployment/predict"  # Обновленный URL
ABACUS_TOKEN = "004a4ac2c18144cda4198ce9a964d26d"

# История чатов пользователей
user_histories = {}

# Инициализация Flask и бота
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

def get_ai_response(user_id, message_text):
    """Получение ответа от Abacus AI"""
    try:
        logger.debug(f"Получаем ответ AI для пользователя {user_id}")
        
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        headers = {
            "Authorization": f"Bearer {ABACUS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "deployment_id": ABACUS_DEPLOYMENT_ID,
            "prediction_input": {
                "question": message_text,
                "chat_history": user_histories[user_id]
            }
        }
        
        logger.debug(f"Отправляем запрос к API: URL={ABACUS_API_URL}")
        logger.debug(f"Заголовки: {headers}")
        logger.debug(f"Данные: {json.dumps(data)}")
        
        # Пробуем разные варианты URL если основной не работает
        urls_to_try = [
            "https://app.abacus.ai/api/v0/deployment/predict",
            "https://api.abacus.ai/api/v0/deployment/predict",
            "https://api.abacus.ai/deployment/predict"
        ]
        
        response = None
        working_url = None
        
        for url in urls_to_try:
            try:
                logger.debug(f"Пробуем URL: {url}")
                response = requests.post(url, headers=headers, json=data, timeout=10)
                if response.status_code == 200:
                    working_url = url
                    break
                else:
                    logger.warning(f"URL {url} вернул статус {response.status_code}")
            except Exception as e:
                logger.warning(f"Ошибка при использовании URL {url}: {str(e)}")
                continue
        
        if working_url:
            logger.info(f"Найден работающий URL: {working_url}")
            global ABACUS_API_URL
            ABACUS_API_URL = working_url
        
        if response and response.status_code == 200:
            result = response.json()
            answer = result["prediction"]["answer"]
            
            user_histories[user_id].append({"role": "user", "content": message_text})
            user_histories[user_id].append({"role": "assistant", "content": answer})
            
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][-20:]
            
            logger.debug("Успешно получен ответ от AI")
            return answer
        else:
            status = response.status_code if response else "Нет ответа"
            text = response.text[:200] if response else "Нет текста ответа"
            logger.error(f"Ошибка API: {status} - {text}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении ответа AI: {str(e)}", exc_info=True)
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
        logger.error(f"Ошибка в обработчике start: {str(e)}", exc_info=True)

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
            error_message = "Извините, произошла техническая ошибка. Мы работаем над её устранением. Пожалуйста, попробуйте позже."
            bot.reply_to(message, error_message)
            logger.warning("Отправлено сообщение об ошибке (ответ AI не получен)")

    except Exception as e:
        logger.error(f"Ошибка в обработчике сообщений: {str(e)}", exc_info=True)
        bot.reply_to(message, "Произошла ошибка. Попробуйте еще раз позже.")

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
        logger.error(f"Ошибка в обработчике вебхука: {str(e)}", exc_info=True)
        return 'Error in webhook handler'

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    logger.info("Запуск приложения бота")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
