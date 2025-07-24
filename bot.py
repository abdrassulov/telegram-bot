import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_data = os.environ.get("GSPREAD_JSON")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_data), scope)
client = gspread.authorize(creds)

# Подключение к таблице
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = spreadsheet.worksheet("СЦ")  # Название листа

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, чтобы получить информацию.")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    all_data = worksheet.get_all_values()

    headers = all_data[0]  # первая строка — заголовки
    rows = all_data[1:]    # остальные строки — данные

    result_row = None
    for row in rows:
        if row[0].strip() == user_input:  # ищем по первой колонке
            result_row = row
            break

    if result_row:
        message = "Вот информация о заказе:\n\n"
        for i in range(len(result_row)):
            header = headers[i] if i < len(headers) else f"Поле {i+1}"
            value = result_row[i]
            message += f"{header}: {value}\n"
    else:
        message = "Ничего не найдено по этому номеру заказа."

    await update.message.reply_text(message)

# Запуск бота
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Не установлена переменная окружения BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен ...")
    app.run_polling()
