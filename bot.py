import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
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

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я пришлю детали.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    headers = worksheet.row_values(1)
    all_rows = worksheet.get_all_values()

    for row in all_rows[1:]:
        if row[0].strip() == order_number:
            response = "\n".join([f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))])
            await update.message.reply_text(response)
            return
    await update.message.reply_text("❌ Заказ не найден.")

# FastAPI приложение
app = FastAPI()
bot_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.on_event("startup")
async def on_startup():
    logging.info("✅ Запуск бота")
    await bot_app.initialize()
    await bot_app.bot.delete_webhook()
    await bot_app.bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
    logging.info("📡 Webhook установлен")

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.shutdown()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "бот работает"}
