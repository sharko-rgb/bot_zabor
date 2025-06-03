from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

TG_ADMIN_ID = 1346038165  # <-- Замените на ID администратора

# Состояния ConversationHandler
(
    MAIN_MENU,
    SELECT_FENCE_TYPE,
    DETAIL_OR_PRICE,
    CALC_LENGTH,
    CALC_HEIGHT,
    CALC_GATE,
    CONTACTS,
    WAITING_CONTACT,
    QUESTION_SPECIALIST
) = range(9)

FENCE_TYPES = [
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

PRICES = {
    "Забор из профнастила": {"1.8": 3474, "2.0": 3650},
    "Забор «профлист в рамке»": {"1.8": 6140, "2.0": 6500},
    "Евроштакетник вертикально": {"1.8": 7620, "2.0": 8260},
    "Евроштакетник горизонтально": {"1.8": 9650, "2.0": 10350},
    "Забор Жалюзи": {"1.8": 8700},
    "Забор Ранчо (двойной)": {"1.8": 14500},
    "Забор Ранчо (одинарный)": {"1.8": 11000},
    "Забор из 3Д сетки": {"1.8": 3100},
    "Ворота откатные": {"1.8": 87000, "2.0": 87000},
    "Ворота распашные + Калитка": {"1.8": 37000, "2.0": 37000},
    "Навесы для автомобиля": {}  # Цена по кв.м, рассчёт индивидуально
}

GATE_PRICES = {
    "Ворота": 87000,
    "Калитка": 37000,
    "Оба": 87000 + 37000,
    "Не нужно": 0
}

FENCE_DESCRIPTIONS = {
    "Забор из профнастила": "Прочный и долговечный забор из профилированного листа.",
    "Забор «профлист в рамке»": "Профлист, установленный в металлическую рамку для прочности.",
    "Евроштакетник вертикально": "Металлический евроштакетник, установленный вертикально в два ряда.",
    "Евроштакетник горизонтально": "Металлический евроштакетник, установленный горизонтально в два ряда.",
    "Забор Жалюзи": "Забор из металлических ламелей с двухсторонней полимерной окраской.",
    "Забор Ранчо (двойной)": "Двойной металлический забор Ранчо с возможностью комбинировать цвета.",
    "Забор Ранчо (одинарный)": "Одинарный забор Ранчо с двухсторонней полимерной окраской.",
    "Забор из 3Д сетки": "Прозрачный забор из 3D-сетки.",
    "Ворота откатные": "Откатные ворота из трубы проф.60х40 с фурнитурой Алютех.",
    "Ворота распашные + Калитка": "Распашные ворота с калиткой.",
    "Навесы для автомобиля": "Навесы с разными типами крыш — радиусные, односкатные, плоские."
}

# Начало работы, приветствие и главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Здравствуйте, Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов «под ключ», "
        "в том числе каменных, из кирпича и керамзитоблоков, также мы строим металлические навесы для автомобилей.\n\n"
        "Выберите пункт меню:"
    )
    keyboard = [
        ["1. Выбрать тип забора"],
        ["2. Рассчитать стоимость"],
        ["3. Оставить заявку на бесплатный замер"],
        ["4. Посмотреть примеры наших работ"],
        ["5. Задать вопрос специалисту"],
        ["6. Контакты"]
    ]
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return MAIN_MENU

