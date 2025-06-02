import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # Ваш Telegram ID

# Состояния для ConversationHandler
(
    MAIN_MENU,
    CHOOSING_FENCE,
    ENTER_LENGTH,
    ENTER_HEIGHT,
    CHOOSE_GATE,
    CONFIRMATION,
    ENTER_NAME,
    ENTER_PHONE,
    ASK_QUESTION,
    CONFIRM_QUESTION,
) = range(10)

# Локализация сообщений
MESSAGES = {
    "welcome": "Здравствуйте! Вы в компании Zabory72.ru. Выберите действие:",
    "choose_fence": "Выберите тип забора:",
    "enter_length": "Введите протяженность забора в метрах (число, например: 10 или 15.5):",
    "enter_height": "Введите высоту забора в метрах (число, например: 1.5):",
    "choose_gate": "Выберите, нужны ли ворота или калитка:",
    "enter_name": "Пожалуйста, введите ваше имя:",
    "enter_phone": "Введите ваш телефон (например: +7 999 123-45-67):",
    "invalid_number": "Неверный формат. Введите положительное число (пример: 12.5):",
    "invalid_phone": "Неверный формат телефона. Попробуйте еще раз.",
    "confirm_order": "Пожалуйста, подтвердите заявку:\n\n{summary}",
    "order_sent": "Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.",
    "cancelled": "Действие отменено. Главное меню:",
    "main_menu": "Главное меню",
    "ask_question": "Задайте ваш вопрос специалисту:",
    "confirm_question": "Вы уверены, что хотите отправить этот вопрос?",
    "question_sent": "Ваш вопрос отправлен специалисту. Спасибо!",
    "back_button": "⬅ Назад",
    "main_menu_button": "🏠 Главное меню",
}

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Выбрать тип забора", callback_data="choose_fence")],
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate_price")],
        [InlineKeyboardButton("Оставить заявку на замер", callback_data="order_measurement")],
        [InlineKeyboardButton("Посмотреть примеры работ", callback_data="show_examples")],
        [InlineKeyboardButton("Задать вопрос специалисту", callback_data="ask_specialist")],
        [InlineKeyboardButton("Контакты", callback_data="contacts")],
    ])

def fence_type_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Профнастил", callback_data="fence_prof")],
        [InlineKeyboardButton("Сетка-рабица", callback_data="fence_mesh")],
        [InlineKeyboardButton("Металлопрофиль", callback_data="fence_metal")],
        [InlineKeyboardButton("Деревянный забор", callback_data="fence_wood")],
        [InlineKeyboardButton("Штакетник", callback_data="fence_shtaketnik")],
        [InlineKeyboardButton("Еврозабор (бетонный)", callback_data="fence_euro")],
        [InlineKeyboardButton("Другой / Не уверен", callback_data="fence_other")],
        [InlineKeyboardButton(MESSAGES["back_button"], callback_data="back_to_main")],
    ])

def gate_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ворота", callback_data="gate_gate")],
        [InlineKeyboardButton("Калитка", callback_data="gate_door")],
        [InlineKeyboardButton("Ворота и калитка", callback_data="gate_both")],
        [InlineKeyboardButton("Не нужно", callback_data="gate_none")],
        [InlineKeyboardButton(MESSAGES["back_button"], callback_data="back_to_length")],
    ])

def confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Подтвердить ✅", callback_data="confirm_yes")],
        [InlineKeyboardButton("Отменить ❌", callback_data="confirm_no")],
        [InlineKeyboardButton(MESSAGES["back_button"], callback_data="back_to_main")],
    ])

def main_menu_button_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MESSAGES["main_menu_button"], callback_data="back_to_main")]
    ])

# Валидация телефона по простой регулярке (российские номера)
PHONE_REGEX = re.compile(r"^\+7\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$")

# --- Хендлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MESSAGES["welcome"],
        reply_markup=main_menu_kb()
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Очистим данные при входе в меню
    if data == "back_to_main":
        context.user_data.clear()
        await query.edit_message_text(MESSAGES["welcome"], reply_markup=main_menu_kb())
        return MAIN_MENU

    if data == "choose_fence":
        await query.edit_message_text(MESSAGES["choose_fence"], reply_markup=fence_type_kb())
        return CHOOSING_FENCE

    if data.startswith("fence_"):
        fence_type = data[6:]
        context.user_data["fence_type"] = fence_type
        await query.edit_message_text(MESSAGES["enter_length"], reply_markup=main_menu_button_kb())
        return ENTER_LENGTH

    if data == "calculate_price":
        await query.edit_message_text(MESSAGES["enter_length"], reply_markup=main_menu_button_kb())
        return ENTER_LENGTH

    if data == "back_to_length":
        await query.edit_message_text(MESSAGES["enter_length"], reply_markup=main_menu_button_kb())
        return ENTER_LENGTH

    if data == "back_to_height":
        await query.edit_message_text(MESSAGES["enter_height"], reply_markup=main_menu_button_kb())
        return ENTER_HEIGHT

    if data == "back_to_gate":
        await query.edit_message_text(MESSAGES["choose_gate"], reply_markup=gate_kb())
        return CHOOSE_GATE

    if data == "order_measurement":
        await query.edit_message_text(MESSAGES["enter_name"], reply_markup=main_menu_button_kb())
        return ENTER_NAME

    if data == "ask_specialist":
        await query.edit_message_text(MESSAGES["ask_question"], reply_markup=main_menu_button_kb())
        return ASK_QUESTION

    if data == "show_examples":
        await query.edit_message_text(
            "Примеры наших работ:\nhttps://example.com/works",
            reply_markup=main_menu_kb()
        )
        return MAIN_MENU

    if data == "contacts":
        await query.edit_message_text(
            "Наши контакты:\n"
            "Телефон: +7 123 456 78 90\n"
            "Email: info@zabory72.ru\n"
            "Сайт: https://zabory72.ru",
            reply_markup=main_menu_kb()
        )
        return MAIN_MENU

    if data.startswith("gate_"):
        gate = data[5:]
        context.user_data["gate"] = gate
        await query.edit_message_text(MESSAGES["enter_name"], reply_markup=main_menu_button_kb())
        return ENTER_NAME

    if data == "confirm_yes":
        # Отправляем заявку админу
        d = context.user_data
        summary = (
            f"<b>Новая заявка</b>\n"
            f"Забор: {d.get('fence_type', 'не выбран')}\n"
            f"Длина: {d.get('length', 'не указана')} м\n"
            f"Высота: {d.get('height', 'не указана')} м\n"
            f"Ворота/калитка: {d.get('gate', 'не указано')}\n"
            f"Имя: {d.get('name')}\n"
            f"Телефон: {d.get('phone')}"
        )
        await query.edit_message_text(MESSAGES["order_sent"], reply_markup=main_menu_kb())
        await context.bot.send_message(ADMIN_ID, summary, parse_mode="HTML")
        context.user_data.clear()
        return MAIN_MENU

    if data == "confirm_no":
        await query.edit_message_text(MESSAGES["cancelled"], reply_markup=main_menu_kb())
        context.user_data.clear()
        return MAIN_MENU

    if data == "cancel":
        await query.edit_message_text(MESSAGES["cancelled"], reply_markup=main_menu_kb())
        context.user_data.clear()
        return MAIN_MENU

    await query.answer("Неизвестная команда.")
    return MAIN_MENU


