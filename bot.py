import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, CallbackQueryHandler, filters

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

fence_types = [
    "Забор из профнастила",
    "Забор «профлист в рамке»",
    "Евроштакетник вертикально",
    "Евроштакетник горизонтально",
    "Забор Жалюзи",
    "Забор Ранчо (двойной)",
    "Забор Ранчо (одинарный)",
    "Забор из 3Д сетки",
    "Ворота откатные",
    "Ворота распашные + Калитка",
    "Навесы для автомобиля"
]

price_table = {
    "Забор из профнастила": {"1.8": 3474, "2.0": 3650},
    "Забор «профлист в рамке»": {"1.8": 6140, "2.0": 6500},
    "Евроштакетник вертикально": {"1.8": 7620, "2.0": 8260},
    "Евроштакетник горизонтально": {"1.8": 9650, "2.0": 10350},
    "Забор Жалюзи": {"1.8": 8700},
    "Забор Ранчо (двойной)": {"1.8": 14500},
    "Забор Ранчо (одинарный)": {"1.8": 11000},
    "Забор из 3Д сетки": {"1.8": 3100},
    "Ворота откатные": {"1.8": 87000},
    "Ворота распашные + Калитка": {"1.8": 37000},
    "Навесы для автомобиля": {"1.8": 7500}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Вы обратились в компанию Zabory72.ru — супермаркет металлических заборов под ключ, в том числе каменных, из кирпича и керамзитоблоков. Также мы строим металлические навесы для автомобилей.\n\nЧем можем помочь?",
        reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔩 Выбрать тип забора":
        keyboard = [[KeyboardButton(ftype)] for ftype in fence_types]
        await update.message.reply_text("Какой тип забора Вас интересует?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return 20
    elif text == "💰 Рассчитать стоимость":
        await update.message.reply_text("Введите протяжённость забора (в метрах):")
        return 30
    elif text == "📐 Оставить заявку на бесплатный замер":
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
            "г. Тюмень, ул. Примерная, 1\nТел: +7 (3452) 00-00-00\nEmail: info@zabory72.ru\nСайт: https://zabory72.ru\nВремя работы: Пн–Сб с 09:00 до 18:00"
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
    message = f"📥 Новая заявка на замер\n👤 ID: {update.message.from_user.id}\nИмя: {user_data['name']}\nТелефон: {user_data['phone']}\nАдрес: {user_data['address']}\nВремя: {user_data['time']}"
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

# Выбор типа забора
async def fence_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fence = update.message.text
    await update.message.reply_text(f"Отлично! Вы выбрали: {fence}. Хотите узнать подробнее или сразу рассчитать стоимость?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Подробнее", callback_data="details"), InlineKeyboardButton("Рассчитать стоимость", callback_data="calc")]
        ])
    )
    return ConversationHandler.END

# Расчёт стоимости
calc_data = {}

async def get_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        calc_data['length'] = float(update.message.text)
        await update.message.reply_text("Введите высоту забора (1.8 или 2.0):")
        return 31
    except ValueError:
        await update.message.reply_text("Введите число.")
        return 30

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calc_data['height'] = update.message.text
    keyboard = [[KeyboardButton(ftype)] for ftype in fence_types]
    await update.message.reply_text("Выберите тип забора:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return 32

async def get_fence_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calc_data['type'] = update.message.text
    await update.message.reply_text("Нужны ли ворота или калитка? (Ворота, Калитка, Оба, Не нужно):")
    return 33

async def get_extras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calc_data['extra'] = update.message.text
    base_price = price_table.get(calc_data['type'], {}).get(calc_data['height'], 0)
    total = base_price * calc_data['length']
    if calc_data['extra'] == "Ворота":
        total += 20000
    elif calc_data['extra'] == "Калитка":
        total += 10000
    elif calc_data['extra'] == "Оба":
        total += 30000
    await update.message.reply_text(f"Примерная стоимость: {int(total)} руб.\nВведите ваше имя для точного расчёта:")
    return 34

async def get_contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    await update.message.reply_text("Введите ваш телефон:")
    return 35

async def get_contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    message = f"📥 Расчёт стоимости\n👤 ID: {update.message.from_user.id}\nТип: {calc_data['type']}\nДлина: {calc_data['length']} м\nВысота: {calc_data['height']}\nДополнительно: {calc_data['extra']}\nТелефон: {phone}"
    await context.bot.send_message(chat_id=TG_ADMIN_ID, text=message)
    await update.message.reply_text("Спасибо! Мы свяжемся с вами для точного расчёта.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token("7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0").build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            1: [MessageHandler(filters.TEXT, get_name)],
            2: [MessageHandler(filters.TEXT, get_phone)],
            3: [MessageHandler(filters.TEXT, get_address)],
            4: [MessageHandler(filters.TEXT, get_time)],
            10: [MessageHandler(filters.TEXT, get_question)],
            20: [MessageHandler(filters.TEXT, fence_choice)],
            30: [MessageHandler(filters.TEXT, get_length)],
            31: [MessageHandler(filters.TEXT, get_height)],
            32: [MessageHandler(filters.TEXT, get_fence_type)],
            33: [MessageHandler(filters.TEXT, get_extras)],
            34: [MessageHandler(filters.TEXT, get_contact_name)],
            35: [MessageHandler(filters.TEXT, get_contact_phone)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()
















