from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
import os

# Вставь свои токены и ID
BOT_TOKEN = '7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0'
ADMIN_CHAT_ID = 1346038165  # Замени на ID админа

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Состояния анкеты
class Form(StatesGroup):
    choosing_type = State()
    choosing_detail = State()
    length = State()
    height = State()
    type_confirm = State()
    gates = State()
    name = State()
    phone = State()
    address = State()
    question = State()

# Главное меню
async def send_main_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("1. Выбрать тип забора", callback_data="choose_type"),
        InlineKeyboardButton("2. Рассчитать стоимость", callback_data="calc_price"),
        InlineKeyboardButton("3. Оставить заявку на замер", callback_data="order_measure"),
        InlineKeyboardButton("4. Примеры работ", callback_data="show_examples"),
        InlineKeyboardButton("5. Вопрос специалисту", callback_data="ask_question"),
        InlineKeyboardButton("6. Контакты", callback_data="show_contacts")
    )
    await message.answer("Здравствуйте, Вы обратились в компанию Zabory72.ru...", reply_markup=keyboard)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await send_main_menu(message)

@dp.callback_query_handler(Text(equals="choose_type"))
async def choose_type(call: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(row_width=2)
    types_list = [
        "Профнастил", "Сетка-рабица", "Металлопрофиль",
        "Деревянный забор", "Штакетник", "Еврозабор (бетонный)", "Другой / Не уверен"
    ]
    for t in types_list:
        keyboard.add(InlineKeyboardButton(t, callback_data=f"type_{t}"))
    await call.message.edit_text("Какой тип забора вас интересует?", reply_markup=keyboard)
    await Form.choosing_type.set()

@dp.callback_query_handler(lambda c: c.data.startswith("type_"), state=Form.choosing_type)
async def after_type(call: types.CallbackQuery, state: FSMContext):
    chosen = call.data[5:]
    await state.update_data(fence_type=chosen)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Подробнее", callback_data="details"),
        InlineKeyboardButton("Рассчитать стоимость", callback_data="calc_now")
    )
    await call.message.edit_text(f"Вы выбрали: {chosen}. Что хотите дальше?", reply_markup=keyboard)
    await Form.choosing_detail.set()

@dp.callback_query_handler(Text(equals="details"), state=Form.choosing_detail)
async def show_details(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Пример: выведем просто описание
    await call.message.answer(f"Описание типа забора: {data['fence_type']} - надежный и практичный.")
    await send_main_menu(call.message)
    await state.finish()

@dp.callback_query_handler(Text(equals="calc_now"), state=Form.choosing_detail)
@dp.callback_query_handler(Text(equals="calc_price"))
async def start_calc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите протяженность забора в метрах:", reply_markup=ReplyKeyboardRemove())
    await Form.length.set()

@dp.message_handler(state=Form.length)
async def get_length(message: types.Message, state: FSMContext):
    await state.update_data(length=message.text)
    await message.answer("Введите высоту забора в метрах:")
    await Form.height.set()

@dp.message_handler(state=Form.height)
async def get_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Уточните тип забора или напишите 'тот, что выбрал':")
    await Form.type_confirm.set()

@dp.message_handler(state=Form.type_confirm)
async def get_type_confirm(message: types.Message, state: FSMContext):
    await state.update_data(type_confirm=message.text)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Ворота", callback_data="gates"),
        InlineKeyboardButton("Калитка", callback_data="wicket"),
        InlineKeyboardButton("И то, и другое", callback_data="both"),
        InlineKeyboardButton("Не нужно", callback_data="none")
    )
    await message.answer("Нужны ли ворота / калитка?", reply_markup=keyboard)
    await Form.gates.set()

@dp.callback_query_handler(state=Form.gates)
async def gates_choice(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(gates=call.data)
    await call.message.answer("Введите ваше имя:")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона:")
    await Form.phone.set()

@dp.message_handler(state=Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    msg = (
        f"Новая заявка на расчет\n"
        f"Имя: {data['name']}\nТелефон: {data['phone']}\n"
        f"Длина: {data['length']} м\nВысота: {data['height']} м\n"
        f"Тип забора: {data['type_confirm']}\n"
        f"Дополнительно: {data['gates']}"
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
    await message.answer("Спасибо! Менеджер свяжется с вами.")
    await send_main_menu(message)
    await state.finish()

@dp.callback_query_handler(Text(equals="order_measure"))
async def order_measure(call: types.CallbackQuery):
    await call.message.answer("Введите имя:")
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def measure_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона:")
    await Form.phone.set()

@dp.message_handler(state=Form.phone)
async def measure_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите адрес установки:")
    await Form.address.set()

@dp.message_handler(state=Form.address)
async def measure_done(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    msg = (
        f"Заявка на замер\nИмя: {data['name']}\nТелефон: {data['phone']}\nАдрес: {data['address']}"
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
    await message.answer("Спасибо! Специалист свяжется с вами.")
    await send_main_menu(message)
    await state.finish()

@dp.callback_query_handler(Text(equals="show_examples"))
async def show_examples(call: types.CallbackQuery):
    await call.message.answer("Вот примеры наших работ:")
    # Пример — отправка одного фото (можно заменить на свои)
    await bot.send_photo(call.message.chat.id, photo=open("example1.jpg", "rb"))
    await send_main_menu(call.message)

@dp.callback_query_handler(Text(equals="ask_question"))
async def ask_question(call: types.CallbackQuery):
    await call.message.answer("Введите ваш вопрос:")
    await Form.question.set()

@dp.message_handler(state=Form.question)
async def handle_question(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Вопрос от пользователя: {message.text}")
    await message.answer("Спасибо! Мы ответим вам в ближайшее время.")
    await send_main_menu(message)
    await state.finish()

@dp.callback_query_handler(Text(equals="show_contacts"))
async def show_contacts(call: types.CallbackQuery):
    await call.message.answer(
        "Контакты:\nТел: +7-XXX-XXX-XX-XX\nСайт: https://zabory72.ru\nEmail: info@zabory72.ru\nВремя работы: Пн-Сб 9:00-18:00"
    )
    await send_main_menu(call.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


