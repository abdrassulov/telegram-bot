import os
import json
import logging
import gspread
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к Google Таблице
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Инициализация Telegram приложения
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")

# Обработчик сообщений с номером заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    all_values = worksheet.get_all_values()

    headers = all_values[0]
    matched_row = None
    for row in all_values[1:]:
        if row[0].strip() == order_number:
            matched_row = row
            break

    if matched_row:
        result = "\n".join([f"{header}: {value}" for header, value in zip(headers, matched_row)])
    else:
        result = "Заказ не найден."

    await update.message.reply_text(result)

# Добавление обработчиков
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Lifespan вместо on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Бот запускается...")
    await app_telegram.initialize()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await app_telegram.bot.set_webhook(webhook_url)
    await app_telegram.start()
    yield
    logger.info("❌ Остановка бота...")
    await app_telegram.stop()
    await app_telegram.shutdown()

# FastAPI-приложение
app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app_telegram.bot)
    await app_telegram.process_update(update)
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Бот работает"}
