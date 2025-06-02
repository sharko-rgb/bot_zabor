import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING_FENCE, SHOWING_INFO, WAITING_FOR_AREA = range(3)

fence_price_info = {
    "fence_prof": {"name": "Забор из профнастила", "price_h_1_8": 3474, "price_h_2_0": 3650},
    "fence_prof_frame": {"name": "Забор «профлист в рамке»", "price_h_1_8": 6140, "price_h_2_0": 6500},
    # остальные забрали пропущены для краткости — возьми из предыдущего примера
}

ADMIN_CHAT_ID = 1346038165  # <-- сюда поставьте ваш Telegram ID администратора


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Забор из профнастила", callback_data="fence_prof"),
            InlineKeyboardButton("Забор «профлист в рамке»", callback_data="fence_prof_frame"),
        ],
        # Добавь остальные кнопки, как в предыдущем примере
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Какой тип забора вас интересует?",
        reply_markup=reply_markup,
    )
    return CHOOSING_FENCE


async def fence_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fence_key = query.data
    context.user_data['fence_type'] = fence_key  # Запоминаем выбор

    fence = fence_price_info.get(fence_key)
    if not fence:
        await query.edit_message_text("Информация по выбранному типу отсутствует.")
        return CHOOSING_FENCE

    text = (
        f"<b>{fence['name']}</b>\n\n"
        "Вы выбрали этот тип забора.\n\n"
        "Что хотите сделать дальше?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate")],
        [InlineKeyboardButton("Подробнее", callback_data="more_info")],
        [InlineKeyboardButton("Выбрать другой тип забора", callback_data="back_to_menu")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    return SHOWING_INFO


async def more_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fence_key = context.user_data.get('fence_type')
    fence = fence_price_info.get(fence_key)
    if not fence:
        await query.edit_message_text("Информация отсутствует.")
        return SHOWING_INFO

    text = (
        f"<b>{fence['name']}</b>\n\n"
        f"Цена за материалы + монтаж «под ключ»\n"
        f"Высота h=1,8 м — {fence['price_h_1_8']} руб.\n"
        f"Высота h=2,0 м — {fence['price_h_2_0']} руб."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Назад", callback_data="back_to_info")],
        [InlineKeyboardButton("Главное меню", callback_data="back_to_menu")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    return SHOWING_INFO


async def back_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fence_key = context.user_data.get('fence_type')
    fence = fence_price_info.get(fence_key)
    if not fence:
        await query.edit_message_text("Информация отсутствует.")
        return CHOOSING_FENCE

    text = (
        f"<b>{fence['name']}</b>\n\n"
        "Вы выбрали этот тип забора.\n\n"
        "Что хотите сделать дальше?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate")],
        [InlineKeyboardButton("Подробнее", callback_data="more_info")],
        [InlineKeyboardButton("Выбрать другой тип забора", callback_data="back_to_menu")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    return SHOWING_INFO


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Забор из профнастила", callback_data="fence_prof"),
            InlineKeyboardButton("Забор «профлист в рамке»", callback_data="fence_prof_frame"),
        ],
        # Добавь остальные кнопки, как в предыдущих примерах
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Какой тип забора вас интересует?",
        reply_markup=reply_markup,
    )
    return CHOOSING_FENCE


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # У нас уже выбран fence_type, запрашиваем площадь
    await query.edit_message_text("Введите площадь забора в квадратных метрах (число):")
    return WAITING_FOR_AREA


async def area_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.strip()

    try:
        area = float(text.replace(',', '.'))
        if area <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное положительное число для площади.")
        return WAITING_FOR_AREA

    context.user_data['area'] = area
    fence_key = context.user_data.get('fence_type')
    fence = fence_price_info.get(fence_key)

    if not fence:
        await update.message.reply_text("Что-то пошло не так, выберите тип забора заново: /start")
        return ConversationHandler.END

    # Простая формула: берем цену для высоты 1.8, умножаем на площадь
    price_per_m2 = fence['price_h_1_8']
    total_price = price_per_m2 * area

    reply_text = (
        f"Вы выбрали: {fence['name']}\n"
        f"Площадь: {area} м²\n"
        f"Стоимость (ориентировочно, высота 1.8 м): {total_price:.2f} руб.\n\n"
        "Спасибо за обращение! Наш менеджер свяжется с вами в ближайшее время."
    )
    await update.message.reply_text(reply_text)

    # Отправляем админу данные
    username = user.username if user.username else "Нет username"
    user_id = user.id
    admin_message = (
        f"Новая заявка от @{username} (ID: {user_id}):\n"
        f"Тип забора: {fence['name']}\n"
        f"Площадь: {area} м²\n"
        f"Приблизительная стоимость: {total_price:.2f} руб."
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена. Если хотите начать заново, напишите /start")
    return ConversationHandler.END


def main():
    TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_FENCE: [
                CallbackQueryHandler(fence_choice, pattern="^fence_"),
            ],
            SHOWING_INFO: [
                CallbackQueryHandler(more_info, pattern="^more_info$"),
                CallbackQueryHandler(back_to_info, pattern="^back_to_info$"),
                CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"),
                CallbackQueryHandler(calculate, pattern="^calculate$"),
                CallbackQueryHandler(fence_choice, pattern="^fence_"),
            ],
            WAITING_FOR_AREA: [
                CommandHandler("cancel", cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, area_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()










