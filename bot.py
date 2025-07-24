import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Логирование
logging.basicConfig(level=logging.INFO)

# Авторизация Google
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_data = os.environ.get("GSPREAD_JSON")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_data), scope)
client = gspread.authorize(creds)

# Открытие таблицы и листа
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = spreadsheet.worksheet("СЦ")

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду всю информацию.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    all_values = worksheet.get_all_values()  # Получаем ВСЕ данные как список списков
    headers = all_values[0]  # Первая строка — это заголовки
    rows = all_values[1:]    # Остальные строки — данные

    # Ищем строку, где в колонке A совпадает номер заказа
    result_row = None
    for row in rows:
        if len(row) > 0 and row[0].strip() == user_input:
            result_row = row
            break

    if result_row:
        response_lines = [f"{headers[i]}: {result_row[i] if i < len(result_row) else ''}" for i in range(len(headers))]
        message = "Вот информация о заказе:\n" + "\n".join(response_lines)
    else:
        message = "Ничего не найдено по этому номеру заказа."

    await update.message.reply_text(message)

# Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()
