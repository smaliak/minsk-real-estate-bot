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
        
        data = {
            "deployment_id": ABACUS_DEPLOYMENT_ID,
            "prediction_input": {
                "question": message_text,
                "chat
