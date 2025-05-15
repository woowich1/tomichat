import logging
import re
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
ADMIN_CHAT_ID = 7533995960  # ← вставь свой chat_id
ASK_FIO = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    await update.message.reply_text("🔍 Проверяем вас в базе автошколы...")

    try:
        if check_in_dscontrol(fio):
            await update.message.reply_text(f"✅ Вы подтверждены! Вот ссылка на чат:{INVITE_LINK}")
        else:
            await update.message.reply_text("❌ Вы не найдены среди действующих курсантов и выпускников.")
    except Exception as e:
        error_text = f"❗️Ошибка проверки:{e}"
        await update.message.reply_text("⚠️ Возникла внутренняя ошибка. Мы уже разбираемся.")
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=error_text)
        except Exception as ex:
            logger.error(f"Не удалось отправить сообщение админу: {ex}")

    return ConversationHandler.END

def check_in_dscontrol(fio: str) -> bool:
    query = fio
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'api_key': DSCONTROL_API_KEY,
    }

    try:
        response = requests.get(DSCONTROL_URL, headers=headers, params={'search': query})
        data = response.json()
        logger.warning(f"[DEBUG] Ответ API: {data}")

        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("data", [])
        else:
            raise Exception(f"Неизвестный формат ответа: {type(data)}")

        for item in results:
            if not isinstance(item, dict):
                continue

            if item.get("Type", "").lower() == "student":
                role = item.get("Role") or item.get("role") or item.get("Status") or item.get("status") or ""
                role = role.lower()
                if role in ("курсант", "выпускник", "student", "graduate"):
                    return True

    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        raise Exception(f"Ошибка API: {e}")

    return False

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
