import os
import json
import logging
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler,
    CommandHandler, filters
)
import gspread
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # https://your-service.onrender.com

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# FastAPI
app = FastAPI()

# Telegram Application
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()


# Поиск строки по номеру заказа
def find_row_by_order(order_number):
    data = worksheet.get_all_values()
    headers = data[0]
    for row in data[1:]:
        if row[0].strip() == str(order_number).strip():
            result = []
            for i in range(len(headers)):
                if i < len(row):
                    result.append(f"{headers[i]}: {row[i]}")
            return "\n".join(result)
    return "Заказ не найден."


# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")


# Обработка номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)


# Регистрация обработчиков
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


@app.on_event("startup")
async def on_startup():
    logging.info("🚀 Запуск бота")
    await app_telegram.initialize()
    await app_telegram.bot.delete_webhook(drop_pending_updates=True)
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await app_telegram.bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook установлен: {webhook_url}")


@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Остановка бота")
    await app_telegram.bot.delete_webhook()
    await app_telegram.shutdown()


@app.post("/webhook")
async def telegram_webhook(req: Request):
    body = await req.body()
    update = Update.de_json(json.loads(body), app_telegram.bot)
    await app_telegram.process_update(update)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "бот работает"}
