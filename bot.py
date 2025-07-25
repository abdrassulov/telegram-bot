import os
import json
import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    AIORateLimiter,
    filters
)
import gspread
from dotenv import load_dotenv

# Загрузка .env переменных
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # например: https://your-app.onrender.com

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка доступа к Google Таблице
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)  # первая вкладка

# Бот
app_tg: Application = ApplicationBuilder() \
    .token(BOT_TOKEN) \
    .rate_limiter(AIORateLimiter()) \
    .build()


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию по нему.")


# Обработка номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    data = worksheet.get_all_values()
    headers = data[0]
    rows = data[1:]
    for row in rows:
        if row[0].strip() == order_number:  # номер заказа в первом столбце
            response = "\n".join(f"{headers[i]} — {cell}" for i, cell in enumerate(row))
            await update.message.reply_text(response)
            return
    await update.message.reply_text("❌ Заказ не найден.")


# Обработчики Telegram
app_tg.add_handler(CommandHandler("start", start))
app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Telegram-бота...")
    await app_tg.initialize()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await app_tg.bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook установлен: {webhook_url}")
    yield
    logger.info("🛑 Остановка Telegram-бота...")
    await app_tg.shutdown()


# FastAPI приложение
app = FastAPI(lifespan=lifespan)


# Роут для webhook
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_tg.bot)
    await app_tg.process_update(update)
    return {"ok": True}


# Проверка работоспособности
@app.get("/")
def root():
    return {"status": "Бот работает 🎉"}
