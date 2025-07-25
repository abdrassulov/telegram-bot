import os
import logging
import asyncio
import json

from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI для Render
app = FastAPI()

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GSPREAD_JSON), scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = sheet.sheet1  # или нужный лист

# Инициализация Telegram бота
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа.")


# Обработчик номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    try:
        records = worksheet.get_all_records()
        for row in records:
            if str(row["Номер заказа"]) == order_number:
                msg = "\n".join([f"{k}: {v}" for k, v in row.items()])
                await update.message.reply_text(f"🧾 Заказ найден:\n{msg}")
                return
        await update.message.reply_text("❌ Заказ не найден.")
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса.")


# Регистрируем обработчики
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Запуск Telegram-бота при старте FastAPI
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Бот запущен")
    asyncio.create_task(app_telegram.run_polling())


# Тестовый эндпоинт
@app.get("/")
async def root():
    return {"message": "Bot is running"}
