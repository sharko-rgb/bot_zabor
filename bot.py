import asyncio
import logging
import re
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

logging.basicConfig(level=logging.INFO)

# --- Конфигурация ---
TELEGRAM_TOKEN = "7731731504:AAHCy1Ipl61-CxI7Tvni4z9dWCUcYWbT650"
VK_GROUP_TOKEN = "vk1.a.fIwIo0GT7PD42VeV_E9i8pItr2LYeC7BxPvzp1nCQ6W2FDbrk-xAyLOKmwVRkycx5SOwjGL2vRYonLZ_PR-6sbvX2JU3y3Gz2GpiuxamRpNllx8-uO9B36WpN73jRxVabbNi5ku7R1e_uWnnS6fAjQXF5MWGgutORxrNKO3hyTgrQHS4jYHSO9xgq1l6h-gd0oAczgUmEaHno35FJlV0Ew"
VK_GROUP_ID = 80211925  # например 123456789

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
dp = Dispatcher(storage=storage)

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

async def tg_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов.",
        reply_markup=create_telegram_main_menu()
    )

async def tg_choose_fence(message: types.Message):
    await message.answer("Выберите тип забора:", reply_markup=create_telegram_fence_menu())

async def tg_back_main(message: types.Message):
    await message.answer("Возвращаемся в главное меню.", reply_markup=create_telegram_main_menu())

async def tg_fence_selected(message: types.Message):
    await message.answer(f"Вы выбрали: {message.text}\nЕсли хотите рассчитать стоимость, выберите пункт меню '2. Рассчитать стоимость'.")

async def tg_start_cost_calc(message: types.Message):
    await message.answer("Выберите тип забора для расчета стоимости:", reply_markup=create_telegram_fence_menu())
    await TgForm.fence_type.set()

async def tg_process_fence_type(message: types.Message, state: FSMContext):
    text = message.text
    for k, v in COST_TABLE.items():
        if text.startswith(str(k)) or text == v["name"]:
            await state.update_data(fence_type=k)
            await message.answer("Выберите высоту забора:", reply_markup=create_telegram_height_menu())
            await TgForm.next()
            return
    await message.answer("Пожалуйста, выберите тип забора из меню.")

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

@dp.message.register(commands=["start", "help"])
async def tg_start(message: types.Message):
    await tg_start(message)

@dp.message.register(lambda message: message.text == "1. Выбрать тип забора")
async def tg_choose_fence(message: types.Message):
    await tg_choose_fence(message)

@dp.message.register(lambda message: message.text == "Назад")
async def tg_back_main(message: types.Message):
    await tg_back_main(message)

# === Запуск бота ===

async def main():
    tg_task = asyncio.create_task(dp.start_polling())
    vk_task = asyncio.create_task(vk_handler())
    await asyncio.gather(tg_task, vk_task)

if __name__ == "__main__":
    asyncio.run(main())
