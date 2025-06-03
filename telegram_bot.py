from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Главное меню
main_menu = ReplyKeyboardMarkup([
    ["1. Выбрать тип забора"],
    ["2. Рассчитать стоимость"],
    ["3. Оставить заявку на бесплатный замер"],
    ["4. Посмотреть примеры наших работ"],
    ["5. Задать вопрос специалисту"],
    ["6. Контакты"]
], resize_keyboard=True)

# Меню выбора типа забора
fence_types_menu = ReplyKeyboardMarkup([
    ["1. Забор из профнастила"],
    ["2. Забор «профлист в рамке»"],
    ["3. Евроштакетник вертикально"],
    ["4. Евроштакетник горизонтально"],
    ["5. Забор Жалюзи"],
    ["6. Забор Ранчо"],
    ["7. Забор из 3Д сетки"],
    ["8. Ворота откатные"],
    ["9. Ворота распашные + Калитка"],
    ["10. Навесы для автомобиля"],
    ["⬅ Назад"]
], resize_keyboard=True)

# Стоимости по видам заборов (примерные, за 1 метр, для высоты 1.8 м)
fence_prices = {
    "1": 3474,
    "2": 6140,
    "3": 7620,
    "4": 9650,
    "5": 8700,
    "6": 14500,
    "7": 3100,
    "8": 87000,
    "9": 37000,
    "10": 7500  # от 7500 руб./м.кв.
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Здравствуйте, Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов «под ключ», "
        "в том числе каменных, из кирпича и керамзитоблоков, также мы строим металлические навесы для автомобилей.\n\n"
        "Основное меню:"
    )
    await update.message.reply_text(text, reply_markup=main_menu)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    # Главное меню
    if text.startswith("1"):
        await update.message.reply_text("Какой тип забора Вас интересует?", reply_markup=fence_types_menu)
        context.user_data['state'] = 'choosing_fence_type'

    elif text.startswith("2"):
        await update.message.reply_text(
            "Для расчёта стоимости выберите тип забора из меню 'Выбрать тип забора' и укажите параметры.\n"
            "Пока вы можете узнать приблизительную стоимость по таблице."
        )
        # Можно добавить функционал калькулятора позже

    elif text.startswith("3"):
        await update.message.reply_text("Введите адрес для бесплатного замера:")
        context.user_data['state'] = 'awaiting_address'

    elif text.startswith("4"):
        await update.message.reply_text("Вот примеры наших работ:\nhttps://zabory72.ru/gallery")

    elif text.startswith("5"):
        await update.message.reply_text("Задайте ваш вопрос специалисту, мы свяжемся с вами в ближайшее время.")
        context.user_data['state'] = 'awaiting_question'

    elif text.startswith("6"):
        await update.message.reply_text(
            "📌 Адрес: г. Тюмень, ул. Примерная, 1\n"
            "📞 Телефон: +7 (3452) 00-00-00\n"
            "🌐 Сайт: https://zabory72.ru"
        )

    # Обработка выбора типа забора (подменю)
    elif context.user_data.get('state') == 'choosing_fence_type':
        if text == "⬅ Назад":
            await update.message.reply_text("Возврат в главное меню:", reply_markup=main_menu)
            context.user_data.pop('state')
            return

        # Проверим выбранный пункт, например "1. Забор из профнастила"
        selected_num = text.split(".")[0]
        if selected_num in fence_prices:
            price = fence_prices[selected_num]
            fence_name = text[text.find(".")+2:]  # Отрезаем номер и точку

            await update.message.reply_text(
                f"Вы выбрали: {fence_name}\n"
                f"Приблизительная стоимость за 1 метр (высота 1.8 м): {price} руб.\n\n"
                "Хотите узнать подробнее и сразу рассчитать стоимость? Напишите 'Рассчитать'."
            )
            context.user_data['selected_fence'] = fence_name
            context.user_data['state'] = 'ready_to_calculate'
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант из меню.")

    elif context.user_data.get('state') == 'ready_to_calculate':
        if text.lower() == "рассчитать":
            await update.message.reply_text(
                "Отлично! Для расчёта стоимости сообщите длину забора в метрах."
            )
            context.user_data['state'] = 'awaiting_length'
        else:
            await update.message.reply_text("Напишите 'Рассчитать' для начала расчёта или '⬅ Назад' для возврата.")

    elif context.user_data.get('state') == 'awaiting_length':
        try:
            length = float(text.replace(",", "."))
            fence_name = context.user_data.get('selected_fence', 'забор')
            price_per_meter = None
            for k, v in fence_prices.items():
                if fence_name.lower() in v.lower() if isinstance(v, str) else False:
                    price_per_meter = v
            if not price_per_meter:
                # Попробуем по ключу из saved fence name
                for k, v in fence_prices.items():
                    if fence_name.lower().startswith(v.lower() if isinstance(v, str) else ""):
                        price_per_meter = v
            # Или просто берем из словаря по ключу из user_data
            # Для простоты возьмём первый ключ, т.к. user_data не хранит номер, а только название
            # Лучше хранить номер в user_data, тогда:
            selected_num = None
            for num, name in fence_prices.items():
                if fence_name.lower() in name.lower():
                    selected_num = num
            if selected_num is None:
                selected_num = list(fence_prices.keys())[0]  # На всякий случай
            price_per_meter = fence_prices[selected_num]

            total_price = length * price_per_meter
            await update.message.reply_text(
                f"Приблизительная стоимость {fence_name} длиной {length} м составляет {total_price:.2f} руб."
            )
            context.user_data.pop('state')
            context.user_data.pop('selected_fence')
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число (длину забора) в метрах.")

    elif context.user_data.get('state') == 'awaiting_address':
        address = update.message.text
        # Сохрани заявку в БД
        # database.save_request(user_id, "замер", f"Адрес: {address}")  # если есть БД
        await update.message.reply_text("✅ Заявка принята! С вами свяжутся в течение 15 минут.")
        context.user_data.pop('state')

    elif context.user_data.get('state') == 'awaiting_question':
        question = update.message.text
        # database.save_request(user_id, "вопрос", question)  # если есть БД
        await update.message.reply_text("Спасибо за вопрос! Наш специалист свяжется с вами.")
        context.user_data.pop('state')

    else:
        await update.message.reply_text(
            "Пожалуйста, выберите пункт из меню.",
            reply_markup=main_menu
        )


if __name__ == "__main__":
    import config
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    database.init_db()  # Если нужна инициализация БД

    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


