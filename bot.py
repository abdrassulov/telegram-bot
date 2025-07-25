import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Загрузка переменных
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Логгер
logging.basicConfig(level=logging.INFO)

# Google Sheets auth
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# Поиск по номеру заказа
def find_row(order_number):
    headers = worksheet.row_values(1)
    all_data = worksheet.get_all_values()[1:]  # skip header
    for row in all_data:
        if row[0].strip() == order_number.strip():
            return "\n".join([f"{headers[i]}: {row[i]}" for i in range(len(headers))])
    return "\u274c \u0417аказ не найден."

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\ud83d\udc4b Привет! Отправь номер заказа, и я найду информацию.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = find_row(text)
    await update.message.reply_text(result)

# Сборка Telegram App
bot: Application = ApplicationBuilder().token(BOT_TOKEN).build()
bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI с lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("\u2705 Бот запущен...")
    await bot.initialize()
    await bot.start()
    await bot.set_webhook(f"{RENDER_EXTERNAL_URL}/webhook")
    yield
    await bot.stop()
    await bot.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot.bot)
    await bot.process_update(update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "bot is live"}
