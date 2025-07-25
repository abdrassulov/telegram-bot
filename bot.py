import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv
import gspread
import asyncio

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Подключение к Google Sheets
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

# Подключение к нужному листу
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0"
worksheet = gc.open_by_url(SPREADSHEET_URL).sheet1

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём FastAPI и Telegram Application
app = FastAPI()
telegram_app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# 📦 Хендлер /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я пришлю его данные из таблицы.")

# 🔍 Поиск строки по номеру заказа
def find_row_by_order(order_number: str) -> str:
    values = worksheet.get_all_values()
    if not values or len(values) < 2:
        return "Таблица пуста или не содержит данных."

    headers = values[0]
    for row in values[1:]:
        if row[0].strip() == order_number.strip():  # Первый столбец — номер заказа
            return "\n".join([f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))])
    return "Заказ не найден."

# 📩 Обработка сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    response = find_row_by_order(order_number)
    await update.message.reply_text(response)

# 🔗 Обработка входящих запросов от Telegram (webhook)
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# 🚀 Lifespan вместо on_event
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    await telegram_app.initialize()
    await telegram_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

# Проверка статуса
@app.get("/")
async def root():
    return {"status": "Бот работает!"}

# 🔃 Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
