import logging
import requests
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
DSCONTROL_API_KEY = '4746eacc66eb4adc8ea22bd321a62a5b'
DSCONTROL_URL = 'https://app.dscontrol.ru/api/Search'
INVITE_LINK = 'https://t.me/+GN1Ulgtpy3liNzFi'

(ASK_FIO, ASK_PHONE) = range(2)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([["Стать участником чата"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👋 Привет! Нажмите кнопку ниже, чтобы подать заявку в чат.", reply_markup=keyboard)

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ваше полное ФИО (например: Иванов Иван Иванович):")
    return ASK_FIO

async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fio'] = update.message.text.strip()
    await update.message.reply_text("Теперь введите номер телефона в формате +7XXXXXXXXXX:")
    return ASK_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fio = context.user_data['fio']
    phone = update.message.text.strip()

    if not phone.startswith("+7") or len(phone) < 11:
        await update.message.reply_text("⚠️ Некорректный формат номера. Введите номер в формате +7XXXXXXXXXX:")
        return ASK_PHONE

    await update.message.reply_text("🔍 Проверяем вас в базе автошколы...")

    if check_in_dscontrol(fio, phone):
        await update.message.reply_text(f"✅ Вы подтверждены! Вот ссылка на чат: {INVITE_LINK}")
    else:
        await update.message.reply_text("❌ К сожалению, вы не найдены в базе действующих курсантов и выпускников.")

    return ConversationHandler.END

def check_in_dscontrol(fio: str, phone: str) -> bool:
    query = f"{fio} {phone}"
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'api_key': DSCONTROL_API_KEY,
    }

    try:
        response = requests.get(DSCONTROL_URL, headers=headers, params={'query': query})
        data = response.json()
        for item in data.get("data", []):
            role = item.get("role", "").lower()
            if role in ["курсант", "выпускник"]:
                return True
    except Exception as e:
        logger.error(f"Ошибка при обращении к API: {e}")

    return False

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Стать участником чата)$"), start_registration)],
        states={
            ASK_FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("Бот запущен.")
    app.run_polling()

if __name__ == '__main__':
    main()
