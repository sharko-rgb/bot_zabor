from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import config
import database
import vk_api

# Инициализация БД
database.init_db()

# Главное меню
main_menu = ReplyKeyboardMarkup([
    ["🔩 Выбрать тип забора"],
    ["💰 Рассчитать стоимость"],
    ["📐 Заявка на замер"],
    ["🖼 Примеры работ", "❓ Вопрос"],
    ["📞 Контакты"]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.save_user("telegram", user.id, user.username, user.full_name)
    await update.message.reply_text(
        "Здравствуйте! Чем помочь?",
        reply_markup=main_menu
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "📞 Контакты":
        await update.message.reply_text(
            "📌 Адрес: г. Тюмень, ул. Примерная, 1\n"
            "📞 Телефон: +7 (3452) 00-00-00\n"
            "🌐 Сайт: https://zabory72.ru"
        )
    elif text == "📐 Заявка на замер":
        await update.message.reply_text("Введите адрес для замера:")
        context.user_data['awaiting_address'] = True
    elif 'awaiting_address' in context.user_data:
        address = update.message.text
        database.save_request(user_id, "замер", f"Адрес: {address}")
        await update.message.reply_text("✅ Заявка принята! С вами свяжутся в течение 15 минут.")
        await notify_vk_admin(user_id, "замер", f"Адрес: {address}")
        del context.user_data['awaiting_address']

async def notify_vk_admin(user_id, request_type, data):
    user = database.get_user(user_id)
    vk = vk_api.VkApi(token=config.VK_TOKEN)
    
    # Ссылка для быстрого ответа в Telegram
    tg_link = f"tg://user?id={user_id}"
    message = (
        f"📢 Новый запрос из Telegram\n"
        f"Тип: {request_type}\n"
        f"Пользователь: {user[3]} (@{user[2]})\n"
        f"Данные: {data}\n\n"
        f"⚡ Ответить: {tg_link}"
    )
    
    vk.method("messages.send", {
        "user_id": config.ADMIN_VK_ID,
        "message": message,
        "random_id": 0
    })

if __name__ == "__main__":
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
