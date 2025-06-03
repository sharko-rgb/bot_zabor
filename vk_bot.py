import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import database
from telegram import Bot
import asyncio

# Инициализация БД
database.init_db()

vk = vk_api.VkApi(token=config.VK_TOKEN)
longpoll = VkLongPoll(vk)

def send_message(user_id, message, keyboard=None):
    vk.method("messages.send", {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
        "keyboard": keyboard
    })

# Главное меню VK
keyboard = VkKeyboard(one_time=False)
keyboard.add_button("🔩 Тип забора", color=VkKeyboardColor.PRIMARY)
keyboard.add_button("💰 Расчёт стоимости", color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button("📐 Заявка на замер", color=VkKeyboardColor.DEFAULT)
keyboard.add_button("📞 Контакты", color=VkKeyboardColor.NEGATIVE)

async def notify_telegram_admin(user_id, request_type, data):
    user = database.get_user(user_id)
    bot = Bot(token=config.TELEGRAM_TOKEN)
    vk_link = f"vk.com/id{user[2]}"
    message = (
        f"📢 Новый запрос из VK\n"
        f"Тип: {request_type}\n"
        f"Пользователь: {user[3]} ({vk_link})\n"
        f"Данные: {data}\n\n"
        f"⚡ Ответить: {vk_link}"
    )
    await bot.send_message(chat_id=config.ADMIN_TG_ID, text=message)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.lower()

        if text == "начать":
            user_info = vk.method("users.get", {"user_ids": user_id, "fields": "first_name,last_name"})
            full_name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
            database.save_user("vk", user_id, f"id{user_id}", full_name)
            send_message(user_id, "Здравствуйте! Чем помочь?", keyboard.get_keyboard())
        
        elif text == "📐 заявка на замер":
            send_message(user_id, "Введите адрес для замера:")
            # Здесь можно добавить логику сбора данных, как в Telegram
            address = "..."  # Получаем из следующего сообщения
            database.save_request(user_id, "замер", f"Адрес: {address}")
            send_message(user_id, "✅ Заявка принята!")
            asyncio.run(notify_telegram_admin(user_id, "замер", f"Адрес: {address}"))
