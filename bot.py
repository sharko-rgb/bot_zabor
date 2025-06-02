import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = '7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0'
ADMIN_ID = 1346038165  # Replace with your real admin ID

bot = Bot(token=API_TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# FSM
class Form(StatesGroup):
    choosing_fence = State()
    collecting_details = State()
    asking_question = State()
    measurement_request = State()
    collecting_contacts = State()

fence_types = [
    ("Профнастил", "profnastil"),
    ("Сетка-рабица", "setka"),
    ("Металлопрофиль", "metal"),
    ("Деревянный забор", "wood"),
    ("Штакетник", "shtaket"),
    ("Еврозабор", "euro"),
    ("Другой / Не уверен", "other")
]

fence_descriptions = {
    "profnastil": "Профнастил — недорогой и прочный вариант...",
    "setka": "Сетка-рабица — прозрачный и лёгкий забор...",
    "metal": "Металлопрофиль — эстетичный и долговечный...",
    "wood": "Деревянный забор — классика уюта...",
    "shtaket": "Штакетник — современный стиль и проветривание...",
    "euro": "Еврозабор — бетонная надежность...",
    "other": "Вы можете уточнить позже или обсудить с мастером."
}

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="1. Выбрать тип забора", callback_data="choose_fence")
    kb.button(text="2. Рассчитать стоимость", callback_data="calculate")
    kb.button(text="3. Заявка на замер", callback_data="measure")
    kb.button(text="4. Примеры работ", callback_data="examples")
    kb.button(text="5. Вопрос специалисту", callback_data="question")
    kb.button(text="6. Контакты", callback_data="contacts")
    return kb.as_markup()

def fence_type_menu():
    kb = InlineKeyboardBuilder()
    for label, key in fence_types:
        kb.button(text=label, callback_data=f"fence_{key}")
    kb.button(text="◀️ Главное меню", callback_data="main")
    return kb.as_markup()

@dp.message(F.text, ~F.via_bot)
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте! Вы обратились в <b>Zabory72.ru</b>. Выберите нужный пункт:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "main")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())

@dp.callback_query(F.data == "choose_fence")
async def choose_fence(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.choosing_fence)
    await call.message.edit_text("Какой тип забора вас интересует?", reply_markup=fence_type_menu())

@dp.callback_query(F.data.startswith("fence_"))
async def selected_fence(call: types.CallbackQuery, state: FSMContext):
    fence_key = call.data.replace("fence_", "")
    await state.update_data(fence_type=fence_key)
    desc = fence_descriptions.get(fence_key, "Описание отсутствует.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data="info")],
        [InlineKeyboardButton(text="Рассчитать стоимость", callback_data="calculate")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main")]
    ])
    await call.message.edit_text(f"Вы выбрали: <b>{dict(fence_types)[fence_key]}</b>\n{desc}", reply_markup=kb)

@dp.callback_query(F.data == "calculate")
async def start_calculation(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.collecting_details)
    await call.message.edit_text("Введите протяженность забора в метрах:")

@dp.message(Form.collecting_details)
async def get_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text)
        await state.update_data(length=length)
        await message.answer("Теперь укажите высоту забора в метрах:")
        await state.set_state(Form.collecting_contacts)
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@dp.message(Form.collecting_contacts)
async def get_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text)
        data = await state.get_data()
        fence_type = data.get("fence_type", "Не выбран")
        length = data.get("length")
        cost = int(length * height * 500)  # Пример расчета

        summary = f"<b>Тип:</b> {dict(fence_types).get(fence_type, 'Не выбран')}\n<b>Длина:</b> {length} м\n<b>Высота:</b> {height} м\n<b>Примерная стоимость:</b> {cost} руб."

        await bot.send_message(ADMIN_ID, f"Новая заявка на расчет:\n{summary}")
        await message.answer(f"Спасибо! {summary}\n\nНаш менеджер скоро свяжется с вами."
                             , reply_markup=main_menu())
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@dp.callback_query(F.data == "measure")
async def request_measure(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.measurement_request)
    await call.message.edit_text("Введите ваше имя, телефон и адрес замера:")

@dp.message(Form.measurement_request)
async def collect_measure_data(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"Заявка на замер: {message.text}")
    await message.answer("Спасибо! Мы свяжемся с вами для согласования времени.", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "examples")
async def show_examples(call: types.CallbackQuery):
    await call.message.answer("Вот несколько наших работ:")
    await call.message.answer_photo(photo="https://via.placeholder.com/600x400", caption="Пример 1")
    await call.message.answer_photo(photo="https://via.placeholder.com/600x400", caption="Пример 2")

@dp.callback_query(F.data == "question")
async def ask_question(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.asking_question)
    await call.message.edit_text("Задайте ваш вопрос специалисту:")

@dp.message(Form.asking_question)
async def receive_question(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"Вопрос от пользователя: {message.text}")
    await message.answer("Спасибо! Мы ответим вам в ближайшее время.", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "contacts")
async def contacts(call: types.CallbackQuery):
    await call.message.edit_text("<b>Контакты:</b>\nАдрес: г. Тюмень...\nТелефон: +7 900 000 0000\nСайт: zabory72.ru\nEmail: info@zabory72.ru",
                                 reply_markup=main_menu())

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))




