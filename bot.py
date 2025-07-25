import os
import json
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from dotenv import load_dotenv
import asyncio

# Загрузка .env переменных
load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация переменных
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
worksheet = gc.open_by_url(SPREADSHEET_URL).get_worksheet(0)

# Функция поиска строки по номеру заказа
def find_row(order_number):
    headers = worksheet.row_values(1)
    all_rows = worksheet.get_all_values()[1:]
    for row in all_rows:
        if len(row) > 0 and row[0].strip() == order_number.strip():
            return "\n".join(
                f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))
            )
    return "❌ Заказ не найден."

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row(order_number)
    await update.message.reply_text(response)

# Создание Telegram-приложения
app_telegram = Application.builder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# FastAPI
app = FastAPI()

# Lifespan — запускает и останавливает Telegram-бота корректно
@app.on_event("startup")
async def startup():
    asyncio.create_task(app_telegram.run_polling())

@app.get("/")
def root():
    return {"status": "бот работает"}
