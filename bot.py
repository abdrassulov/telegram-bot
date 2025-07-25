import os
import json
import logging
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Инициализация FastAPI
app = FastAPI()

# Переменные из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# Подключение к таблице
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Поиск строки по номеру заказа
def find_row_by_order(order_number):
    headers = worksheet.row_values(1)
    all_rows = worksheet.get_all_values()
    for row in all_rows[1:]:
        if row[0].strip() == order_number.strip():
            return "\n".join(f"{headers[i]}: {cell}" for i, cell in enumerate(row))
    return "Заказ не найден."

# Telegram хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)

# Создание Telegram приложения
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Фоновый запуск Telegram-бота
@app.on_event("startup")
async def startup_event():
    logging.info("✅ Бот запускается...")
    asyncio.create_task(telegram_app.run_polling())

# Корневой эндпоинт (чтобы Render видел активный порт)
@app.get("/")
def root():
    return {"status": "бот работает"}
