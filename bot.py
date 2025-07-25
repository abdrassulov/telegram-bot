import os
import json
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from dotenv import load_dotenv

# === Загрузка .env переменных ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Обязательно в Render

# === Подключение к Google Sheets ===
service_account_info = json.loads(GSPREAD_JSON)
gc = gspread.service_account_from_dict(service_account_info)

spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)

# === Инициализация FastAPI и Telegram Application ===
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# === Обработка команды /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду информацию.")

# === Поиск строки по номеру заказа и возврат пар "шапка — значение" ===
def find_row_pairs(order_number: str) -> str:
    all_values = worksheet.get_all_values()
    if not all_values or len(all_values) < 2:
        return "Таблица пуста или в ней недостаточно строк."

    headers = all_values[0]
    for row in all_values[1:]:
        if row[0].strip() == order_number.strip():  # A столбец — номер заказа
            pairs = []
            for i in range(len(headers)):
                key = headers[i]
                value = row[i] if i < len(row) else ""
                pairs.append(f"{key}: {value}")
            return "\n".join(pairs)
    return "Заказ не найден."

# === Обработка текстовых сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_number = update.message.text.strip()
    response = find_row_pairs(order_number)
    await update.message.reply_text(response)

# === Добавление обработчиков ===
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Webhook endpoint ===
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# === Lifespan события (запуск/остановка) ===
@app.on_event("startup")
async def on_startup():
    logging.basicConfig(level=logging.INFO)
    logging.info("✅ Бот запускается...")
    await application.initialize()
    await application.start()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    logging.info(f"📡 Webhook установлен: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("⛔ Остановка бота...")
    await application.bot.delete_webhook()
    await application.stop()
    await application.shutdown()

# === Корневая страница ===
@app.get("/")
def root():
    return {"status": "бот работает"}

# === Для локального запуска ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=10000)
