import os
import sqlite3
from datetime import datetime
from utils import jalali
import asyncio
import json
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    WebAppInfo,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton, 
    ReplyKeyboardRemove,
)

# ------------------------------------------------------------------------------
# Initials
# ------------------------------------------------------------------------------
# Temporary Storage For User Input Data
user_kua_data = {}

persian_months = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}

# WEB_APP_URL = "https://t.me/HydroCodeBot/SelectLandCoverType"
# WEB_APP_URL = "https://0270-46-254-106-22.ngrok-free.app"

# ------------------------------------------------------------------------------
# Create Bot
# ------------------------------------------------------------------------------
# Load All Environment Variables
load_dotenv()


# Create A Bot
bot = AsyncTeleBot(
    token=os.getenv("HYDROCODEBOT_API_TOKEN")
)


# Set Bot Commands
async def set_bot_commands():
    commands = [
        BotCommand("start", "صفحه اصلی بات"),
        BotCommand("kua", "محاسبه عدد کوا"),
        BotCommand("help", "راهنمایی و توضیحات در مورد دستورها"),
    ]
    await bot.set_my_commands(commands)


# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------
DATABASE_NAME = 'database.db'

# SQLite Database Initialization
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS kua (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            birth_date TEXT,
            kua_number TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Save User Info to Database
def set_info_to_kua(
    user_id, first_name, last_name, gender, birth_date, kua_number
):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute(
        '''
            INSERT OR REPLACE INTO kua (user_id, first_name, last_name, gender, birth_date, kua_number)
            VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (user_id, first_name, last_name, gender, birth_date, kua_number)
    )
    conn.commit()
    conn.close()


# Get User Info From Database
def get_info_from_kua(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM kua WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user


# ------------------------------------------------------------------------------
# Kua Number Calculate
# ------------------------------------------------------------------------------
# Function To Calculate The Kua Number
def calculate_kua_number(
    birth_year: int,
    gender: str
) -> int:
    year_sum = sum(int(digit) for digit in str(birth_year)[-2:])
    while year_sum > 9:
        year_sum = sum(int(digit) for digit in str(year_sum))
    
    if gender.lower() == "male":
        kua_number = 10 - year_sum
    elif gender.lower() == "female":
        kua_number = year_sum + 5
        if kua_number > 9:
            kua_number = sum(int(digit) for digit in str(kua_number))
    else:
        return -1

    return kua_number


# ------------------------------------------------------------------------------
# Convert And Check Date
# ------------------------------------------------------------------------------
# Function To Check If A Date Is Valid
def is_valid_date(
    year: int,
    month: int,
    day: int
) -> bool:
    try:
        jalali.Persian((year, month, day)).gregorian_tuple()
        # datetime(year, month, day)
        return True
    except ValueError:
        return False


# Function To Adjust Year Based On Chinese Solar Calendar
def adjust_year(
    birth_year: int,
    birth_month: int,
    birth_day: int
) -> int:
    if birth_month < 2 or (birth_month == 2 and birth_day < 4):
        return birth_year - 1
    return birth_year


# Handle /start Command
@bot.message_handler(commands=['start'])
async def send_welcome(message):    
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            "سلام رفیق! به بات ما خوش اومدی! 🎉\n\n"
            "خیلی خوشحالیم که به جمع ما پیوستی! اینجا می‌تونی کارهای خیلی جالبی انجام بدی. لیست دستورهای ما رو ببین و هرکدوم رو که دوست داشتی انتخاب کن یا از منو استفاده کن.\n\n"
            "لیست دستورهای ما:\n\n"
            "<b>\u200F /start:</b> صفحه اصلی بات\n\n"
            "<b>\u200F /kua :</b> محاسبه عدد کوا\n\n"
            "<b>\u200F /help :</b> راهنمایی و توضیحات در مورد دستورها\n\n"
        ),
        parse_mode="HTML",
    )


# Handle /kua_number Command
@bot.message_handler(commands=['kua'])
async def start_kua_calculation(message):
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            "اولین محاسبه‌گر دقیق عدد کوا با در نظر گرفتن تمامی استثنائات\n\n"
            "عدد کوا یا عدد کی یا عدد شانس، تنها یکی از عناصر وجودی ماست که در چیدمان محیط به ما کمک می‌کند. کوانامبر نمایانگر جهات خوب و بد نشستن، ایستادن، کار کردن و خوابیدن است که به نوبه خود، روشی مجزا در فنگ‌شویی، تحت عنوان روش فنگ شویی فردی است.\n\n"
            "برای محاسبه عدد کوا کافیست تارخ تولد و جنسیت خود را در ادامه وارد کنید.\n\n"
        ),
        parse_mode="HTML",
    )
    await send_decade_buttons(message.chat.id)


# ------------------------------------------------------------------------------
# /kua_number Functions
# ------------------------------------------------------------------------------
# Send Decade Selection Buttons
async def send_decade_buttons(chat_id):
    decades = [
        "1320",
        "1330",
        "1340",
        "1350",
        "1360",
        "1370",
        "1380",
        "1390",
        "1400",
        "1410",
    ]
    markup = InlineKeyboardMarkup()
    for decade in decades:
        markup.add(
            InlineKeyboardButton(
                text=f"دهه {decade} خورشیدی",
                callback_data=f"decade_{decade}"
            )
        )
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "بیا شروع کنیم.\n\n"
            "لطفاً دهه تولد خود را به شمسی انتخاب کن:\n\n"
        ),
        parse_mode="HTML",
        reply_markup=markup
    )


# Handle Decade Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("decade_"))
async def handle_decade_selection(call):
    selected_decade = call.data.split("_")[1]
    start_year = int(selected_decade)
    end_year = start_year + 9
    await send_year_buttons(
        chat_id=call.message.chat.id,
        years=range(start_year, end_year + 1)
    )
    await bot.answer_callback_query(callback_query_id=call.id)


# Create Inline Keyboard With n-column Layout
def create_inline_keyboard(
    options,
    columns=3,
    callback_prefix="option_"
):
    markup = InlineKeyboardMarkup()
    row = []
    for i, option in enumerate(options):
        row.append(
            InlineKeyboardButton(
                text=str(option) if callback_prefix != "month_" else persian_months[option],
                callback_data=f"{callback_prefix}{option}")
            )
        if len(row) == columns or i == len(options) - 1:
            markup.add(*row)
            row = []
    return markup


# Send Year Selection Buttons
async def send_year_buttons(chat_id, years):
    markup = create_inline_keyboard(
        years,
        columns=3,
        callback_prefix="year_"
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً سال تولد خود را انتخاب کن:\n\n",
        reply_markup=markup
    )
    

# Handle Year Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("year_"))
async def handle_year_selection(call):
    birth_year = int(call.data.split("_")[1])
    user_kua_data[call.message.chat.id] = {"birth_year": birth_year }
    await send_month_buttons(chat_id=call.message.chat.id)
    await bot.answer_callback_query(callback_query_id=call.id)


# Send Month Selection Buttons
async def send_month_buttons(chat_id):
    months = range(1, 13)
    markup = create_inline_keyboard(
        options=months,
        columns=3,
        callback_prefix="month_"
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً ماه تولد خود را انتخاب کن:\n\n", 
        reply_markup=markup
    )
    

# Handle Month Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("month_"))
async def handle_month_selection(call):
    birth_month = int(call.data.split("_")[1])
    user_kua_data[call.message.chat.id]["birth_month"] = birth_month
    await send_day_buttons(chat_id=call.message.chat.id)
    await bot.answer_callback_query(callback_query_id=call.id)


# Send Day Selection Buttons
async def send_day_buttons(chat_id):
    days = range(1, 32)
    markup = create_inline_keyboard(
        options=days,
        columns=3, 
        callback_prefix="day_"
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً روز تولد خود را انتخاب کن:\n\n",
        reply_markup=markup
    )


# Handle Day Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
async def handle_day_selection(call):
    birth_day = int(call.data.split("_")[1])
    user_kua_data[call.message.chat.id]["birth_day"] = birth_day
    await send_gender_buttons(chat_id=call.message.chat.id)
    await bot.answer_callback_query(callback_query_id=call.id)


# Send Gender Selection Buttons
async def send_gender_buttons(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("مرد", callback_data="gender_male"),
        InlineKeyboardButton("زن", callback_data="gender_female")
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً جنسیت خود را انتخاب کن:\n\n",
        reply_markup=markup
    )



# Handle Gender Selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
async def handle_gender_selection(call):
    chat_id = call.message.chat.id
    gender = call.data.split("_")[1]
    user_kua_data[chat_id]["gender"] = gender
    birth_year = user_kua_data[chat_id]["birth_year"]
    birth_month = user_kua_data[chat_id]["birth_month"]
    birth_day = user_kua_data[chat_id]["birth_day"]

    # Validate The Date
    if not is_valid_date(int(birth_year), int(birth_month), int(birth_day)):
        await bot.send_message(
            chat_id=chat_id, 
            text="تاریخ وارد شده اشتباه است. لطفا تاریخ را به صورت صحیح وارد کن!",
        )
        await send_decade_buttons(chat_id)
        return

    # Convert
    birth_year_g, birth_month_g, birth_day_g = jalali.Persian((int(birth_year), int(birth_month), int(birth_day))).gregorian_tuple()
    
    # Adjust the year and calculate the Kua number
    adjusted_year = adjust_year(birth_year_g, birth_month_g, birth_day_g)
    kua_number = calculate_kua_number(adjusted_year, gender)

    await bot.send_message(
        chat_id=chat_id,
        text=f"📝 اطلاعات دریافت‌ شده:\n- تاریخ تولد: {birth_year}/{birth_month}/{birth_day}\n- جنسیت: {'مرد' if gender == 'male' else 'زن'}"
    )
    
    # Send Kua Number Result
    await bot.send_photo(
        chat_id=chat_id,
        photo=open(f"data\img\kua_{kua_number}.png", "rb"),
        caption=f"عدد کوا شما {kua_number} می‌باشد!",
        parse_mode="HTML"
    )
    

    # Save Information To Database
    set_info_to_kua(
        user_id=call.message.chat.id,
        first_name=call.message.chat.first_name,
        last_name=call.message.chat.last_name,
        gender=gender,
        birth_date=f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
        kua_number=kua_number
    )


    # Clear user data after calculation
    user_kua_data.pop(chat_id, None)
    await bot.answer_callback_query(callback_query_id=call.id)


# Main entry point
async def main():
    init_db()
    await set_bot_commands()
    await bot.infinity_polling(
        restart_on_change=True
    )
    print("Bot is running...")

if __name__ == "__main__":
    asyncio.run(main())
