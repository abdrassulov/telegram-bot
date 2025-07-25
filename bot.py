import os
import json
import logging
from contextlib import asynccontextmanager

import gspread
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# === Загрузка переменных окружения ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # https://your-app.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# === Telegram Application ===
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# === Настройка логов ===
logging.basicConfig(level=logging.INFO)

# === Google Sheets ===
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# === Поиск данных по номеру заказа ===
def find_order(order_number: str) -> str:
    headers = worksheet.row_values(1)
    all_rows = worksheet.get_all_values()[1:]
    for row in all_rows:
        if row[0].strip() == order_number.strip():
            return "\n".join(f"{headers[i]}: {row[i]}" for i in range(len(headers)) if i < len(row))
    return "❌ Заказ не найден."

# === Обработка команд ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Отправь номер заказа — я пришлю информацию.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = update.message.text.strip()
    result = find_order(order)
    await update.message.reply_text(result)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# === Жизненный цикл приложения ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🔁 Инициализация Telegram Webhook...")
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    yield
    logging.info("🛑 Остановка Telegram Webhook...")
    await telegram_app.bot.delete_webhook()
    await telegram_app.shutdown()

# === FastAPI Приложение ===
app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "✅ бот работает", "webhook": WEBHOOK_URL}
