import os
import logging
import json
import asyncio

import gspread
from fastapi import FastAPI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI()

# Подключение к Google Таблице
gspread_json = os.getenv("GSPREAD_JSON")
creds = json.loads(gspread_json)
gc = gspread.service_account_from_dict(creds)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")

worksheet = spreadsheet.sheet1  # первая вкладка

# Telegram-приложение
app_telegram = Application.builder().token(BOT_TOKEN).build()

# Обработчик команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите номер заказа:")

# Обработчик сообщений (поиск в таблице)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    try:
        records = worksheet.get_all_records()
        result = None
        for row in records:
            if str(row.get("Номер заказа")) == order_number:
                result = "\n".join([f"{k} — {v}" for k, v in row.items()])
                break

        if result:
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("Заказ не найден.")
    except Exception as e:
        logger.exception("Ошибка при обработке заказа")
        await update.message.reply_text("Произошла ошибка при обработке.")

# Регистрация хендлеров
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Старт телеграм-бота при запуске сервера
@app.on_event("startup")
async def on_startup():
    logger.info("Бот запущен")
    asyncio.create_task(app_telegram.run_polling())
