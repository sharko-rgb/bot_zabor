from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

API_TOKEN = "7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0"
ADMIN_ID = 1346038165  # твой ID

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Form(StatesGroup):
    choosing_fence_type = State()

    fence_details = State()
    calculating_length = State()
    calculating_height = State()
    calculating_gate = State()
    getting_name_price = State()
    getting_phone_price = State()

    getting_name_measure = State()
    getting_phone_measure = State()
    getting_address_measure = State()

    asking_question = State()

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Выбрать тип забора", callback_data="choose_fence")],
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate_price")],
        [InlineKeyboardButton("Оставить заявку на замер", callback_data="order_measurement")],
        [InlineKeyboardButton("Посмотреть примеры работ", callback_data="show_examples")],
        [InlineKeyboardButton("Задать вопрос специалисту", callback_data="ask_specialist")],
        [InlineKeyboardButton("Контакты", callback_data="contacts")]
    ])

def fence_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Профнастил", callback_data="fence_prof")],
        [InlineKeyboardButton("Сетка-рабица", callback_data="fence_mesh")],
        [InlineKeyboardButton("Металлопрофиль", callback_data="fence_metal")],
        [InlineKeyboardButton("Деревянный забор", callback_data="fence_wood")],
        [InlineKeyboardButton("Штакетник", callback_data="fence_shtaketnik")],
        [InlineKeyboardButton("Еврозабор (бетонный)", callback_data="fence_euro")],
        [InlineKeyboardButton("Другой / Не уверен", callback_data="fence_other")],
        [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
    ])

def yes_no_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Подробнее", callback_data="more_info")],
        [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate_price")],
        [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
    ])

def gate_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Ворота", callback_data="gate_gate")],
        [InlineKeyboardButton("Калитка", callback_data="gate_door")],
        [InlineKeyboardButton("Ворота и калитка", callback_data="gate_both")],
        [InlineKeyboardButton("Не нужно", callback_data="gate_none")],
        [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
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

@dp.callback_query(Text("choose_fence"))
async def choose_fence(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "fence_type" in data:
        # Если уже выбран, сразу показываем выбор с подсказкой
        fence_type = data["fence_type"]
        await callback.message.edit_text(
            f"Ваш текущий тип забора: <b>{fence_type[6:].capitalize()}</b>\n"
            "Если хотите изменить, выберите заново:",
            reply_markup=fence_type_kb()
        )
    else:
        await callback.message.edit_text("Какой тип забора вас интересует?", reply_markup=fence_type_kb())
    await state.set_state(Form.choosing_fence_type)

@dp.callback_query(Text("back_to_main"))
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню", reply_markup=main_menu_kb())

@dp.callback_query(Text(startswith="fence_"))
async def fence_type_selected(callback: CallbackQuery, state: FSMContext):
    fence_type = callback.data
    await state.update_data(fence_type=fence_type)
    await callback.message.edit_text(
        f"Вы выбрали: <b>{fence_type[6:].capitalize()}</b>\n"
        "Хотите узнать подробнее или сразу рассчитать стоимость?",
        reply_markup=yes_no_kb()
    )
    await state.set_state(Form.fence_details)

@dp.callback_query(Text("more_info"))
async def more_info(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fence_type = data.get("fence_type")
    text = fence_descriptions.get(fence_type, "Информация отсутствует.")
    await callback.message.edit_text(
        f"{text}\n\nХотите рассчитать стоимость?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Рассчитать стоимость", callback_data="calculate_price")],
            [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
        ])
    )
    await state.set_state(Form.calculating_length)

@dp.callback_query(Text("calculate_price"))
async def calculate_price_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fence_type = data.get("fence_type")
    if not fence_type:
        await callback.message.edit_text("Сначала выберите тип забора.", reply_markup=fence_type_kb())
        await state.set_state(Form.choosing_fence_type)
        return
    await callback.message.edit_text("Введите протяженность забора в метрах (число):\n\n(Кнопка «Назад в меню» всегда доступна внизу)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
    ]))
    await state.set_state(Form.calculating_length)

