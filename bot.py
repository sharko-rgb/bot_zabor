import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = '7853853505:AAEhTPDeWUlX67naGu5JhW9-maep1yesUD0'  # Замените на свой токен

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Приветственное сообщение
WELCOME_TEXT = """
Здравствуйте, Вы обратились в компанию *Zabory72.ru* – супермаркет металлических заборов «под ключ», в том числе каменных, из кирпича и керамзитоблоков. Также мы строим металлические навесы для автомобилей.
"""

# Главное меню
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="1. Выбрать тип забора", callback_data="choose_fence")
    kb.button(text="2. Рассчитать стоимость", callback_data="calc_cost")
    kb.button(text="3. Заявка на замер", callback_data="leave_request")
    kb.button(text="4. Примеры работ", callback_data="examples")
    kb.button(text="5. Вопрос специалисту", callback_data="ask_question")
    kb.button(text="6. Контакты", callback_data="contacts")
    kb.adjust(2)
    return kb.as_markup()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)
    await message.answer("Выберите интересующий вас пункт:", reply_markup=main_menu())

# Обработка пунктов главного меню
@dp.callback_query(F.data == "choose_fence")
async def choose_fence(callback: CallbackQuery):
    fence_types = [
        "Забор из профнастила",
        "Профлист в рамке",
        "Евроштакетник вертикально",
        "Евроштакетник горизонтально",
        "Забор Жалюзи",
        "Забор Ранчо (двойной)",
        "Забор Ранчо (одинарный)",
        "Забор из 3Д сетки",
        "Ворота откатные",
        "Ворота распашные + Калитка",
        "Навесы для автомобиля"
    ]
    kb = InlineKeyboardBuilder()
    for i, ftype in enumerate(fence_types, 1):
        kb.button(text=f"{i}. {ftype}", callback_data=f"fence_{i}")
    kb.adjust(1)
    await callback.message.answer("Какой тип забора Вас интересует?", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("fence_"))
async def fence_selected(callback: CallbackQuery):
    await callback.message.answer("Отлично! Хотите узнать подробнее и сразу рассчитать стоимость?")
    await callback.answer()

# Стоимость
@dp.callback_query(F.data == "calc_cost")
async def calculate_cost(callback: CallbackQuery):
    await callback.message.answer("Выберите интересующий тип и высоту для оценки стоимости.")
    price_table = """
📐 *Примерные цены «под ключ» (материалы + монтаж):*

1. Профнастил – 3474 руб. (h=1.8м), 3650 руб. (h=2.0м)  
2. Профлист в рамке – 6140 / 6500 руб.  
3. Евроштакетник (вертикально) – 7620 / 8260 руб.  
4. Евроштакетник (горизонтально) – 9650 / 10350 руб.  
5. Жалюзи – 8700 руб.  
6. Ранчо (двойной) – 14500 руб.  
7. Ранчо (одинарный) – 11000 руб.  
8. 3Д сетка – 3100 руб.  
9. Ворота откатные – 87000 руб.  
10. Ворота распашные + калитка – 37000 руб.  
11. Навесы – от 7500 руб./м²
"""
    await callback.message.answer(price_table, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

# Заявка на замер
@dp.callback_query(F.data == "leave_request")
async def leave_request(callback: CallbackQuery):
    await callback.message.answer("Пожалуйста, отправьте нам ваше имя, адрес объекта и номер телефона для записи на бесплатный замер.")
    await callback.answer()

# Примеры работ
@dp.callback_query(F.data == "examples")
async def examples(callback: CallbackQuery):
    await callback.message.answer("Вот некоторые из наших работ (фото добавим позже). Также смотрите в [нашей группе ВКонтакте](https://vk.com/zabory72).", parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

# Вопрос специалисту
@dp.callback_query(F.data == "ask_question")
async def ask_specialist(callback: CallbackQuery):
    await callback.message.answer("Пожалуйста, отправьте ваш вопрос, и наш специалист ответит вам в ближайшее время.")
    await callback.answer()

# Контакты
@dp.callback_query(F.data == "contacts")
async def contacts(callback: CallbackQuery):
    contact_text = """
📞 *Контакты:*

Телефон: +7 (3452) 500-600  
Сайт: [https://zabory72.ru](https://zabory72.ru)  
E-mail: info@zabory72.ru  
"""
    await callback.message.answer(contact_text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

