import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackContext,
    filters
)
import gspread
from dotenv import load_dotenv
import asyncio
import telegram

# Загружаем переменные окружения
load_dotenv()

# Инициализируем логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI-приложение
app = FastAPI()

# Получаем токены и данные из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # https://your-app-name.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# Подключаемся к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)

# Создаем объект Telegram бота
bot = Bot(token=BOT_TOKEN)

# Telegram Application
telegram_app = Application.builder().token(BOT_TOKEN).build()


# Функция поиска строки по номеру заказа
def find_row_by_order_number(order_number: str) -> str:
    sheet_data = worksheet.get_all_values()
    headers = sheet_data[0]

    for row in sheet_data[1:]:
        if row[0].strip() == order_number.strip():
            response = []
            for i in range(len(headers)):
                if i < len(row):
                    response.append(f"{headers[i]}: {row[i]}")
            return "\n".join(response)
    return "❌ Заказ не найден."


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь номер заказа, и я найду информацию.")


# Обработчик текста (номер заказа)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    result = find_row_by_order_number(user_input)
    await update.message.reply_text(result)


# Добавляем хендлеры
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# Запуск бота при старте приложения
@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен")
    asyncio.create_task(telegram_app.initialize())
    asyncio.create_task(telegram_app.start())


# Остановка бота
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()
    logger.info("🛑 Бот остановлен")


# Обработка webhook запросов от Telegram
@app.post(WEBHOOK_PATH)
async def process_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await telegram_app.update_queue.put(update)
    return {"status": "ok"}


# Страница здоровья
@app.get("/")
def read_root():
    return {"status": "бот запущен"}
