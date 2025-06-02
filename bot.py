import asyncio
import logging
import re
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from concurrent.futures import ThreadPoolExecutor

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
    5: {"name": "Забор Жалюзи", 1.8: 8700},
    6: {"name": "Забор Ранчо (двойная ламель)", 1.8: 14500},
    7: {"name": "Забор из 3Д сетки", 1.8: 3100},
    8: {"name": "Ворота откатные", 1.8: 87000, 2.0: 87000},
    9: {"name": "Ворота распашные + Калитка", 1.8: 37000, 2.0: 37000},
    10: {"name": "Навесы для автомобиля", 1.8: 7500}
}

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class TgForm(StatesGroup):
    fence_type = State()
    fence_height = State()

vk_session = VkApi(token=VK_GROUP_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

executor = ThreadPoolExecutor()

# --- Keyboard Functions ---
def create_telegram_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        "1. Выбрать тип забора",
        "2. Рассчитать стоимость"
    )
    return keyboard

def create_telegram_fence_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 11):
        keyboard.add(f"{i}. {COST_TABLE[i]['name']}")
    keyboard.add("Назад")
    return keyboard

def create_telegram_height_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add("1.8 м", "2.0 м", "Отмена")

# --- DB Function ---
async def save_application(name, phone, address):
    async with aiosqlite.connect("zabory72.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT, address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("INSERT INTO applications (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
        await db.commit()

# --- Telegram Handlers ---
@dp.message(Command("start"))
async def tg_start(message: types.Message):
    await message.answer("Здравствуйте! Выберите действие:", reply_markup=create_telegram_main_menu())

@dp.message(lambda m: m.text == "1. Выбрать тип забора")
async def tg_choose_fence(message: types.Message):
    await message.answer("Выберите тип забора:", reply_markup=create_telegram_fence_menu())

@dp.message(lambda m: m.text == "2. Рассчитать стоимость")
async def tg_start_calc(message: types.Message, state: FSMContext):
    await message.answer("Выберите тип забора:", reply_markup=create_telegram_fence_menu())
    await state.set_state(TgForm.fence_type)

@dp.message(TgForm.fence_type)
async def tg_set_fence_type(message: types.Message, state: FSMContext):
    for k, v in COST_TABLE.items():
        if message.text.startswith(str(k)) or message.text == v["name"]:
            await state.update_data(fence_type=k)
            await message.answer("Выберите высоту:", reply_markup=create_telegram_height_menu())
            await state.set_state(TgForm.fence_height)
            return
    await message.answer("Пожалуйста, выберите тип из меню.")

@dp.message(TgForm.fence_height)
async def tg_set_height(message: types.Message, state: FSMContext):
    if message.text == "Отмена":
        await message.answer("Операция отменена.", reply_markup=create_telegram_main_menu())
        await state.clear()
        return
    if message.text not in ["1.8 м", "2.0 м"]:
        await message.answer("Выберите высоту из меню.")
        return

    height = float(message.text.split()[0])
    data = await state.get_data()
    fence_type = data.get("fence_type")
    name = COST_TABLE[fence_type]["name"]
    price = COST_TABLE[fence_type].get(height)

    if price:
        await message.answer(f"Стоимость для {name} ({height} м): {price} руб.")
    else:
        await message.answer(f"Для {name} с высотой {height} м цена отсутствует.")

    await state.clear()
    await message.answer("Что хотите сделать дальше?", reply_markup=create_telegram_main_menu())

# --- VK Handler ---
def handle_vk_event(event):
    if event.type == VkBotEventType.MESSAGE_NEW:
        user_id = event.obj.message["from_id"]
        text = event.obj.message["text"]

        if text.lower() == "привет":
            vk.messages.send(user_id=user_id, message="Привет! Напиши '1' чтобы выбрать тип забора", random_id=0)
        elif text.startswith("1"):
            response = "\n".join([f"{k}. {v['name']}" for k, v in COST_TABLE.items()])
            vk.messages.send(user_id=user_id, message="Выберите тип:\n" + response, random_id=0)
        elif text.startswith(tuple(str(i) for i in range(1, 11))):
            num = int(text.split(".")[0])
            name = COST_TABLE[num]["name"]
            vk.messages.send(user_id=user_id, message=f"Вы выбрали: {name}. Доступные высоты: 1.8 м, 2.0 м", random_id=0)
        elif text in ["1.8", "2.0"]:
            vk.messages.send(user_id=user_id, message=f"Оценим стоимость: {text} м", random_id=0)
        else:
            vk.messages.send(user_id=user_id, message="Команда не распознана. Напишите '1' для начала.", random_id=0)

async def vk_listener():
    loop = asyncio.get_running_loop()
    for event in longpoll.listen():
        loop.call_soon_threadsafe(handle_vk_event, event)

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        asyncio.to_thread(vk_listener)
    )

if __name__ == "__main__":
    asyncio.run(main())

