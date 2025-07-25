import os
import logging
import asyncio
import json

from fastapi import FastAPI
from contextlib import asynccontextmanager
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к Google Таблице
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GSPREAD_JSON), scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = sheet.sheet1

# Создаём Telegram Application
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()


# === HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    try:
        records = worksheet.get_all_records()
        for row in records:
            if str(row["Номер заказа"]) == order_number:
                msg = "\n".join([f"{k}: {v}" for k, v in row.items()])
                await update.message.reply_text(f"🧾 Заказ найден:\n{msg}")
                return
        await update.message.reply_text("❌ Заказ не найден.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка при обработке.")


# === Регистрируем обработчики ===
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# === FastAPI с lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Бот запускается")
    asyncio.create_task(app_telegram.run_polling())
    yield
    logger.info("🛑 Бот остановлен")

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Бот работает"}
