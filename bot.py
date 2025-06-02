import asyncio
import logging
import re
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

logging.basicConfig(level=logging.INFO)

# --- Конфигурация ---
TELEGRAM_TOKEN = "7731731504:AAHCy1Ipl61-CxI7Tvni4z9dWCUcYWbT650"
VK_GROUP_TOKEN = "ВАШ_VK_GROUP_TOKEN"
VK_GROUP_ID = ВАШ_VK_GROUP_ID  # например 123456789

# --- Таблица стоимости ---
COST_TABLE = {
    1: {"name": "Забор из профнастила", 1.8: 3474, 2.0: 3650},
    2: {"name": "Забор «профлист в рамке»", 1.8: 6140, 2.0: 6500},
    3: {"name": "Евроштакетник вертикально", 1.8: 7620, 2.0: 8260},
    4: {"name": "Евроштакетник горизонтально", 1.8: 9650, 2.0: 10350},
    5: {"name": "Забор Жалюзи", 1.8: 8700, 2.0: None},
    6: {"name": "Забор Ранчо (двойная ламель)", 1.8: 14500, 2.0: None},
    7: {"name": "Забор из 3Д сетки", 1.8: 3100, 2.0: None},
    8: {"name": "Ворота откатные", 1.8: 87000, 2.0: 87000},
    9: {"name": "Ворота распашные + Калитка", 1.8: 37000, 2.0: 37000},
    10: {"name": "Навесы для автомобиля", 1.8: 7500, 2.0: None}
}

# ==== Telegram ====

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class TgForm(StatesGroup):
    fence_type = State()
    fence_height = State()
    name = State()
    phone = State()
    address = State()

# ==== VK ====

vk_session = VkApi(token=VK_GROUP_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

vk_user_states = {}
vk_user_data = {}

# --- Общие функции ---

def create_telegram_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        "1. Выбрать тип забора",
        "2. Рассчитать стоимость",
        "3. Оставить заявку на бесплатный замер",
        "4. Посмотреть примеры наших работ",
        "5. Задать вопрос специалисту",
        "6. Контакты"
    )
    return keyboard

def create_telegram_fence_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for i in range(1, 11):
        keyboard.insert(f"{i}. {COST_TABLE[i]['name']}")
    keyboard.add("Назад")
    return keyboard

def create_telegram_height_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("1.8 м", "2.0 м")
    keyboard.add("Отмена")
    return keyboard

