import logging
import sqlite3
from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto)
from telegram.ext import (ApplicationBuilder, CommandHandler, CallbackQueryHandler,
                          MessageHandler, ContextTypes, filters)

# Настройки
API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_CHAT_ID = 1346038165  # Замените на ID администратора
DB_NAME = "users.db"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        fence_type TEXT,
        area TEXT
    )
    """)
    conn.commit()
    conn.close()

# Сохранение данных
def save_user_data(user_id, username, fence_type=None, area=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, fence_type, area)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            fence_type=COALESCE(excluded.fence_type, users.fence_type),
            area=COALESCE(excluded.area, users.area)
    """, (user_id, username, fence_type, area))
    conn.commit()
    conn.close()

# Получение типа забора
def get_user_fence_type(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fence_type FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Основное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("1. Выбрать тип забора", callback_data="choose_fence")],
        [InlineKeyboardButton("2. Рассчитать стоимость", callback_data="calc_cost")],
        [InlineKeyboardButton("3. Бесплатный замер", callback_data="free_measure")],
        [InlineKeyboardButton("4. Примеры работ", callback_data="examples")],
        [InlineKeyboardButton("5. Вопрос специалисту", callback_data="ask_expert")],
        [InlineKeyboardButton("6. Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Типы заборов
FENCE_TYPES = {
    "fence_1": ("Забор из профнастила", 3474, 3650),
    "fence_2": ("Профлист в рамке", 6140, 6500),
    "fence_3": ("Евроштакетник вертикально", 7620, 8260),
    "fence_4": ("Евроштакетник горизонтально", 9650, 10350),
    "fence_5": ("Жалюзи", 8700, None),
    "fence_6": ("Ранчо двойной", 14500, None),
    "fence_6b": ("Ранчо одинарной ламели", 11000, None),
    "fence_7": ("3Д сетка", 3100, None),
    "fence_8": ("Откатные ворота", 87000, 87000),
    "fence_9": ("Распашные ворота + калитка", 37000, 37000),
    "fence_10": ("Навесы", "от 7500 руб./м²", "")
}

def fence_menu():
    keyboard = []
    for i, (key, value) in enumerate(FENCE_TYPES.items(), start=1):
        keyboard.append([InlineKeyboardButton(f"{i}. {value[0]}", callback_data=f"{key}")])
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user_data(user.id, user.username)
    await update.message.reply_text("Добро пожаловать!", reply_markup=main_menu())

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "choose_fence":
        await query.edit_message_text("Какой тип забора вас интересует?", reply_markup=fence_menu())
    elif data.startswith("fence_"):
        fence_name = FENCE_TYPES[data][0]
        save_user_data(user.id, user.username, fence_type=fence_name)
        await query.edit_message_text(f"Вы выбрали: {fence_name}. Хотите узнать подробнее и рассчитать стоимость?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Подробнее", callback_data="details")],
            [InlineKeyboardButton("На главную", callback_data="menu")]
        ]))
    elif data == "details":
        fence = get_user_fence_type(user.id)
        cost = next((v for k, v in FENCE_TYPES.items() if v[0] == fence), None)
        text = f"{fence}\nСтоимость при h=1.8м: {cost[1]}\nСтоимость при h=2.0м: {cost[2]}" if isinstance(cost[1], int) else f"{fence}: {cost[1]}"
        await query.edit_message_text(text, reply_markup=main_menu())
    elif data == "calc_cost":
        await query.edit_message_text("Введите площадь участка в м²:")
        context.user_data['awaiting_area'] = True
    elif data == "free_measure":
        await query.edit_message_text("Чтобы заказать бесплатный замер, отправьте ваш адрес и телефон.")
    elif data == "examples":
        media = [InputMediaPhoto(media="https://example.com/photo1.jpg"),
                 InputMediaPhoto(media="https://example.com/photo2.jpg")]
        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
    elif data == "ask_expert":
        await query.edit_message_text("Задайте свой вопрос и специалист ответит вам в ближайшее время.")
    elif data == "contacts":
        await query.edit_message_text("Контакты:\n📞 +7 (900) 000-00-00\n🌐 zabory.ru\n📍 Москва")
    elif data == "menu":
        await query.edit_message_text("Вы в главном меню", reply_markup=main_menu())

# Обработка ввода площади
async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_area'):
        try:
            area = float(update.message.text)
            user = update.effective_user
            fence = get_user_fence_type(user.id)
            cost = next((v for k, v in FENCE_TYPES.items() if v[0] == fence), None)
            unit_price = cost[1] if isinstance(cost[1], int) else 0
            total = unit_price * area
            msg = f"Тип забора: {fence}\nПлощадь: {area} м²\nПриблизительная стоимость: {total:.2f} руб."
            await update.message.reply_text(msg)
            await context.bot.send_message(ADMIN_CHAT_ID, f"Новая заявка от @{user.username}:\n{msg}")
            save_user_data(user.id, user.username, area=str(area))
        except ValueError:
            await update.message.reply_text("Введите число.")
        finally:
            context.user_data['awaiting_area'] = False

# Основной запуск
async def main():
    init_db()
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_area))

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())











