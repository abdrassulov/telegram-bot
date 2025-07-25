import os
import json
import logging
from fastapi import FastAPI
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# FastAPI app
app = FastAPI()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Авторизация в Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Функция поиска строки
def find_order_row(order_number):
    headers = worksheet.row_values(1)
    all_data = worksheet.get_all_values()[1:]  # без заголовков
    for row in all_data:
        if len(row) > 0 and row[0].strip() == order_number.strip():
            response_lines = []
            for i, value in enumerate(row):
                if i < len(headers):
                    response_lines.append(f"{headers[i]}: {value}")
            return "\n".join(response_lines)
    return "❌ Заказ не найден."

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне номер заказа, и я найду данные.")

# Обработчик текста
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    response = find_order_row(order_number)
    await update.message.reply_text(response)

# Создание Telegram приложения
app_telegram = Application.builder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Фоновый запуск Telegram-бота
@app.on_event("startup")
async def startup():
    logging.info("✅ Бот запускается...")
    asyncio.create_task(app_telegram.run_polling())

@app.get("/")
def root():
    return {"status": "бот работает"}

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
