import os
import json
import logging
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from dotenv import load_dotenv

# Загрузка переменных
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Логгирование
logging.basicConfig(level=logging.INFO)

# Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Поиск строки
def find_row_by_order(order_number):
    headers = worksheet.row_values(1)
    rows = worksheet.get_all_values()[1:]
    for row in rows:
        if row[0].strip() == order_number.strip():
            return "\n".join(f"{headers[i]}: {cell}" for i, cell in enumerate(row))
    return "❌ Заказ не найден."

# Telegram хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Отправь номер заказа, и я найду его в таблице.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    response = find_row_by_order(number)
    await update.message.reply_text(response)

# FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "бот работает"}

# Глобальный объект Telegram Application
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Вместо @app.on_event — lifespan
@app.on_event("startup")
async def on_startup():
    logging.info("✅ Запуск Telegram бота...")
    asyncio.create_task(telegram_app.run_polling())
