import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # <-- замените на ваш Telegram ID

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class CostCalc(StatesGroup):
    length = State()
    height = State()
    type = State()
    extras = State()
    contact = State()

class MeasureRequest(StatesGroup):
    name = State()
    phone = State()
    address = State()

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1. Выбрать тип забора", callback_data="choose_type")],
    [InlineKeyboardButton(text="2. Рассчитать стоимость", callback_data="calc_cost")],
    [InlineKeyboardButton(text="3. Оставить заявку на замер", callback_data="request_measure")],
    [InlineKeyboardButton(text="4. Примеры работ", callback_data="show_examples")],
    [InlineKeyboardButton(text="5. Вопрос специалисту", callback_data="ask_question")],
    [InlineKeyboardButton(text="6. Контакты", callback_data="contacts")]
])

types_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Профнастил", callback_data="type_Профнастил")],
    [InlineKeyboardButton(text="Сетка-рабица", callback_data="type_Сетка-рабица")],
    [InlineKeyboardButton(text="Металлопрофиль", callback_data="type_Металлопрофиль")],
    [InlineKeyboardButton(text="Деревянный забор", callback_data="type_Деревянный")],
    [InlineKeyboardButton(text="Штакетник", callback_data="type_Штакетник")],
    [InlineKeyboardButton(text="Еврозабор (бетон)", callback_data="type_Еврозабор")],
    [InlineKeyboardButton(text="Другой / Не уверен", callback_data="type_Другой")]
])

@dp.message(F.text, F.text.lower().in_(["/start", "start"]))
async def start(message: Message):
    await message.answer(
        "Здравствуйте, Вы обратились в компанию Zabory72.ru!", reply_markup=main_menu)

@dp.callback_query(F.data == "choose_type")
async def choose_type(callback: CallbackQuery):
    await callback.message.edit_text("Какой тип забора вас интересует?", reply_markup=types_keyboard)

@dp.callback_query(F.data.startswith("type_"))
async def type_chosen(callback: CallbackQuery):
    fence_type = callback.data[5:]
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data=f"info_{fence_type}")],
        [InlineKeyboardButton(text="Рассчитать стоимость", callback_data=f"calc_{fence_type}")]
    ])
    await callback.message.edit_text(f"Вы выбрали: {fence_type}. Что дальше?", reply_markup=markup)

@dp.callback_query(F.data.startswith("calc_"))
async def start_calc(callback: CallbackQuery, state: FSMContext):
    fence_type = callback.data[5:]
    await state.set_state(CostCalc.length)
    await state.update_data(fence_type=fence_type)
    await callback.message.answer("Введите протяженность забора в метрах:", reply_markup=ReplyKeyboardRemove())

@dp.message(CostCalc.length)
async def get_length(message: Message, state: FSMContext):
    await state.update_data(length=message.text)
    await state.set_state(CostCalc.height)
    await message.answer("Введите высоту забора в метрах:")

@dp.message(CostCalc.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await state.set_state(CostCalc.extras)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ворота", callback_data="extra_ворота")],
        [InlineKeyboardButton(text="Калитка", callback_data="extra_калитка")],
        [InlineKeyboardButton(text="Оба", callback_data="extra_оба")],
        [InlineKeyboardButton(text="Не нужно", callback_data="extra_нет")],
    ])
    await message.answer("Нужны ли ворота или калитка?", reply_markup=markup)

@dp.callback_query(F.data.startswith("extra_"))
async def get_extra(callback: CallbackQuery, state: FSMContext):
    await state.update_data(extra=callback.data[6:])
    await state.set_state(CostCalc.contact)
    await callback.message.answer("Оставьте ваш номер телефона для связи:")

@dp.message(CostCalc.contact)
async def get_contact(message: Message, state: FSMContext):
    user_data = await state.update_data(contact=message.text)
    await message.answer("Спасибо! Мы свяжемся с вами скоро.", reply_markup=main_menu)

    # Отправка админу
    info = user_data | {"user": message.from_user.username or message.from_user.full_name}
    text = (f"<b>Новая заявка на расчет</b>\n"
            f"Тип: {info['fence_type']}\n"
            f"Длина: {info['length']} м\n"
            f"Высота: {info['height']} м\n"
            f"Дополнительно: {info['extra']}\n"
            f"Контакт: {info['contact']}\n"
            f"Пользователь: @{info['user']}")
    await bot.send_message(ADMIN_ID, text)
    await state.clear()

# Аналогично можно реализовать заявки на замер, галерею и FAQ

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())



