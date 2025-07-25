import os
import json
import logging
import asyncio

import httpx
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Инициализация FastAPI (для Render)
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bot is running"}

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GSPREAD_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(creds)

# Подключение к таблице
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8/edit#gid=0")
worksheet = spreadsheet.get_worksheet(0)  # Первый лист

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь номер заказа, и я найду информацию.")

# Обработка номера заказа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    order_number = update.message.text.strip()
    logging.info(f"Ищем заказ: {order_number}")

    try:
        data = worksheet.get_all_records()
        headers = worksheet.row_values(1)

        for row in data:
            if str(row.get("Номер заказа")).strip() == order_number:
                message = "\n".join(f"{header}: {row.get(header, '')}" for header in headers)
                await update.message.reply_text(message)
                return

        await update.message.reply_text("Номер заказа не найден.")
    except Exception as e:
        logging.exception("Ошибка при поиске заказа")
        await update.message.reply_text(f"Ошибка: {e}")

# Основная функция запуска
async def main():
    app_telegram = Application.builder().token(BOT_TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен")
    await app_telegram.run_polling()

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
