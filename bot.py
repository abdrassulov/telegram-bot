import os
import json
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)

# FastAPI приложение
app = FastAPI()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# URL таблицы
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Функция поиска строки по номеру заказа
def find_row_by_order(order_number):
    all_data = worksheet.get_all_records()
    for row in all_data:
        if str(row.get("Номер заказа")).strip() == str(order_number).strip():
            return "\n".join([f"{k}: {v}" for k, v in row.items()])
    return "Заказ не найден."

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)

# Инициализация Telegram Application
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск бота при старте приложения
@app.on_event("startup")
async def startup():
    logging.info("Бот запущен")
    await app_telegram.initialize()
    await app_telegram.start()
    await app_telegram.updater.start_polling()

# Остановка бота при выключении
@app.on_event("shutdown")
async def shutdown():
    await app_telegram.updater.stop()
    await app_telegram.stop()
    await app_telegram.shutdown()

# Корневая страница
@app.get("/")
def root():
    return {"status": "бот работает"}

# Локальный запуск (на Render не используется, но оставим)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
