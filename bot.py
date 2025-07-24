import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Подключение к Google Таблице
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("telegram-bot-466907-ef1c20c5199b.json", scope)
client = gspread.authorize(creds)

# ✅ Новый spreadsheet ID
spreadsheet = client.open_by_key("1Pjw1XZgeTGplzm5eJxKkExA4q5YvJjTD4wdptbn7tY8")
sheet = spreadsheet.worksheet("СЦ")  # имя листа

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь номер заказа или серийный номер, и я покажу информацию о товаре."
    )

# Обработка текста
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    data = sheet.get_all_values()
    headers = data[0]
    found = False

    for row in data[1:]:
        if query in (row[0], row[2]):  # ищем по столбцу A и C
            result = "\n".join([f"{headers[i]}: {cell}" for i, cell in enumerate(row)])
            await update.message.reply_text(f"Вот информация о заказе:\n\n{result}")
            found = True
            break

    if not found:
        await update.message.reply_text("Ничего не найдено. Проверь номер заказа или серийный номер.")

# Инициализация бота
app = ApplicationBuilder().token("7289717705:AAFM9iaZWmecqPwRqX8M5oh0FYsc5jB5H78").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен ...")
app.run_polling()
