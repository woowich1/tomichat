import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)



BOT_TOKEN = '7634211288:AAF2hG1BQaq_K4iVZM_NcJIkusq3O66MHSA'
INVITE_LINK = 'https://t.me/+GN1Ulgtpy3liNzFi'
ADMIN_CHAT_ID = 7533995960  # ← вставь свой chat_id

ASK_FIO = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet

def check_fio_in_sheet(fio: str) -> bool:
    sheet = get_sheet()
    fio_list = sheet.col_values(1)
    fio_cleaned = fio.strip().lower()
    for row_fio in fio_list:
        if row_fio.strip().lower() == fio_cleaned:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([["Стать участником чата"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Нажмите кнопку ниже, чтобы подать заявку в чат.", reply_markup=keyboard)
    await update.message.reply_text(f"Ваш chat_id: {update.message.chat_id}")

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ваше полное ФИО (например: Иванов Иван Иванович):")
    return ASK_FIO

async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fio = update.message.text.strip()
    if len(fio.split()) < 2:
        await update.message.reply_text("⚠️ Пожалуйста, введите как минимум имя и фамилию.")
        return ASK_FIO

    await update.message.reply_text("🔍 Проверяем вас в базе...")

    try:
        if check_fio_in_sheet(fio):
            await update.message.reply_text(f"✅ Вы подтверждены! Вот ссылка на чат:{INVITE_LINK}")
        else:
            await update.message.reply_text("❌ Вы не найдены среди курсантов.")
    except Exception as e:
        error_text = f"❗️Ошибка доступа к таблице:{e}"
        await update.message.reply_text("⚠️ Возникла ошибка. Мы уже разбираемся.")
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=error_text)
        except Exception as ex:
            logger.error(f"Не удалось уведомить администратора: {ex}")

    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Стать участником чата)$"), start_registration)],
        states={
            ASK_FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("Бот запущен.")
    app.run_polling()

if __name__ == '__main__':
    main()
