import asyncio

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput, MessageInput
from environs import Env
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog.widgets.kbd import Button, Row, Column, Url, Select, Group, Back, Next, Cancel, Start, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Calendar
from datetime import date
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from aiogram_dialog import Dialog, DialogManager, StartMode, Window, setup_dialogs


env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')
CHAT_ID = env('CHAT_ID')

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

router = Router()

expenses = {}


class StartSG(StatesGroup):
    start = State()
    category = State()
    no_click = State()

    refueling = State()
    highway = State()
    parking = State()
    washing = State()
    fine = State()
    tax = State()
    osago = State()
    kasko = State()
    other = State()
    other_selected = State()

    mileage = State()
    expense = State()
    choice_date = State()
    calendar = State()
    send_message = State()
    result = State()

    choice_change = State()


# Выбор Категории
async def category_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str):
    categories = await category_getter()
    selected_category = next((category for category in categories['categories'] if str(category[1]) == str(item_id)),
                             None)
    if selected_category:
        dialog_manager.dialog_data['category'] = selected_category[0]
        expenses.update(dialog_manager.dialog_data)
        print(expenses)
        if selected_category[1] == 9:
            await dialog_manager.switch_to(state=StartSG.other_selected)
        else:
            await dialog_manager.switch_to(state=StartSG.mileage)


# Отправка не текста
async def no_text(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['item'] = 'Новая покупка'
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.mileage)
    await message.send_copy(chat_id=CHAT_ID)


# Отправка текста, где он не предполагается
def not_text(text):
    if isinstance(text, str):
        return text
    raise ValueError


async def not_text_answer(message: Message, callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager):
    await message.answer('Здесь не предполагается ввод текста')
    await message.delete()


async def not_text_answer_other(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    await message.answer('В данном окне не предполагается отправка данного типа сообщения')
    await message.delete()


# Ввод покупки в Прочее
def add_text_other(text):
    if isinstance(text, str):
        return text
    raise ValueError


async def correct_text_other(message: Message, widget: TextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['category'] = 'Прочее 🛒: ' + text
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.mileage)


async def error_text_other(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, error: ValueError):
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.other_selected)


# Ввод Пробега и Расхода
def add_text_mileage(text):
    if all(ch.isdigit() for ch in text) and 1 <= len(text) <= 6:
        return text
    raise ValueError


async def correct_text_mileage(message: Message, widget: TextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['mileage'] = str(int(text) // 1000) + ' ' + str(text[-3:]) + ' км'
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.expense)


async def error_text_mileage(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager,
                             error: ValueError):
    await message.answer('Введите число')
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.mileage)



