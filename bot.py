import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import gspread

# Загрузка .env
load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
worksheet = gc.open_by_url(SPREADSHEET_URL).get_worksheet(0)

# Инициализация Telegram-приложения
app_tg = Application.builder().token(BOT_TOKEN).build()

# Функция поиска строки
def find_order(order_number: str) -> str:
    headers = worksheet.row_values(1)
    all_data = worksheet.get_all_values()[1:]
    for row in all_data:
        if row and row[0].strip() == order_number.strip():
            return "\n".join([f"{headers[i]} — {row[i]}" for i in range(len(headers)) if i < len(row)])
    return "Заказ не найден."

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я покажу информацию.")

# Обработчик номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    response = find_order(text)
    await update.message.reply_text(response)

# Регистрация обработчиков
app_tg.add_handler(CommandHandler("start", start))
app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI-приложение
app = FastAPI()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_tg.bot)
    await app_tg.process_update(update)
    return JSONResponse({"status": "ok"})

@app.get("/")
def home():
    return {"status": "ok"}

# Lifespan (запуск бота + установка webhook)
@app.on_event("startup")
async def on_startup():
    logger.info("⏳ Установка Webhook...")
    await app_tg.initialize()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await app_tg.bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 Отключение Webhook...")
    await app_tg.shutdown()
