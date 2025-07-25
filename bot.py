import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    AIORateLimiter,
)
from gspread import service_account_from_dict
from dotenv import load_dotenv

load_dotenv()

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Пример: https://telegram-bot-abc1.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# Telegram-приложение
telegram_app = Application.builder() \
    .token(BOT_TOKEN) \
    .rate_limiter(AIORateLimiter()) \
    .build()

# Подключение к Google Таблице
service_account_info = json.loads(GSPREAD_JSON)
gc = service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)


def find_row(order_number: str) -> str:
    all_data = worksheet.get_all_values()
    headers = all_data[0]
    for row in all_data[1:]:
        if str(row[0]).strip() == str(order_number).strip():
            return "\n".join(f"{headers[i]}: {row[i]}" for i in range(len(headers)) if i < len(row))
    return "Заказ не найден."


# Обработчики Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне номер заказа, и я покажу информацию.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text
    result = find_row(order_number)
    await update.message.reply_text(result)


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# FastAPI приложение
app = FastAPI()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return JSONResponse(content={"ok": True})


@app.get("/")
def home():
    return {"status": "бот работает"}


@app.on_event("startup")
async def on_startup():
    logger.info("✅ Установка webhook...")
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    await telegram_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.bot.delete_webhook()
    await telegram_app.stop()
    await telegram_app.shutdown()
