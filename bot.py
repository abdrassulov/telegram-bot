import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка переменных окружения
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

# FastAPI app
app = FastAPI()

# Создание Telegram-приложения
app_telegram = Application.builder().token(BOT_TOKEN).build()


def find_row_by_order(order_number: str) -> str:
    all_data = worksheet.get_all_values()
    headers = all_data[0]
    for row in all_data[1:]:
        if row[0].strip() == order_number.strip():  # поиск по первому столбцу
            result = "\n".join([f"{headers[i]} — {row[i]}" for i in range(len(headers))])
            return result
    return "❌ Заказ не найден."


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я пришлю детали.")

# Обработчик номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)


# Регистрация обработчиков
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Webhook endpoint от Telegram
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_telegram.bot)
    await app_telegram.process_update(update)
    return {"ok": True}


# При старте — устанавливаем webhook
@app.on_event("startup")
async def on_startup():
    logging.info("✅ Бот запускается...")
    await app_telegram.initialize()
    await app_telegram.bot.set_webhook(f"{RENDER_EXTERNAL_URL}")
    logging.info("✅ Webhook установлен")


# При завершении
@app.on_event("shutdown")
async def on_shutdown():
    await app_telegram.bot.delete_webhook()
    await app_telegram.shutdown()
