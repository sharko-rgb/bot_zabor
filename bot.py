from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # Твой Telegram ID

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class Form(StatesGroup):
    choosing_fence_type = State()
    fence_details = State()
    calculating_length = State()
    calculating_height = State()
    calculating_gate = State()
    getting_name = State()
    getting_phone = State()
    getting_address = State()
    asking_question = State()

# Клавиатуры
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать тип забора", callback_data="choose_fence")],
        [InlineKeyboardButton(text="Рассчитать стоимость", callback_data="calculate_price")],
        [InlineKeyboardButton(text="Оставить заявку на замер", callback_data="order_measurement")],
        [InlineKeyboardButton(text="Посмотреть примеры работ", callback_data="show_examples")],
        [InlineKeyboardButton(text="Задать вопрос специалисту", callback_data="ask_specialist")],
        [InlineKeyboardButton(text="Контакты", callback_data="contacts")]
    ])

def fence_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Профнастил", callback_data="fence_prof")],
        [InlineKeyboardButton(text="Сетка-рабица", callback_data="fence_mesh")],
        [InlineKeyboardButton(text="Металлопрофиль", callback_data="fence_metal")],
        [InlineKeyboardButton(text="Деревянный забор", callback_data="fence_wood")],
        [InlineKeyboardButton(text="Штакетник", callback_data="fence_shtaketnik")],
        [InlineKeyboardButton(text="Еврозабор (бетонный)", callback_data="fence_euro")],
        [InlineKeyboardButton(text="Другой / Не уверен", callback_data="fence_other")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_main")]
    ])

def yes_no_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data="more_info")],
        [InlineKeyboardButton(text="Рассчитать стоимость", callback_data="calculate_price")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_main")]
    ])

def gate_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ворота", callback_data="gate_gate")],
        [InlineKeyboardButton(text="Калитка", callback_data="gate_door")],
        [InlineKeyboardButton(text="Ворота и калитка", callback_data="gate_both")],
        [InlineKeyboardButton(text="Не нужно", callback_data="gate_none")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_main")]
    ])

# Описания заборов для "Подробнее"
fence_descriptions = {
    "fence_prof": "Профнастил - надежный и бюджетный материал. Отлично защищает участок.",
    "fence_mesh": "Сетка-рабица - экономичный и легкий вариант забора.",
    "fence_metal": "Металлопрофиль - прочный, устойчивый к внешним воздействиям.",
    "fence_wood": "Деревянный забор - экологичный и красивый, но требует ухода.",
    "fence_shtaketnik": "Штакетник - классический деревянный забор с аккуратным видом.",
    "fence_euro": "Еврозабор - бетонный забор высокой прочности и надежности.",
    "fence_other": "Мы поможем подобрать подходящий вариант под ваш проект."
}

# Старт
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте, Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов «под ключ».",
        reply_markup=main_menu_kb()
    )

# Главное меню
@dp.callback_query(F.data == "choose_fence")
async def choose_fence(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Какой тип забора вас интересует?", reply_markup=fence_type_kb())
    await state.set_state(Form.choosing_fence_type)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню", reply_markup=main_menu_kb())

@dp.callback_query(F.data.startswith("fence_"))
async def fence_type_selected(callback: CallbackQuery, state: FSMContext):
    fence_type = callback.data
    await state.update_data(fence_type=fence_type)
    await callback.message.edit_text(
        f"Вы выбрали: {fence_type[6:].capitalize()}\nХотите узнать подробнее или сразу рассчитать стоимость?",
        reply_markup=yes_no_kb()
    )
    await state.set_state(Form.fence_details)

@dp.callback_query(F.data == "more_info")
async def more_info(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fence_type = data.get("fence_type")
    text = fence_descriptions.get(fence_type, "Информация отсутствует.")
    await callback.message.edit_text(
        f"{text}\n\nХотите рассчитать стоимость?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рассчитать стоимость", callback_data="calculate_price")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_main")]
        ])
    )
    await state.set_state(Form.calculating_length)

