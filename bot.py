import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Логирование
logging.basicConfig(level=logging.INFO)

# Авторизация Google Sheets через переменную окружения
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
json_data = os.environ.get("GSPREAD_JSON")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(json_data), scope)
client = gspread.authorize(creds)

# Подключение к таблице и листу
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
worksheet = spreadsheet.worksheet("СЦ")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь номер заказа, и я найду всю информацию.")

# Обработка сообщения (поиск заказа)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    all_values = worksheet.get_all_values()

    headers = all_values[0]
    found_row = None

    for row in all_values[1:]:
        if row and row[0].strip() == user_input:
            found_row = row
            break

    if found_row:
        lines = ["Вот информация о заказе:"]
        for i in range(len(headers)):
            key = headers[i].strip() if i < len(headers) else f"Столбец {i+1}"
            value = found_row[i].strip() if i < len(found_row) else ""
            lines.append(f"{key}: {value}")
        await update.message.reply_text("\n".join(lines))
    else:
        await update.message.reply_text("Ничего не найдено по этому номеру заказа.")

# Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Переменная окружения BOT_TOKEN не установлена")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()