# Обработка главного меню
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("1"):
        # Показать выбор типа забора
        keyboard = [[InlineKeyboardButton(f, callback_data=f)] for f in FENCE_TYPES]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Какой тип забора Вас интересует?", reply_markup=reply_markup)
        return SELECT_FENCE_TYPE
    elif text.startswith("2"):
        await update.message.reply_text("Для расчёта стоимости, пожалуйста, выберите тип забора первым через пункт 'Выбрать тип забора'.")
        return MAIN_MENU
    elif text.startswith("3"):
        await update.message.reply_text("Пожалуйста, отправьте заявку на замер в формате:\nИмя, Телефон, Адрес, Удобное время (если есть).")
        return WAITING_CONTACT
    elif text.startswith("4"):
        await update.message.reply_text("Вот примеры наших работ:\n(здесь можно добавить отправку фото)")
        return MAIN_MENU
    elif text.startswith("5"):
        await update.message.reply_text("Напишите ваш вопрос специалисту.")
        return QUESTION_SPECIALIST
    elif text.startswith("6"):
        contacts = (
            "Адрес: г. Тюмень, ул. Примерная, 1\n"
            "Телефон: +7 (3452) 00-00-00\n"
            "Email: info@zabory72.ru\n"
            "Сайт: https://zabory72.ru\n"
            "Время работы: Пн–Сб с 09:00 до 18:00"
        )
        await update.message.reply_text(contacts)
        return MAIN_MENU
    else:
        await update.message.reply_text("Пожалуйста, выберите пункт меню.")
        return MAIN_MENU

# Пользователь выбрал тип забора
async def fence_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_fence = query.data
    context.user_data['selected_fence'] = selected_fence

    keyboard = [
        [InlineKeyboardButton("Подробнее", callback_data="detail")],
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calc")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Вы выбрали: {selected_fence}\nОтлично! Хотите узнать подробнее и сразу рассчитать стоимость?",
        reply_markup=reply_markup
    )
    return DETAIL_OR_PRICE