@dp.callback_query(F.data == "calculate_price")
async def calculate_price_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fence_type = data.get("fence_type")
    if not fence_type:
        await callback.message.edit_text("Сначала выберите тип забора.", reply_markup=fence_type_kb())
        await state.set_state(Form.choosing_fence_type)
        return
    await callback.message.edit_text("Введите протяженность забора в метрах (число):")
    await state.set_state(Form.calculating_length)

@dp.message(Form.calculating_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError()
        await state.update_data(length=length)
        await message.answer("Введите высоту забора в метрах (число):")
        await state.set_state(Form.calculating_height)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число для протяженности.")

@dp.message(Form.calculating_height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text.replace(",", "."))
        if height <= 0:
            raise ValueError()
        await state.update_data(height=height)
        await message.answer("Выберите, нужны ли ворота или калитка:", reply_markup=gate_kb())
        await state.set_state(Form.calculating_gate)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число для высоты.")

@dp.callback_query(F.data.startswith("gate_"))
async def process_gate(callback: CallbackQuery, state: FSMContext):
    gate = callback.data
    if gate == "back_to_main":
        await state.clear()
        await callback.message.edit_text("Главное меню", reply_markup=main_menu_kb())
        return
    await state.update_data(gate=gate)
    await callback.message.edit_text("Пожалуйста, введите ваше имя:")
    await state.set_state(Form.getting_name)

@dp.message(Form.getting_name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш телефон:")
    await state.set_state(Form.getting_phone)

@dp.message(Form.getting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 5:
        await message.answer("Пожалуйста, введите корректный телефон.")
        return
    await state.update_data(phone=phone)
    data = await state.get_data()
    fence_type = data.get("fence_type")
    length = data.get("length")
    height = data.get("height")
    gate = data.get("gate")
    name = data.get("name")
    phone = data.get("phone")

    # Пример расчёта стоимости
    base_price_per_meter = 3500
    total_price = base_price_per_meter * length

    text = (
        f"<b>Новая заявка на расчет стоимости</b>\n"
        f"Тип забора: {fence_type[6:].capitalize()}\n"
        f"Протяженность: {length} м\n"
        f"Высота: {height} м\n"
        f"Ворота/Калитка: {gate[5:].capitalize()}\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Примерная стоимость: {total_price:.2f} руб."
    )

    await message.answer("Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.")
    await bot.send_message(ADMIN_ID, text)
    await state.clear()

@dp.callback_query(F.data == "order_measurement")
async def order_measurement(callback: CallbackQuery):
    await callback.message.edit_text("Пожалуйста, введите ваше имя:")
    await Form.getting_name.set()

@dp.message(Form.getting_name)
async def process_order_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш телефон:")
    await state.set_state(Form.getting_phone)

@dp.message(Form.getting_phone)
async def process_order_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("Введите адрес для замера:")
    await state.set_state(Form.getting_address)

@dp.message(Form.getting_address)
async def process_order_address(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    phone = data.get("phone")
    address = message.text.strip()

    text = (
        f"<b>Заявка на замер</b>\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Адрес: {address}"
    )
    await message.answer("Спасибо! Ваша заявка на замер принята.")
    await bot.send_message(ADMIN_ID, text)
    await state.clear()

@dp.callback_query(F.data == "show_examples")
async def show_examples(callback: CallbackQuery):
    await callback.message.edit_text("Ссылка на примеры работ:\nhttps://vk.com/album-123456789_123456789")

@dp.callback_query(F.data == "ask_specialist")
async def ask_specialist(callback: CallbackQuery):
    await callback.message.edit_text("Пожалуйста, напишите ваш вопрос специалисту:")
    await Form.asking_question.set()

@dp.message(Form.asking_question)
async def process_question(message: Message, state: FSMContext):
    question = message.text.strip()
    await bot.send_message(ADMIN_ID, f"<b>Вопрос от пользователя:</b>\n{question}")
    await message.answer("Спасибо за вопрос! Мы свяжемся с вами в ближайшее время.")
    await state.clear()

@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        "Наши контакты:\n"
        "📞 Телефон: +7 (3452) 678-901\n"
        "🌐 Сайт: https://zabory72.ru\n"
        "📍 Адрес: г. Тюмень, ул. Примерная, д. 1",
        reply_markup=main_menu_kb()
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))






