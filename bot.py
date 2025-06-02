from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.filters.callback_query import CallbackQueryData
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # твой ID телеграм

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML, session=AiohttpSession())
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

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

fence_descriptions = {
    "fence_prof": "Профнастил - надежный и бюджетный материал. Отлично защищает участок.",
    "fence_mesh": "Сетка-рабица - экономичный и легкий вариант забора.",
    "fence_metal": "Металлопрофиль - прочный, устойчивый к внешним воздействиям.",
    "fence_wood": "Деревянный забор - экологичный и красивый, но требует ухода.",
    "fence_shtaketnik": "Штакетник - классический деревянный забор с аккуратным видом.",
    "fence_euro": "Еврозабор - бетонный забор высокой прочности и надежности.",
    "fence_other": "Мы поможем подобрать подходящий вариант под ваш проект."
}

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте, Вы обратились в компанию Zabory72.ru, супермаркет металлических заборов «под ключ».",
        reply_markup=main_menu_kb()
    )

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
        f"Вы выбрали: {fence_type[6:].capitalize()}\n"
        "Хотите узнать подробнее или сразу рассчитать стоимость?",
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

@dp.callback_query(Form.calculating_gate)
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
    if len(message.text) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=message.text)
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

    base_price_per_meter = 3500  # примерная цена за метр
    total_price = base_price_per_meter * length

    text = (
        f"<b>Новая заявка на расчет стоимости</b>\n"
        f"Тип забора: {fence_type[6:].capitalize()}\n"
        f"Протяженность: {length} м\n"
        f"Высота: {height} м\n"
        f"Ворота/Калитка: {gate}\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Примерная стоимость: {total_price} руб."
    )

    await bot.send_message(ADMIN_ID, text)
    await message.answer("Спасибо! Ваша заявка отправлена. Наш менеджер свяжется с вами для уточнения деталей.", reply_markup=main_menu_kb())
    await state.clear()

@dp.callback_query(F.data == "order_measurement")
async def order_measurement(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите ваше имя:")
    await state.set_state(Form.getting_name)

@dp.message(Form.getting_name)
async def order_name(message: Message, state: FSMContext):
    # Этот обработчик уже есть выше, его можно расширить или разделить, если нужно

    # Если хотим разделить логику, можно использовать доп. флаг в state.
    # Для простоты здесь пропущу.

    pass

@dp.callback_query(F.data == "ask_specialist")
async def ask_specialist(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Задайте ваш вопрос специалисту:")
    await state.set_state(Form.asking_question)

@dp.message(Form.asking_question)
async def process_question(message: Message, state: FSMContext):
    question = message.text
    name = message.from_user.full_name
    text = f"Вопрос от {name}:\n{question}"
    await bot.send_message(ADMIN_ID, text)
    await message.answer("Спасибо за вопрос! Мы свяжемся с вами в ближайшее время.", reply_markup=main_menu_kb())
    await state.clear()

@dp.callback_query(F.data == "show_examples")
async def show_examples(callback: CallbackQuery):
    await callback.message.edit_text(
        "Примеры наших работ можно посмотреть на сайте: https://zabory72.ru/gallery",
        reply_markup=main_menu_kb()
    )

@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        "Наши контакты:\n"
        "Телефон: +7 (922) 988-11-74\n"
        "Сайт: https://zabory72.ru\n"
        "Адрес: г.Тюмень, ул. 30 лет Победы 53",
        reply_markup=main_menu_kb()
    )

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())







