import os
import json
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)


# Функция поиска по номеру заказа
def find_row_by_order(order_number):
    all_values = worksheet.get_all_values()

    if not all_values:
        return "Таблица пуста."

    headers = all_values[0]  # Шапка таблицы (A1, B1, ...)

    for row in all_values[1:]:
        if row and str(row[0]).strip() == str(order_number).strip():
            return "\n".join(
                f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))
            )

    return "Заказ не найден."


# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию по нему.")


# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    result = find_row_by_order(order_number)
    await update.message.reply_text(result)


# Создание Telegram-приложения
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Запуск бота при старте FastAPI (с учетом депрекейта on_event)
@app.on_event("startup")
async def startup_event():
    logger.info("✅ Бот запускается...")
    await app_telegram.initialize()
    await app_telegram.start()
    await app_telegram.updater.start_polling()


# Остановка бота
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("⛔ Остановка бота...")
    await app_telegram.updater.stop()
    await app_telegram.stop()
    await app_telegram.shutdown()


# Эндпоинт для проверки работоспособности
@app.get("/")
def read_root():
    return {"status": "бот работает"}


# Локальный запуск (для отладки)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
