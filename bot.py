import os
import json
import logging
from fastapi import FastAPI, Request
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
from contextlib import asynccontextmanager

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Логирование
logging.basicConfig(level=logging.INFO)

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Telegram приложение
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Функция поиска по заказу
def find_row_by_order(order_number: str) -> str:
    all_data = worksheet.get_all_values()
    headers = all_data[0]
    for row in all_data[1:]:
        if row[0].strip() == order_number.strip():
            return "\n".join([f"{headers[i]} — {row[i]}" for i in range(len(headers))])
    return "❌ Заказ не найден."

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я покажу данные.")

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = update.message.text.strip()
    await update.message.reply_text(find_row_by_order(order))

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))

# Lifespan для FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("✅ Запуск Telegram-бота")
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=RENDER_EXTERNAL_URL)
    yield
    logging.info("🛑 Остановка Telegram-бота")
    await telegram_app.shutdown()

# FastAPI
app = FastAPI(lifespan=lifespan)

# Webhook endpoint
@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
