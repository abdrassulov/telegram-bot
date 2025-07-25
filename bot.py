import os
import json
import logging
import asyncio

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# FastAPI приложение
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Bot is alive"}

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GSPREAD_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

# Подключение к таблице
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь номер заказа")

# Обработка номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    order_number = update.message.text.strip()
    logging.info(f"Ищем заказ: {order_number}")

    try:
        data = worksheet.get_all_records()
        headers = worksheet.row_values(1)

        for row in data:
            if str(row.get("Номер заказа")).strip() == order_number:
                response = "\n".join(f"{header}: {row.get(header, '')}" for header in headers)
                await update.message.reply_text(response)
                return

        await update.message.reply_text("Номер заказа не найден.")
    except Exception as e:
        logging.exception("Ошибка при поиске")
        await update.message.reply_text(f"Ошибка: {e}")

# Основной бот
async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Telegram bot is running")
    await application.run_polling(close_loop=False)

# Запуск бота при старте FastAPI
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())
