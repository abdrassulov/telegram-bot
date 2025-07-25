import os
import json
import logging
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# Подключение к таблице
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)


# Функция поиска строки по номеру заказа и возврата пары "заголовок: значение"
def find_order(order_number):
    all_values = worksheet.get_all_values()
    if not all_values or len(all_values) < 2:
        return "❌ Таблица пуста или нет данных."

    headers = all_values[0]
    rows = all_values[1:]

    for row in rows:
        if len(row) > 0 and row[0].strip() == order_number.strip():
            response_lines = []
            for i in range(len(headers)):
                header = headers[i] if i < len(headers) else f"Колонка {i + 1}"
                value = row[i] if i < len(row) else ""
                response_lines.append(f"{header}: {value}")
            return "\n".join(response_lines)

    return "❌ Заказ не найден."


# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь номер заказа, и я найду информацию.")


# Обработка обычных сообщений (предположительно номер заказа)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = find_order(user_message)
    await update.message.reply_text(response)


# Инициализация Telegram Application
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start_command))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Инициализация FastAPI
app = FastAPI()


# Lifespan (запуск и остановка бота)
@app.on_event("startup")
async def on_startup():
    logging.info("🚀 Запускается бот...")
    asyncio.create_task(app_telegram.run_polling())


@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Остановка бота...")
    await app_telegram.shutdown()


# Эндпоинт для проверки статуса
@app.get("/")
def root():
    return {"status": "бот работает"}
