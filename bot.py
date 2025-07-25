import os
import json
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.get_worksheet(0)


def find_row_by_order(order_number):
    all_data = worksheet.get_all_values()
    headers = all_data[0]
    for row in all_data[1:]:
        if str(row[0]).strip() == str(order_number).strip():
            return "\n".join(f"{headers[i]}: {cell}" for i, cell in enumerate(row))
    return "Заказ не найден."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    result = find_row_by_order(order_number)
    await update.message.reply_text(result)


# Создаем Telegram-приложение (Application)
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# Lifespan (инициализация и завершение)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Бот запускается...")
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    yield
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()
    logger.info("🛑 Бот остановлен.")


# FastAPI-приложение с lifespan
app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"status": "бот работает"}
