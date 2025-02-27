from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from crud_functions import *


initiate_db()

api = ""
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Рассчитать"),
            KeyboardButton(text="Информация")
        ],
        [KeyboardButton(text="Купить")],
        [KeyboardButton(text="Регистрация")]

    ], resize_keyboard=True
)

kb_inl = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Рассчитать", callback_data="calories")],
        [InlineKeyboardButton(text="Формулы расчёта", callback_data="formulas")]
    ]
)

kb_gender = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="М"),
            KeyboardButton(text="Ж")
        ]
    ], resize_keyboard=True
)

kb_prod = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Product1", callback_data="product_buying"),
            InlineKeyboardButton(text="Product2", callback_data="product_buying"),
            InlineKeyboardButton(text="Product3", callback_data="product_buying"),
            InlineKeyboardButton(text="Product4", callback_data="product_buying")
        ]
    ]
)


class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()
    gender = State()


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = State()


@dp.message_handler(commands=['start'])
async def start(message):
    await message.answer(
        "Привет! Я бот помогающий твоему здоровью. "
        "Что бы посчитать суточную норму калорий нажмите - Рассчитать", reply_markup=kb
    )


@dp.message_handler(text="Рассчитать")
async def main_menu(message):
    await message.answer("Выберите опцию:", reply_markup=kb_inl)


@dp.callback_query_handler(text="formulas")
async def get_formulas(call):
    await call.message.answer(
        "Упрощенная формула Миффлина-Сан Жеора: "
        "\n-для мужчин: 10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5 "
        "\n-для женщин: 10 x вес (кг) + 6,25 x рост (см) – 5 x возраст (г) – 161"
    )
    await call.answer()


@dp.callback_query_handler(text='calories')
async def set_age(call):
    await call.message.answer('Введите свой возраст (полных лет):')
    await call.answer()
    await UserState.age.set()


@dp.message_handler(state=UserState.age)
async def set_growth(message, state):
    await state.update_data(age=message.text)
    await message.answer("Введите свой рост (см):")
    await UserState.growth.set()


@dp.message_handler(state=UserState.growth)
async def set_growth(message, state):
    await state.update_data(growth=message.text)
    await message.answer("Введите свой вес (кг):")
    await UserState.weight.set()


@dp.message_handler(state=UserState.weight)
async def send_calories(message, state):
    await state.update_data(weight=message.text)
    await message.answer(f'Введите свой пол (М или Ж):', reply_markup=kb_gender)
    await UserState.gender.set()


@dp.message_handler(state=UserState.gender)
async def send_calories(message, state):
    await state.update_data(gender=message.text)
    data = await state.get_data()
    if data["gender"] == "М":
        await message.answer(
            f'Ваша суточная норма калорий:'
            f'{int(data["weight"]) * 10 + int(data["growth"]) * 6.25 - int(data["age"]) * 5 + 5}(ккал)'
        )
    elif data["gender"] == "Ж":
        await message.answer(
            f'Ваша суточная норма калорий:'
            f'{int(data["weight"]) * 10 + int(data["growth"]) * 6.25 - int(data["age"]) * 5 - 161}(ккал)'
        )
    await state.finish()


@dp.message_handler(text="Купить")
async def get_buying_list(message):
    pictures = ["Витамин А.jpg", "Глютамин.jpg", "Омега-3.jpg", "Протеин.jpg"]
    products_list = get_all_products()
    count = 0

    for product in products_list:
        with open(pictures[count], "rb") as p:
            await message.answer_photo(
                p, f"Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}"
            )
        count += 1
    await message.answer("Выберите продукт для покупки:", reply_markup=kb_prod)


@dp.callback_query_handler(text="product_buying")
async def send_confirm_message(call):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()


@dp.message_handler(text="Регистрация")
async def sing_up(message):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.username)
async def set_username(message, state):
    if is_included(message.text) == False:
        await state.update_data(username=message.text)
        await message.answer("Введите свой email:")
        await RegistrationState.email.set()
    else:
        await message.answer("Пользователь существует, введите другое имя")
        await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.email)
async def set_email(message, state):
    await state.update_data(email=message.text)
    await message.answer("Введите свой возраст:")
    await RegistrationState.age.set()


@dp.message_handler(state=RegistrationState.age)
async def set_age(message, state):
    await state.update_data(age=message.text)
    data_u = await state.get_data()
    add_user(data_u["username"], data_u["email"], data_u["age"])
    await message.answer("Вы успешно зарегестрировались", reply_markup=kb)
    await state.finish()

@dp.message_handler()
async def all_messages(message):
    await message.answer("Введите команду /start, чтобы начать общение.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)