import os
import json
import logging

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import gspread
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # напр. https://telegram-bot-xxxx.onrender.com

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI()

# Авторизация Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# Подключение к таблице
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Поиск строки по номеру заказа
def find_row_by_order(order_number):
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    for row in all_values[1:]:
        if str(row[0]).strip() == str(order_number).strip():
            return "\n".join([f"{headers[i]}: {row[i]}" for i in range(len(headers))])
    return "Заказ не найден."

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")

# Обработка текста (номеров заказов)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)

# Инициализация Telegram-приложения
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Установка webhook при старте
@app.on_event("startup")
async def startup_event():
    logger.info("✅ Бот запускается...")
    await app_telegram.initialize()
    await app_telegram.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
    logger.info("🔗 Webhook установлен")

# Остановка при завершении
@app.on_event("shutdown")
async def shutdown_event():
    await app_telegram.shutdown()
    logger.info("❌ Бот остановлен")

# Обработка запросов Telegram
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_telegram.bot)
    await app_telegram.update_queue.put(update)
    return {"ok": True}

# Проверка статуса
@app.get("/")
def root():
    return {"status": "бот работает"}
