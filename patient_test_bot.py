from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3

TOKEN = '8085146448:AAGoLZ6qumO9w96xAiHQYI2V5bnJoDfKq-g'

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_PATH = r'C:\Users\stasb\OneDrive\patient_answers.db'

class Form(StatesGroup):
    age = State()
    gender = State()
    penetrative_sex = State()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Включаем поддержку внешних ключей
    cursor.execute('PRAGMA foreign_keys = ON')

    # Создаем таблицу Users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        age INTEGER,
        gender TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу Questions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Questions (
        question_id INTEGER PRIMARY KEY,
        question_text TEXT
    )
    ''')

    # Создаем таблицу Answers с внешними ключами
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Answers (
        user_id INTEGER,
        question_id INTEGER,
        answer TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(id),
        FOREIGN KEY (question_id) REFERENCES Questions(question_id)
    )
    ''')

    # Проверяем, пуста ли таблица Questions
    cursor.execute('SELECT COUNT(*) FROM Questions')
    if cursor.fetchone()[0] == 0:
        # Заполняем таблицу вопросами
        questions = [
            (1, "Практикуете ли вы проникающие виды секса как активный партнёр (вагинальный, анальный)?"),
            (2, "Практикуете ли вы анальный секс как пассивный (принимающий) партнёр?"),
            (3, "Практикуете ли вы оральный вид секса как принимающий партнёр?"),
            (4, "Практикуете ли вы оральные виды секса как активный партнёр (делающий)?"),
            (5, "Практикуете ли вы анилингус в активной роли (делающей)?"),
            (6, "Практикуете ли вы анилингус в пассивной роли (принимающей)?")
        ]
        cursor.executemany('INSERT INTO Questions (question_id, question_text) VALUES (?, ?)', questions)

    conn.commit()
    conn.close()

def save_answer(age, gender):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу Users, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        age INTEGER,
        gender TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('INSERT INTO Users (age, gender) VALUES (?, ?)',
                   (age, gender))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Form.age)
    await message.answer("Сколько вам лет?")

@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await state.set_state(Form.gender)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Мужской", callback_data="gender_м"),
             InlineKeyboardButton(text="Женский", callback_data="gender_ж")]
        ])

        await message.answer("Укажите ваш биологический пол:", reply_markup=keyboard)
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@dp.callback_query(Form.gender)
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split('_')[1]
    await state.update_data(gender=gender)
    await state.set_state(Form.penetrative_sex)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="penetrative_да"),
         InlineKeyboardButton(text="Нет", callback_data="penetrative_нет")]
    ])

    await callback.message.answer("Практикуете ли вы проникающие виды секса как активный партнёр (вагинальный, анальный)?", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(Form.penetrative_sex)
async def process_penetrative_sex(callback: types.CallbackQuery, state: FSMContext):
    penetrative_sex = callback.data.split('_')[1]
    await state.update_data(penetrative_sex=penetrative_sex)
    data = await state.get_data()

    new_id = save_answer(data['age'], data['gender'])

    await callback.message.answer(f"Спасибо за ответы! Ваш номер в базе данных: {new_id}. "
                                  f"Вам {data['age']} лет, ваш пол: {'мужской' if data['gender'] == 'м' else 'женский'}, "
                                  f"{'практикуете' if penetrative_sex == 'да' else 'не практикуете'} проникающие виды секса.")
    await callback.answer()
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())