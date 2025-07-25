import os
import json
import gspread
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# Инициализация FastAPI (для Render)
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot is running"}

# Логгинг
logging.basicConfig(level=logging.INFO)

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GSPREAD_JSON = os.getenv("GSPREAD_JSON")

# Парсим JSON ключ
json_data = json.loads(GSPREAD_JSON)

# Авторизация в Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_data, scope)
gc = gspread.authorize(credentials)

# Открываем таблицу
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/СПИСОК_ID_ИЛИ_URL")
worksheet = spreadsheet.sheet1

# Основная логика: поиск по номеру заказа
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    try:
        data = worksheet.get_all_values()
        headers = data[0]
        for row in data[1:]:
            if row[0] == query:
                response = "\n".join(
                    f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row)))
                )
                await update.message.reply_text(f"Вот информация о заказе:\n\n{response}")
                return
        await update.message.reply_text("Заказ не найден.")
    except Exception as e:
        await update.message.reply_text("Ошибка при обработке запроса.")
        logging.exception("Ошибка:")

# Запуск бота
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", handle_order))
    application.add_handler(CommandHandler("help", handle_order))
    application.add_handler(CommandHandler("order", handle_order))
    application.add_handler(CommandHandler("заказ", handle_order))
    application.add_handler(CommandHandler("номер", handle_order))
    application.add_handler(CommandHandler("номер_заказа", handle_order))
    application.add_handler(CommandHandler("номерзаказа", handle_order))

    application.add_handler(CommandHandler(None, handle_order))
    await application.run_polling()

import asyncio
asyncio.create_task(main())