async def length_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(",", ".").strip()
    try:
        length = float(text)
        if length <= 0:
            raise ValueError
        context.user_data["length"] = length
        await update.message.reply_text(MESSAGES["enter_height"], reply_markup=main_menu_button_kb())
        return ENTER_HEIGHT
    except ValueError:
        await update.message.reply_text(MESSAGES["invalid_number"], reply_markup=main_menu_button_kb())
        return ENTER_LENGTH

async def height_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace(",", ".").strip()
    try:
        height = float(text)
        if height <= 0:
            raise ValueError
        context.user_data["height"] = height
        await update.message.reply_text(MESSAGES["choose_gate"], reply_markup=gate_kb())
        return CHOOSE_GATE
    except ValueError:
        await update.message.reply_text(MESSAGES["invalid_number"], reply_markup=main_menu_button_kb())
        return ENTER_HEIGHT

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Пожалуйста, введите корректное имя.", reply_markup=main_menu_button_kb())
        return ENTER_NAME
    context.user_data["name"] = name
    await update.message.reply_text(MESSAGES["enter_phone"], reply_markup=main_menu_button_kb())
    return ENTER_PHONE

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not PHONE_REGEX.match(phone):
        await update.message.reply_text(MESSAGES["invalid_phone"], reply_markup=main_menu_button_kb())
        return ENTER_PHONE
    context.user_data["phone"] = phone

    # Показать сводку заказа для подтверждения
    d = context.user_data
    summary = (
        f"Забор: {d.get('fence_type', 'не выбран')}\n"
        f"Длина: {d.get('length', 'не указана')} м\n"
        f"Высота: {d.get('height', 'не указана')} м\n"
        f"Ворота/калитка: {d.get('gate', 'не указано')}\n"
        f"Имя: {d.get('name')}\n"
        f"Телефон: {d.get('phone')}\n\n"
        "Подтвердите отправку заявки?"
    )
    await update.message.reply_text(summary, reply_markup=confirm_kb())
    return CONFIRMATION

async def ask_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if len(question) < 5:
        await update.message.reply_text("Пожалуйста, задайте более развернутый вопрос.", reply_markup=main_menu_button_kb())
        return ASK_QUESTION
    context.user_data["question"] = question
    await update.message.reply_text(MESSAGES["confirm_question"], reply_markup=confirm_kb())
    return CONFIRM_QUESTION

async def confirm_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm_yes":
        text = f"<b>Вопрос от пользователя</b>:\n{context.user_data.get('question')}"
        await query.edit_message_text(MESSAGES["question_sent"], reply_markup=main_menu_kb())
        await context.bot.send_message(ADMIN_ID, text, parse_mode="HTML")
        context.user_data.clear()
        return MAIN_MENU
    if data == "confirm_no":
        await query.edit_message_text(MESSAGES["cancelled"], reply_markup=main_menu_kb())
        context.user_data.clear()
        return MAIN_MENU

    if data == "back_to_main":
        await query.edit_message_text(MESSAGES["welcome"], reply_markup=main_menu_kb())
        context.user_data.clear()
        return MAIN_MENU

    return CONFIRM_QUESTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MESSAGES["cancelled"], reply_markup=main_menu_kb())
    context.user_data.clear()
    return MAIN_MENU

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я не понял, попробуйте еще раз или введите /cancel чтобы выйти.", reply_markup=main_menu_kb())
    return MAIN_MENU


def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(main_menu_handler)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],

            CHOOSING_FENCE: [CallbackQueryHandler(main_menu_handler)],

            ENTER_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, length_handler)],
            ENTER_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height_handler)],

            CHOOSE_GATE: [CallbackQueryHandler(main_menu_handler)],

            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],

            CONFIRMATION: [CallbackQueryHandler(main_menu_handler)],

            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_handler)],
            CONFIRM_QUESTION: [CallbackQueryHandler(confirm_question_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()









