import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Подключение к Google Таблице через переменную окружения
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_data = os.environ.get("GSPREAD_JSON")  # именно GSPREAD_JSON, не имя файла!
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_data), scope)
client = gspread.authorize(creds)

# Открываем таблицу по ID
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = spreadsheet.worksheet("СЦ")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, чтобы получить информацию.")

# Обработка сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    data = worksheet.get_all_records()

    result = next((row for row in data if str(row.get("Номер заказа")).strip() == user_input), None)

    if result:
        message = (
            f"Номер заказа: {result.get('Номер заказа')}\n"
            f"Клиент: {result.get('Клиент')}\n"
            f"Статус: {result.get('Статус')}"
        )
    else:
        message = "Ничего не найдено по этому номеру заказа."

    await update.message.reply_text(message)

# Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Не установлена переменная окружения BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен ...")
    app.run_polling()