@dp.message(Form.calculating_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError()
        await state.update_data(length=length)
        await message.answer("Введите высоту забора в метрах (число):\n\n(Кнопка «Назад в меню» в меню)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Назад в меню", callback_data="back_to_main")]
        ]))
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
    await state.set_state(Form.getting_name_price)

@dp.message(Form.getting_name_price)
async def process_name_price(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш телефон:")
    await state.set_state(Form.getting_phone_price)

@dp.message(Form.getting_phone_price)
async def process_phone_price(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 5:
        await message.answer("Пожалуйста, введите корректный телефон.")
        return
    await state.update_data(phone=phone)
    data = await state.get_data()

    # Рассчитаем примерную стоимость (пример)
    price_per_meter = 1500  # рубли за метр, пример
    length = data.get("length", 0)
    height = data.get("height", 0)
    gate = data.get("gate", "gate_none")

    base_price = length * height * price_per_meter
    gate_price = 0
    if gate == "gate_gate":
        gate_price = 8000
    elif gate == "gate_door":
        gate_price = 3000
    elif gate == "gate_both":
        gate_price = 11000

    total_price = base_price + gate_price

    text = (
        f"Новая заявка на расчет стоимости забора:\n"
        f"Тип забора: {data.get('fence_type')[6:].capitalize()}\n"
        f"Длина: {length} м\n"
        f"Высота: {height} м\n"
        f"Ворота/калитка: {gate[5:]}\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {phone}\n"
        f"Примерная стоимость: {int(total_price)} ₽"
    )
    await bot.send_message(ADMIN_ID, text)
    await message.answer(f"Спасибо! Ваша заявка отправлена.\nПримерная стоимость: {int(total_price)} ₽", reply_markup=main_menu_kb())
    await state.clear()

@dp.callback_query(Text("order_measurement"))
async def order_measurement(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите ваше имя:")
    await state.set_state(Form.getting_name_measure)

@dp.message(Form.getting_name_measure)
async def measurement_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш телефон:")
    await state.set_state(Form.getting_phone_measure)

@dp.message(Form.getting_phone_measure)
async def measurement_phone(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("Пожалуйста, введите корректный телефон.")
        return
    await state.update_data(phone=message.text.strip())
    await message.answer("Введите адрес установки забора:")
    await state.set_state(Form.getting_address_measure)

@dp.message(Form.getting_address_measure)
async def measurement_address(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("Пожалуйста, введите корректный адрес.")
        return
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    text = (
        f"Новая заявка на замер забора:\n"
        f"Имя: {data.get('name')}\n"
        f"Телефон: {data.get('phone')}\n"
        f"Адрес: {data.get('address')}"
    )
    await bot.send_message(ADMIN_ID, text)
    await message.answer("Спасибо! Ваша заявка на замер отправлена.", reply_markup=main_menu_kb())
    await state.clear()

@dp.callback_query(Text("ask_specialist"))
async def ask_specialist(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите ваш вопрос:")
    await state.set_state(Form.asking_question)

@dp.message(Form.asking_question)
async def process_question(message: Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("Пожалуйста, задайте более подробный вопрос.")
        return
    text = f"Вопрос от пользователя:\n{message.text}\n\nОт пользователя: @{message.from_user.username or message.from_user.full_name}"
    await bot.send_message(ADMIN_ID, text)
    await message.answer("Спасибо! Ваш вопрос отправлен специалисту.", reply_markup=main_menu_kb())
    await state.clear()

@dp.callback_query(Text("show_examples"))
async def show_examples(callback: CallbackQuery):
    # Здесь можно добавить показ фото/примеров работ
    await callback.message.edit_text("Примеры наших работ скоро появятся.", reply_markup=main_menu_kb())

@dp.callback_query(Text("contacts"))
async def contacts(callback: CallbackQuery):
    await callback.message.edit_text(
        "Наши контакты:\n"
        "📞 Телефон: +7 (999) 999-99-99\n"
        "📍 Адрес: г. Тюмень, ул. Примерная, 1\n"
        "🌐 Сайт: https://zabory72.ru",
        reply_markup=main_menu_kb()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())