async def skip_mileage(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    dialog_manager.dialog_data['mileage'] = 'Не указан'
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await dialog_manager.switch_to(state=StartSG.choice_date)


def add_text_expense(text):
    if all(ch.isdigit() for ch in text) and 1 <= len(text) <= 6:
        return text
    raise ValueError


async def correct_text_expense(message: Message, widget: TextInput, dialog_manager: DialogManager, text: str):
    if int(text) >= 1000:
        dialog_manager.dialog_data['expense'] = str(int(text) // 1000) + ' ' + text[-3:] + ' руб.'
    else:
        dialog_manager.dialog_data['expense'] = text + ' руб.'
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.choice_date)


async def error_text_expense(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager,
                             error: ValueError):
    await message.answer('Введите число')
    await message.delete()
    await dialog_manager.switch_to(state=StartSG.expense)


# Выбор даты
async def date_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    dialog_manager.dialog_data['date'] = widget.text.text
    expenses.update(dialog_manager.dialog_data)
    print(expenses)


# Календарь
async def calendar(callback: CallbackQuery, widget, dialog_manager: DialogManager, selected_date: date):
    dialog_manager.dialog_data['date'] = selected_date.strftime("%d.%m.%Y г.")
    expenses.update(dialog_manager.dialog_data)
    print(expenses)
    await dialog_manager.switch_to(state=StartSG.result)


# ГЕТТЕРЫ
# Username
async def username_getter(event_from_user: User, **kwargs):
    return {'username': event_from_user.first_name}


# Категории
async def category_getter(**kwargs):
    categories = [
        ('Заправка ⛽️', 1), ('Дорога 🛣', 2), ('Парковка 🅿️ ', 3),
        ('Мойка 🧽', 4), ('Штраф 👮‍♂️', 5), ('Налог 💵', 6),
        ('ОСАГО 🎫', 7), ('КАСКО 🎟', 8), ('Прочее 🛒', 9)
    ]
    return {'categories': categories}


# Результат
async def result_getter(**kwargs):
    return {'date': expenses['date'], 'category': expenses['category'],
            'mileage': expenses['mileage'], 'expense': expenses['expense'], }


# Отправка сообщения
async def send_message(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    message = (f"🚨 <b><u>НОВЫЙ РАСХОД</u></b> 🚨\n\n"
               f"<b>📆   Дата:</b>   {expenses['date']}\n"
               f"<b>🚙   Категория:</b>   {expenses['category']}\n"
               f"<b>🔢   Пробег:</b>   {expenses['mileage']}\n"
               f"<b>💸   Стоимость:</b>   {expenses['expense']}")
    await bot.send_message(chat_id=CHAT_ID, text=message)


start_dialog = Dialog(
    # ПРИВЕТСТВИЕ
    Window(
        Const('Хорошо, но обязательно запомни текущий пробег автомобиля!'),
        SwitchTo(Const('✅ Внести расходы'), id='yes', state=StartSG.category),
        state=StartSG.no_click,
    ),
    Window(
        Format('<b>Привет, {username}!☺️</b>\n\n'
               'Если у тебя появились расходы на автомобиль, то внеси их, используя этот бот!'),
        Row(
        Next(Const('✅ Внести'), id='yes'),
            Back(Const('❎ Отложить'), id='no'),
        ),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        getter=username_getter,
        state=StartSG.start,
    ),

    # КАТЕГОРИИ
    Window(
        Const('Выберете <b>категорию</b> расхода 🚙'),
        Group(
            Select(
                Format('{item[0]}'),
                id='category',
                item_id_getter=lambda x: x[1],
                items='categories',
                on_click=category_selection,
            ),
            width=3
        ),
        Back(Const('◀️ Назад'), id='b_back'),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        state=StartSG.category,
        getter=category_getter,
    ),

    # ПРОЧЕЕ
    Window(
        Const('Укажите какая была совершена <b>покупка 🛒</b>'),
        TextInput(id='other', type_factory=add_text_other, on_success=correct_text_other, on_error=error_text_other),
        MessageInput(func=no_text, content_types=ContentType.ANY),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        state=StartSG.other_selected,
    ),

    # ПРОБЕГ
    Window(
        Const('Укажите текущий <b>пробег 🔢</b> автомобиля'),
        TextInput(id='mileage', type_factory=add_text_mileage, on_success=correct_text_mileage,
                  on_error=error_text_mileage),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        SwitchTo(Const('Пропустить ▶️'), id='skip', state=StartSG.expense, on_click=skip_mileage),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        state=StartSG.mileage,
    ),

    # РАСХОД
    Window(
        Const('Укажите <b>стоимость 💸</b> в рублях'),
        TextInput(id='expense', type_factory=add_text_expense, on_success=correct_text_expense,
                  on_error=error_text_expense),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.mileage),
        state=StartSG.expense,
    ),

    # ДАТА
    Window(
        Const('Укажите <b>дату 📆</b>'),
        Group(
            Row(
                SwitchTo(Const('Сегодня 👌 '), id='today', state=StartSG.result, on_click=date_selection),
                SwitchTo(Const('Вчера 👈🏻 '), id='tomorrow', state=StartSG.result, on_click=date_selection),
            ),
            width=2
        ),
        SwitchTo(Const('📆 Выбрать дату'), id='choice_date', state=StartSG.calendar),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.expense),
        SwitchTo(Const('❎ Отменить'), id='cancel', state=StartSG.no_click),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        state=StartSG.choice_date
    ),

    # КАЛЕНДАРЬ
    Window(
        Const('Укажите <b>дату 📆</b>'),
        Calendar(id='calendar', on_click=calendar),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.choice_date),
        SwitchTo(Const('❎ Отменить'), id='cancel', state=StartSG.no_click),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        state=StartSG.calendar
    ),

    # РЕЗУЛЬТАТ
    Window(
        Format('<b>Подтвердите Ваш расход!</b>\n\n'
               '<b>📆   Дата:</b>   {date}\n'
               '<b>🚙   Категория:</b>   {category}\n'
               '<b>🔢   Пробег:</b>   {mileage}\n'
               '<b>💸   Стоимость:</b>   {expense}'
               ),
        SwitchTo(Const('✅ Верно!'), id='yes', state=StartSG.send_message, on_click=send_message),
        Row(
            SwitchTo(Const('🔄 Изменить'), id='change', state=StartSG.choice_change),
            SwitchTo(Const('❎ Отменить'), id='cancel', state=StartSG.no_click),
        ),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        getter=result_getter,
        state=StartSG.result
    ),

    # ВЕРНО
    Window(
        Const('<b>Ваш расход сформирован</b>'),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        state=StartSG.send_message
    ),

    # ИЗМЕНИТЬ
    Window(
        Const('<b>Что Вы хотите изменить?</b>'),
        Group(
            Row(
                SwitchTo(Const('🚙 Категорию'), id='category', state=StartSG.category),
                SwitchTo(Const('🔢 Пробег'), id='mileage', state=StartSG.mileage),
                SwitchTo(Const('💸 Расход'), id='expense', state=StartSG.expense),
                SwitchTo(Const('📆 Дату'), id='date', state=StartSG.choice_date),
            ),
            width=2,
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.result),
        TextInput(id='not_text', type_factory=not_text, on_success=not_text_answer),
        MessageInput(func=not_text_answer_other, content_types=ContentType.ANY),
        state=StartSG.choice_change
    ),
)


# Это классический хэндлер, который будет срабатывать на команду /start
@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)
    await message.delete()


dp.include_router(router)
dp.include_router(start_dialog)
setup_dialogs(dp)
dp.run_polling(bot)
