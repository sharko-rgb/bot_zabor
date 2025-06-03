import vk_api  # Добавляем импорт

async def notify_vk_admin(user_id, request_type, data):
    vk = vk_api.VkApi(token=config.VK_TOKEN)
    user = database.get_user(user_id)
    message = (
        f"📢 Новое уведомление из Telegram\n"
        f"Тип: {request_type}\n"
        f"Пользователь: {user[3]} (@{user[2]})\n"
        f"Данные: {data}"
    )
    vk.method("messages.send", {
        "user_id": config.ADMIN_VK_ID,
        "message": message,
        "random_id": 0
    })

# Пример вызова (в обработчике заявки):
await notify_vk_admin(update.message.from_user.id, "замер", "Адрес: ул. Примерная, 10")
