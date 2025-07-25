import os
import json
import logging
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
worksheet = gc.open_by_url(SPREADSHEET_URL).get_worksheet(0)

# Поиск по заказу
def find_order(order_number):
    headers = worksheet.row_values(1)
    rows = worksheet.get_all_values()[1:]  # Без заголовков
    for row in rows:
        if row and row[0].strip() == order_number.strip():
            return "\n".join(
                f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))
            )
    return "❌ Заказ не найден."

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = update.message.text
    result = find_order(order)
    await update.message.reply_text(result)

# FastAPI
app = FastAPI()

# Telegram App
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# FastAPI lifecycle (lifespan)
@app.on_event("startup")
async def on_startup():
    logging.info("✅ Бот запускается...")
    asyncio.create_task(telegram_app.run_polling())

@app.get("/")
def root():
    return {"status": "бот работает"}