# Обработка выбора Подробнее / Рассчитать / Назад
async def detail_or_calc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    selected_fence = context.user_data.get('selected_fence')

    if action == "detail":
        desc = FENCE_DESCRIPTIONS.get(selected_fence, "Описание отсутствует.")
        # Можно добавить фото — пока просто текст
        keyboard = [
            [InlineKeyboardButton("Рассчитать стоимость", callback_data="calc")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_fence_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🔹 {selected_fence}\n\n{desc}\n\nХотите рассчитать стоимость?", reply_markup=reply_markup)
        return DETAIL_OR_PRICE

    elif action == "calc":
        await query.edit_message_text("Введите протяжённость забора в метрах (число):")
        return CALC_LENGTH

    elif action == "back_to_menu":
        keyboard = [
            ["1. Выбрать тип забора"],
            ["2. Рассчитать стоимость"],
            ["3. Оставить заявку на бесплатный замер"],
            ["4. Посмотреть примеры наших работ"],
            ["5. Задать вопрос специалисту"],
            ["6. Контакты"]
        ]
        await query.edit_message_text(
            "Выберите пункт меню:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return MAIN_MENU

    elif action == "back_to_fence_selection":
        keyboard = [[InlineKeyboardButton(f, callback_data=f)] for f in FENCE_TYPES]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Какой тип забора Вас интересует?", reply_markup=reply_markup)
        return SELECT_FENCE_TYPE

# Ввод длины забора
async def calc_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        length = float(text.replace(',', '.'))
        if length <= 0:
            raise ValueError
        context.user_data['length'] = length
        # Далее выбираем высоту
        keyboard = [[InlineKeyboardButton("1.8"), InlineKeyboardButton("2.0")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите высоту забора:", reply_markup=reply_markup)
        return CALC_HEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число для длины забора:")
        return CALC_LENGTH

# Выбор высоты забора
async def calc_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    height = query.data
    if height not in ["1.8", "2.0"]:
        await query.message.reply_text("Пожалуйста, выберите высоту из вариантов.")
        return CALC_HEIGHT
    context.user_data['height'] = height
    # Выбираем ворота/калитку
    keyboard = [
        [InlineKeyboardButton("Ворота", callback_data="Ворота")],
        [InlineKeyboardButton("Калитка", callback_data="Калитка")],
        [InlineKeyboardButton("Оба", callback_data="Оба")],
        [InlineKeyboardButton("Не нужно", callback_data="Не нужно")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Нужны ли ворота или калитка?", reply_markup=reply_markup)
    return CALC_GATE

# Выбор ворот/калитки
async def calc_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gate_choice = query.data
    context.user_data['gate'] = gate_choice

    fence = context.user_data['selected_fence']
    length = context.user_data['length']
    height = context.user_data['height']

    # Рассчёт цены
    if fence in PRICES and height in PRICES[fence]:
        price_per_meter = PRICES[fence][height]
        fence_price = price_per_meter * length
    else:
        fence_price = None  # Цена по запросу

    gate_price = GATE_PRICES.get(gate_choice, 0)

    if fence_price is None:
        price_text = "Стоимость рассчитывается индивидуально. Свяжитесь с нами для точного расчёта."
    else:
        total = fence_price + gate_price
        price_text = (
            f"Предварительный расчёт:\n"
            f"{fence}, высота {height} м, длина {length} м = {fence_price:,.0f} ₽\n"
            f"Ворота/Калитка: {gate_price:,.0f} ₽\n"
            f"Итого: {total:,.0f} ₽"
        )
    keyboard = [[InlineKeyboardButton("Оставить заявку на замер", callback_data="leave_request")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_detail")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(price_text + "\n\nХотите оставить заявку на бесплатный замер?", reply_markup=reply_markup)
    return CONTACTS

# Возврат в подробности
async def back_to_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fence = context.user_data.get('selected_fence')
    desc = FENCE_DESCRIPTIONS.get(fence, "Описание отсутствует.")
    keyboard = [
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calc")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_fence_selection")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🔹 {fence}\n\n{desc}\n\nХотите рассчитать стоимость?", reply_markup=reply_markup)
    return DETAIL_OR_PRICE

# Запрос контактов для заявки
async def leave_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Пожалуйста, напишите ваше имя и телефон для связи:")
    return WAITING_CONTACT

# Получение контактов и отправка админу
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    fence = context.user_data.get('selected_fence', 'не указан')
    length = context.user_data.get('length', 'не указан')
    height = context.user_data.get('height', 'не указан')
    gate = context.user_data.get('gate', 'не указан')

    msg_to_admin = (
        f"Новая заявка от @{user.username} (id={user.id}):\n"
        f"Тип забора: {fence}\n"
        f"Длина: {length}\n"
        f"Высота: {height}\n"
        f"Ворота/Калитка: {gate}\n"
        f"Контакты: {text}"
    )
    await update.message.reply_text("Спасибо! Ваша заявка отправлена, с вами свяжутся в ближайшее время.", reply_markup=ReplyKeyboardRemove())

    await context.bot.send_message(TG_ADMIN_ID, msg_to_admin)
    return ConversationHandler.END

# Обработка вопроса специалисту
async def question_specialist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    msg = f"Вопрос от @{user.username} (id={user.id}):\n\n{text}"
    await context.bot.send_message(TG_ADMIN_ID, msg)
    await update.message.reply_text("Спасибо за вопрос! Наш специалист скоро ответит.")
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена. Чтобы начать заново, отправьте /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основной запуск приложения
def main():
    app = ApplicationBuilder().token("7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            SELECT_FENCE_TYPE: [CallbackQueryHandler(fence_type_chosen)],
            DETAIL_OR_PRICE: [CallbackQueryHandler(detail_or_calc_handler, pattern="^(detail|calc|back_to_menu|back_to_fence_selection)$")],
            CALC_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_length)],
            CALC_HEIGHT: [CallbackQueryHandler(calc_height)],
            CALC_GATE: [CallbackQueryHandler(calc_gate)],
            CONTACTS: [CallbackQueryHandler(leave_request_handler, pattern="^leave_request$"),
                       CallbackQueryHandler(back_to_detail, pattern="^back_to_detail$")],
            WAITING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            QUESTION_SPECIALIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_specialist)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()

















