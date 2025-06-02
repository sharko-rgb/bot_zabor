import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command

# Укажи токен своего бота
API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # Укажи свой Telegram user ID

# Создание бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Клавиатуры
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1. Выбрать тип забора", callback_data="choose_type")],
    [InlineKeyboardButton(text="2. Рассчитать стоимость", callback_data="calculate")],
    [InlineKeyboardButton(text="3. Заявка на замер", callback_data="order_measure")],
    [InlineKeyboardButton(text="4. Примеры работ", callback_data="examples")],
    [InlineKeyboardButton(text="5. Вопрос специалисту", callback_data="ask_question")],
    [InlineKeyboardButton(text="6. Контакты", callback_data="contacts")],
])

type_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Профнастил", callback_data="type_profnastil")],
    [InlineKeyboardButton(text="Сетка-рабица", callback_data="type_rabica")],
    [InlineKeyboardButton(text="Металлопрофиль", callback_data="type_metall")],
    [InlineKeyboardButton(text="Деревянный забор", callback_data="type_wood")],
    [InlineKeyboardButton(text="Штакетник", callback_data="type_shtaket")],
    [InlineKeyboardButton(text="Еврозабор", callback_data="type_euro")],
    [InlineKeyboardButton(text="Другой / Не уверен", callback_data="type_other")],
])

followup_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Подробнее", callback_data="more_info")],
    [InlineKeyboardButton(text="Рассчитать стоимость", callback_data="calculate")],
])

# Машина состояний
class CalcForm(StatesGroup):
    length = State()
    height = State()
    type = State()
    gates = State()
    name = State()
    phone = State()

# Обработчики
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Здравствуйте! Вы обратились в компанию <b>Zabory72.ru</b>\n"
        "Супермаркет металлических заборов под ключ и навесов.\n"
        "Выберите действие:",
        reply_markup=main_menu_kb
    )

@dp.callback_query(F.data == "choose_type")
async def choose_type(callback: CallbackQuery):
    await callback.message.edit_text("Какой тип забора вас интересует?", reply_markup=type_menu_kb)

@dp.callback_query(F.data.startswith("type_"))
async def show_type_options(callback: CallbackQuery):
    await callback.message.answer("Отлично! Хотите узнать подробнее или сразу рассчитать стоимость?", reply_markup=followup_kb)

@dp.callback_query(F.data == "calculate")
async def calc_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите протяженность забора (в метрах):")
    await state.set_state(CalcForm.length)

@dp.message(CalcForm.length)
async def calc_height(message: Message, state: FSMContext):
    await state.update_data(length=message.text)
    await message.answer("Введите высоту забора (в метрах):")
    await state.set_state(CalcForm.height)

@dp.message(CalcForm.height)
async def calc_type(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Введите тип забора:")
    await state.set_state(CalcForm.type)

@dp.message(CalcForm.type)
async def calc_gates(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer("Нужны ли ворота/калитка? (варианты: ворота, калитка, оба, не нужно)")
    await state.set_state(CalcForm.gates)

@dp.message(CalcForm.gates)
async def calc_name(message: Message, state: FSMContext):
    await state.update_data(gates=message.text)
    await message.answer("Введите ваше имя:")
    await state.set_state(CalcForm.name)

@dp.message(CalcForm.name)
async def calc_phone(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(CalcForm.phone)

@dp.message(CalcForm.phone)
async def calc_finish(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await state.clear()

    msg = (
        f"Новая заявка на расчет:\n"
        f"Протяженность: {data['length']} м\n"
        f"Высота: {data['height']} м\n"
        f"Тип: {data['type']}\n"
        f"Ворота/Калитка: {data['gates']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}"
    )
    await message.answer("Спасибо! Наш менеджер скоро свяжется с вами.")
    await bot.send_message(chat_id=ADMIN_ID, text=msg)

@dp.callback_query(F.data == "order_measure")
async def order_measure(callback: CallbackQuery):
    await callback.message.answer("Пожалуйста, напишите ваше имя, телефон и адрес для замера.")

@dp.callback_query(F.data == "examples")
async def examples(callback: CallbackQuery):
    await callback.message.answer("Примеры наших работ: (фото можно загрузить сюда)")

@dp.callback_query(F.data == "ask_question")
async def ask_question(callback: CallbackQuery):
    await callback.message.answer("Пожалуйста, напишите ваш вопрос. Наш специалист скоро ответит.")

@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    await callback.message.answer(
        "Наши контакты:\n"
        "📍 Адрес: г. Тюмень, ул. Примерная 1\n"
        "📞 Телефон: +7 (3452) 000-000\n"
        "🕒 Время работы: Пн-Сб 9:00–18:00\n"
        "🌐 Сайт: https://zabory72.ru"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




