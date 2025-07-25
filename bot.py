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
    filters
)
import gspread
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Инициализация логгера
logging.basicConfig(level=logging.INFO)

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# Поиск строки по номеру заказа
def find_row(order_number: str):
    headers = worksheet.row_values(1)
    all_data = worksheet.get_all_values()
    for row in all_data[1:]:
        if row[0].strip() == order_number.strip():
            return "\n".join(f"{headers[i]}: {row[i]}" for i in range(len(headers)))
    return "❌ Заказ не найден."

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь номер заказа, и я найду информацию.")

# Обработчик сообщений с номером заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row(order_number)
    await update.message.reply_text(response)

# Создание Telegram-приложения
bot: Application = ApplicationBuilder().token(BOT_TOKEN).build()
bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Lifespan для FastAPI (вместо on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("✅ Бот запускается...")
    await bot.initialize()
    await bot.start()
    await bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
    yield
    logging.info("🛑 Остановка бота...")
    await bot.stop()
    await bot.shutdown()

# FastAPI-приложение
app = FastAPI(lifespan=lifespan)

# Webhook endpoint
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot.bot)
    await bot.process_update(update)
    return {"status": "ok"}

# Главная страница
@app.get("/")
def root():
    return {"status": "бот работает"}
