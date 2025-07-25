import os
import json
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных (для локальной разработки, на Render не обязательно)
load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Проверка токена и подключения
if not BOT_TOKEN or not GSPREAD_JSON:
    raise RuntimeError("❌ BOT_TOKEN или GSPREAD_JSON не заданы в переменных окружения!")

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# URL таблицы
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
worksheet = gc.open_by_url(SPREADSHEET_URL).get_worksheet(0)

# Функция поиска строки по номеру заказа
def find_order_row(order_number: str) -> str:
    sheet_data = worksheet.get_all_values()
    if not sheet_data or len(sheet_data) < 2:
        return "❌ Таблица пуста или содержит только заголовки."

    headers = sheet_data[0]
    for row in sheet_data[1:]:
        if row[0].strip() == order_number.strip():  # Сравниваем с первым столбцом (Номер заказа)
            return "\n".join(f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row))))
    return "🔍 Заказ не найден."

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь номер заказа, и я найду информацию в таблице.")

# Сообщения с текстом
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    response = find_order_row(order_number)
    await update.message.reply_text(response)

# Инициализация Telegram Application
app_telegram: Application = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Стартап и выключение через lifespan
@app.on_event("startup")
async def startup():
    logger.info("✅ Бот запускается...")
    await app_telegram.initialize()
    await app_telegram.start()
    await app_telegram.updater.start_polling()

@app.on_event("shutdown")
async def shutdown():
    await app_telegram.updater.stop()
    await app_telegram.stop()
    await app_telegram.shutdown()

# Эндпоинт для проверки
@app.get("/")
def root():
    return {"status": "бот работает ✅"}

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
