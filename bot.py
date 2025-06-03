import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters

logging.basicConfig(level=logging.INFO)

TG_ADMIN_ID = 1346038165  # Замените на реальный Telegram ID администратора

menu_buttons = [[
    "🔩 Выбрать тип забора",
    "💰 Рассчитать стоимость"
], [
    "📐 Оставить заявку на бесплатный замер",
    "🖼 Посмотреть примеры работ"
], [
    "❓ Задать вопрос специалисту",
    "📞 Контакты"
]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Вы обратились в компанию Zabory72.ru — супермаркет металлических заборов под ключ...",
        reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📐 Оставить заявку на бесплатный замер":
        await update.message.reply_text("Введите ваше имя:")
        return 1
    elif text == "❓ Задать вопрос специалисту":
        await update.message.reply_text("Пожалуйста, напишите ваш вопрос:")
        return 10
    elif text == "🖼 Посмотреть примеры работ":
        await update.message.reply_photo(photo=InputFile("photo1.jpg"), caption="Забор Жалюзи, г. Тюмень")
        return ConversationHandler.END
    elif text == "📞 Контакты":
        await update.message.reply_text(
            "г. Тюмень, ул. Примерная, 1\nТел: +7 (3452) 00-00-00\nEmail: info@zabory72.ru\nВремя работы: Пн–Сб с 09:00 до 18:00"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт из меню.")
        return ConversationHandler.END

# Заявка на замер
user_data = {}

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['name'] = update.message.text
    await update.message.reply_text("Введите ваш телефон:")
    return 2

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['phone'] = update.message.text
    await update.message.reply_text("Введите адрес:")
    return 3

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['address'] = update.message.text
    await update.message.reply_text("Удобное время (необязательно):")
    return 4

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['time'] = update.message.text
    message = f"📥 Новая заявка на замер\nИмя: {user_data['name']}\nТелефон: {user_data['phone']}\nАдрес: {user_data['address']}\nВремя: {user_data['time']}"
    await context.bot.send_message(chat_id=TG_ADMIN_ID, text=message)
    await update.message.reply_text("Спасибо! Мы свяжемся с вами в ближайшее время.")
    return ConversationHandler.END

# Вопрос специалисту
async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    question = update.message.text
    message = f"📥 Вопрос от пользователя @{user.username if user.username else user.id}:\n{question}"
    await context.bot.send_message(chat_id=TG_ADMIN_ID, text=message)
    await update.message.reply_text("Спасибо! Специалист ответит вам в ближайшее время.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token("7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0").build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_question)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()
















