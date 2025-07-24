import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_data = os.environ.get("GSPREAD_JSON")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_data), scope)
client = gspread.authorize(creds)

# Открываем таблицу
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = spreadsheet.worksheet("СЦ")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, чтобы получить всю информацию.")

# Сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # Все данные
    all_data = worksheet.get_all_values()
    headers = all_data[0]  # первая строка = шапка
    rows = all_data[1:]    # остальные строки = данные

    # Поиск строки
    result = None
    for row in rows:
        if row[0].strip() == user_input:
            result = row
            break

    # Формируем ответ
    if result:
        lines = []
        for i in range(len(headers)):
            key = headers[i].strip()
            value = result[i].strip() if i < len(result) else ""
            lines.append(f"{key}: {value}")
        message = "Вот информация о заказе:\n" + "\n".join(lines)
    else:
        message = "Ничего не найдено по этому номеру заказа."

    await update.message.reply_text(message)

# Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен ...")
    app.run_polling()
