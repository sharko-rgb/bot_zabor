from telegram import Bot  # Добавляем импорт

async def notify_telegram_admin(user_id, request_type, data):
    bot = Bot(token=config.TELEGRAM_TOKEN)
    user = database.get_user(user_id)
    message = (
        f"📢 Новое уведомление из VK\n"
        f"Тип: {request_type}\n"
        f"Пользователь: {user[3]} (vk.com/id{user[2]})\n"
        f"Данные: {data}"
    )
    await bot.send_message(chat_id=config.ADMIN_TG_ID, text=message)

# Пример вызова (в обработчике заявки):
await notify_telegram_admin(event.user_id, "вопрос", "Какова цена забора?")
