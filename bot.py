import os
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import gspread
import json
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Инициализация логгера
logging.basicConfig(level=logging.INFO)

# Создание FastAPI-приложения
app = FastAPI()

# Создание Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# Укажи ПРАВИЛЬНЫЙ URL твоей таблицы
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Функция поиска по номеру заказа
def find_row_by_order(order_number):
    all_data = worksheet.get_all_records()
    for row in all_data:
        if str(row.get("Номер заказа")).strip() == str(order_number).strip():
            return "\n".join([f"{k}: {v}" for k, v in row.items()])
    return "Заказ не найден."

# Обработчик сообщений Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)

# Инициализация Telegram-приложения
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск Telegram-бота при старте FastAPI
@app.on_event("startup")
async def startup_event():
    logging.info("Бот запущен")
    await app_telegram.initialize()
    await app_telegram.start()
    await app_telegram.updater.start_polling()

# Завершение при остановке
@app.on_event("shutdown")
async def shutdown_event():
    await app_telegram.updater.stop()
    await app_telegram.stop()
    await app_telegram.shutdown()

# Корневой эндпоинт FastAPI
@app.get("/")
def root():
    return {"status": "бот работает"}

# Запуск uvicorn на Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
