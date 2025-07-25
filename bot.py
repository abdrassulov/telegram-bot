import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import gspread
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")  # например: https://telegram-bot-xxxxx.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# Поиск строки по номеру заказа
def find_order(order_number):
    headers = worksheet.row_values(1)
    all_rows = worksheet.get_all_values()[1:]  # без шапки
    for row in all_rows:
        if row[0].strip() == order_number.strip():
            return "\n".join(f"{headers[i]}: {row[i]}" for i in range(len(headers)) if i < len(row))
    return "❌ Заказ не найден."

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я пришлю информацию.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    result = find_order(order_number)
    await update.message.reply_text(result)

# Создание FastAPI-приложения
app = FastAPI()
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Подключение Webhook
@app.on_event("startup")
async def on_startup():
    logging.info("🚀 Старт приложения")
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Остановка приложения")
    await telegram_app.bot.delete_webhook()
    await telegram_app.shutdown()

# Webhook endpoint
@app.post(WEBHOOK_PATH)
async def process_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "✅ бот запущен и ждёт команды"}