def create_vk_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("1. Выбрать тип забора", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("2. Рассчитать стоимость", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("3. Оставить заявку на бесплатный замер", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("4. Посмотреть примеры наших работ", color=VkKeyboardColor.DEFAULT)
    keyboard.add_line()
    keyboard.add_button("5. Задать вопрос специалисту", color=VkKeyboardColor.DEFAULT)
    keyboard.add_line()
    keyboard.add_button("6. Контакты", color=VkKeyboardColor.DEFAULT)
    return keyboard.get_keyboard()

def create_vk_fence_keyboard():
    keyboard = VkKeyboard(one_time=True)
    for i in range(1, 11):
        keyboard.add_button(f"{i}. {COST_TABLE[i]['name']}", color=VkKeyboardColor.PRIMARY)
        if i % 2 == 0:
            keyboard.add_line()
    keyboard.add_button("Назад", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def create_vk_height_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("1.8 м", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("2.0 м", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Отмена", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

async def send_vk_message(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        random_id=0,
        message=message,
        keyboard=keyboard
    )

def parse_fence_choice(text):
    match = re.match(r"(\d+)", text)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 10:
            return num
    return None

async def save_application(name, phone, address):
    async with aiosqlite.connect("zabory72.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "INSERT INTO applications (name, phone, address) VALUES (?, ?, ?)",
            (name, phone, address)
        )
        await db.commit()

# ==== Telegram Handlers ====

@dp.message_handler(commands=["start", "help"])
async def tg_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов.",
        reply_markup=create_telegram_main_menu()
    )

@dp.message_handler(lambda message: message.text == "1. Выбрать тип забора")
async def tg_choose_fence(message: types.Message):
    await message.answer("Выберите тип забора:", reply_markup=create_telegram_fence_menu())

@dp.message_handler(lambda message: message.text == "Назад")
async def tg_back_main(message: types.Message):
    await message.answer("Возвращаемся в главное меню.", reply_markup=create_telegram_main_menu())

@dp.message_handler(lambda message: message.text and message.text[0].isdigit() and int(message.text[0]) in range(1,11))
async def tg_fence_selected(message: types.Message):
    await message.answer(f"Вы выбрали: {message.text}\nЕсли хотите рассчитать стоимость, выберите пункт меню '2. Рассчитать стоимость'.")

@dp.message_handler(lambda message: message.text == "2. Рассчитать стоимость")
async def tg_start_cost_calc(message: types.Message):
    await message.answer("Выберите тип забора для расчета стоимости:", reply_markup=create_telegram_fence_menu())
    await TgForm.fence_type.set()

@dp.message_handler(state=TgForm.fence_type)
async def tg_process_fence_type(message: types.Message, state: FSMContext):
    text = message.text
    for k, v in COST_TABLE.items():
        if text.startswith(str(k)) or text == v["name"]:
            await state.update_data(fence_type=k)
            await message.answer("Выберите высоту забора:", reply_markup=create_telegram_height_menu())
            await TgForm.next()
            return
    await message.answer("Пожалуйста, выберите тип забора из меню.")

@dp.message_handler(state=TgForm.fence_height)
async def tg_process_height(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
        await message.answer("Отмена расчёта стоимости.", reply_markup=create_telegram_main_menu())
        await state.finish()
        return
    if message.text not in ["1.8 м", "2.0 м"]:
        await message.answer("Пожалуйста, выберите высоту из меню.")
        return

    height = float(message.text.split()[0])
    data = await state.get_data()
    fence_type = data.get("fence_type")
    price = COST_TABLE[fence_type].get(height)
    name = COST_TABLE[fence_type]["name"]

    if price is None:
        await message.answer(f"Для {name} высотой {height} м цена отсутствует.")
    else:
        await message.answer(f"Примерная стоимость за метр погонный для {name} высотой {height} м: {price} руб.")

    await message.answer("Если хотите, можете оставить заявку на бесплатный замер через пункт меню '3. Оставить заявку на бесплатный замер'.", reply_markup=create_telegram_main_menu())
    await state.finish()

@dp.message_handler(lambda message: message.text == "3. Оставить заявку на бесплатный замер")
async def tg_start_application(message: types.Message):
    await message.answer("Пожалуйста, укажите Ваше имя:")
    await TgForm.name.set()

@dp.message_handler(state=TgForm.name)
async def tg_process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш телефон:")
    await TgForm.next()

@dp.message_handler(state=TgForm.phone)
async def tg_process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите адрес объекта:")
    await TgForm.next()

@dp.message_handler(state=TgForm.address)
async def tg_process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()

    await save_application(data['name'], data['phone'], data['address'])

    await message.answer("Спасибо! Ваша заявка принята. Наши специалисты свяжутся с Вами в ближайшее время.", reply_markup=create_telegram_main_menu())
    await state.finish()

@dp.message_handler(lambda message: message.text == "4. Посмотреть примеры наших работ")
async def tg_show_examples(message: types.Message):
    await message.answer("Примеры наших работ можно посмотреть в нашей группе ВКонтакте:\nhttps://vk.com/yourgroup", reply_markup=create_telegram_main_menu())

@dp.message_handler(lambda message: message.text == "5. Задать вопрос специалисту")
async def tg_ask_specialist(message: types.Message):
    await message.answer("Пожалуйста, напишите ваш вопрос, и мы передадим его специалисту. Также можно связаться по телефону.", reply_markup=create_telegram_main_menu())

@dp.message_handler(lambda message: message.text == "6. Контакты")
async def tg_contacts(message: types.Message):
    await message.answer(
        "Контакты компании Zabory72.ru:\n"
        "Телефон: +7 (XXX) XXX-XX-XX\n"
        "Email: info@zabory72.ru\n"
        "Адрес: г. Ваш город, ул. Примерная, д.1",
        reply_markup=create_telegram_main_menu()
    )

# ==== VK Handler ====

STATE_MAIN = "MAIN"
STATE_CHOOSE_FENCE = "CHOOSE_FENCE"
STATE_CALC_FENCE_TYPE = "CALC_FENCE_TYPE"
STATE_CALC_FENCE_HEIGHT = "CALC_FENCE_HEIGHT"
STATE_APP_NAME = "APP_NAME"
STATE_APP_PHONE = "APP_PHONE"
STATE_APP_ADDRESS = "APP_ADDRESS"

async def vk_handler():
    print("VK bot started...")
    async with aiosqlite.connect("zabory72.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_id = event.object.message['from_id']
            text = event.object.message['text'].strip().lower()
            state = vk_user_states.get(user_id, STATE_MAIN)

            if state == STATE_MAIN:
                if text in ["начать", "старт", "привет"]:
                    await send_vk_message(user_id, "Здравствуйте! Вы в меню компании Zabory72.ru.", create_vk_main_keyboard())
                elif text.startswith("1"):
                    vk_user_states[user_id] = STATE_CHOOSE_FENCE
                    await send_vk_message(user_id, "Выберите тип забора:", create_vk_fence_keyboard())
                elif text.startswith("2"):
                    vk_user_states[user_id] = STATE_CALC_FENCE_TYPE
                    await send_vk_message(user_id, "Выберите тип забора для расчёта стоимости:", create_vk_fence_keyboard())
                elif text.startswith("3"):
                    vk_user_states[user_id] = STATE_APP_NAME
                    await send_vk_message(user_id, "Пожалуйста, введите Ваше имя:")
                elif text.startswith("4"):
                    await send_vk_message(user_id, "Примеры наших работ смотрите в группе: https://vk.com/yourgroup", create_vk_main_keyboard())
                elif text.startswith("5"):
                    await send_vk_message(user_id, "Напишите ваш вопрос, и мы передадим его специалисту.", create_vk_main_keyboard())
                elif text.startswith("6"):
                    await send_vk_message(user_id, "Контакты:\nТелефон: +7 (XXX) XXX-XX-XX\nEmail: info@zabory72.ru\nАдрес: г. Ваш город", create_vk_main_keyboard())
                else:
                    await send_vk_message(user_id, "Пожалуйста, выберите пункт меню от 1 до 6 или напишите 'Начать'.", create_vk_main_keyboard())

            elif state == STATE_CHOOSE_FENCE:
                if text == "назад":
                    vk_user_states[user_id] = STATE_MAIN
                    await send_vk_message(user_id, "Возвращаемся в главное меню.", create_vk_main_keyboard())
                else:
                    choice = parse_fence_choice(text)
                    if choice:
                        name = COST_TABLE[choice]["name"]
                        await send_vk_message(user_id, f"Вы выбрали: {name}\nДля расчёта стоимости выберите пункт меню '2. Рассчитать стоимость'.")
                    else:
                        await send_vk_message(user_id, "Пожалуйста, выберите корректный тип забора из меню.", create_vk_fence_keyboard())

            elif state == STATE_CALC_FENCE_TYPE:
                if text == "назад":
                    vk_user_states[user_id] = STATE_MAIN
                    await send_vk_message(user_id, "Возвращаемся в главное меню.", create_vk_main_keyboard())
                else:
                    choice = parse_fence_choice(text)
                    if choice:
                        vk_user_data[user_id] = {"fence_type": choice}
                        vk_user_states[user_id] = STATE_CALC_FENCE_HEIGHT
                        await send_vk_message(user_id, "Выберите высоту забора:", create_vk_height_keyboard())
                    else:
                        await send_vk_message(user_id, "Пожалуйста, выберите корректный тип забора из меню.", create_vk_fence_keyboard())

            elif state == STATE_CALC_FENCE_HEIGHT:
                if text == "отмена":
                    vk_user_states[user_id] = STATE_MAIN
                    vk_user_data.pop(user_id, None)
                    await send_vk_message(user_id, "Отмена расчёта стоимости.", create_vk_main_keyboard())
                elif text in ["1.8 м", "2.0 м"]:
                    height = float(text.split()[0])
                    choice = vk_user_data.get(user_id, {}).get("fence_type")
                    if choice:
                        price = COST_TABLE[choice].get(height)
                        name = COST_TABLE[choice]["name"]
                        if price is None:
                            await send_vk_message(user_id, f"Для {name} высота {height} м цена не указана.")
                        else:
                            await send_vk_message(user_id, f"Примерная стоимость за метр погонный для {name} высотой {height} м: {price} руб.")
                        vk_user_states[user_id] = STATE_MAIN
                        vk_user_data.pop(user_id, None)
                        await send_vk_message(user_id, "Главное меню:", create_vk_main_keyboard())
                    else:
                        await send_vk_message(user_id, "Ошибка выбора типа забора, попробуйте заново.", create_vk_main_keyboard())
                        vk_user_states[user_id] = STATE_MAIN
                        vk_user_data.pop(user_id, None)
                else:
                    await send_vk_message(user_id, "Пожалуйста, выберите высоту из меню.", create_vk_height_keyboard())

            elif state == STATE_APP_NAME:
                vk_user_data[user_id] = {"name": text}
                vk_user_states[user_id] = STATE_APP_PHONE
                await send_vk_message(user_id, "Введите ваш телефон:")

            elif state == STATE_APP_PHONE:
                vk_user_data[user_id]["phone"] = text
                vk_user_states[user_id] = STATE_APP_ADDRESS
                await send_vk_message(user_id, "Введите адрес объекта:")

            elif state == STATE_APP_ADDRESS:
                vk_user_data[user_id]["address"] = text
                data = vk_user_data[user_id]
                await save_application(data["name"], data["phone"], data["address"])
                await send_vk_message(user_id, f"Спасибо, {data['name']}! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.", create_vk_main_keyboard())
                vk_user_states[user_id] = STATE_MAIN
                vk_user_data.pop(user_id, None)

# ====== MAIN ======

async def main():
    tg_task = asyncio.create_task(dp.start_polling())
    vk_task = asyncio.create_task(vk_handler())
    await asyncio.gather(tg_task, vk_task)

if __name__ == "__main__":
    asyncio.run(main())
