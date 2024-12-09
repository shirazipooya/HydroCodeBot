import datetime
import lunardate
from sqlmodel import Session, select
from utils import jalali
from models import User, Kua, Zodiac
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)



PERSIAN_MONTHS = {
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

CHINESE_SIGNS = [
    'Monkey',
    'Rooster',
    'Dog', 
    'Pig', 
    'Rat', 
    'Ox',
    'Tiger',
    'Rabbit',
    'Dragon',
    'Snake',
    'Horse',
    'Goat',
]

CHINESE_SIGNS_FARSI = {
    'Monkey': 'میمون',
    'Rooster': 'خروس',
    'Dog': 'سگ',
    'Pig': 'خوک',
    'Rat': 'موش',
    'Ox': 'گاو',
    'Tiger': 'ببر',
    'Rabbit': 'خرگوش',
    'Dragon': 'اژدها',
    'Snake': 'مار',
    'Horse': 'اسب',
    'Goat': 'بز',
}

CHINESE_ELEMENTS = [
    "Metal", 
    "Water", 
    "Wood", 
    "Fire", 
    "Earth"
]

CHINESE_ELEMENTS_FARSI = {
    "Metal": "فلز",
    "Water": "آب",
    "Wood": "چوب",
    "Fire": "آتش",
    "Earth": "زمین",
}

def dashboard_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="عدد شانس (کوا)", callback_data="kua_button"),
        InlineKeyboardButton(text="زودیاک تولد", callback_data="zodiac_button")
    )
    markup.add(
        InlineKeyboardButton(text="راهنما", callback_data="help_button"),
        InlineKeyboardButton(text="شروع", callback_data="start_button"),
        # InlineKeyboardButton(text="ویرایش اطلاعات", callback_data="update_button")
    )
    return markup


async def is_user_member(bot, user_id, channels):
    remaining_channels = []
    try:
        for cid in channels:
            member = await bot.get_chat_member(
                chat_id=f"@{cid}",
                user_id=user_id
            )
            if member.status not in ['member', 'administrator', 'creator']:
                remaining_channels.append(cid)
    except Exception as e:
        print(f"Error Checking Membership: {e}")
    return len(remaining_channels) == 0, remaining_channels



async def send_join_channel_button(bot, chat_id, channels):
    markup = InlineKeyboardMarkup()
    for cu in channels:
        join_button = InlineKeyboardButton(
            text=f"عضویت در کانال\n{cu}@", 
            url=f"https://t.me/{cu.strip('@')}"  # Generates the URL for the channel
        )
        markup.add(join_button)
    
    confirm_button = InlineKeyboardButton(
        text="عضو شدم ✅", 
        callback_data="confirm_join"
    )
    markup.add(confirm_button)

    await bot.send_message(
        chat_id=chat_id,
        text="برای استفاده از همه امکانات نیاز است در کانال زیر عضو شوید:",
        reply_markup=markup
    )



async def user_channel_check(engine, table, bot, message, user_id, max_visit, channels):
    with Session(engine) as session:
        statement = select(table).where(table.user_id == user_id)
        user = session.exec(statement).first()
        is_member, rm_channels = await is_user_member(bot=bot, user_id=user_id, channels=channels)
        # if user and\
        #     user.count_visit >= max_visit and\
        #         not is_member:
        if not is_member:
            await send_join_channel_button(
                bot=bot,
                chat_id=message.chat.id,
                channels=rm_channels
            )
            return False
        return True



def create_inline_keyboard(options, columns=3, callback_prefix="option_"):
    """Generate inline keyboards with flexible column layout."""
    markup = InlineKeyboardMarkup()
    row = []
    for i, option in enumerate(options):
        row.append(
            InlineKeyboardButton(
                text=PERSIAN_MONTHS[option] if "month" in callback_prefix else str(option),
                callback_data=f"{callback_prefix}{option}")
            )
        if len(row) == columns or i == len(options) - 1:
            markup.add(*row)
            row = []
    return markup



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



def extract_chinese_year(
        date_string: str
    ) -> int:
    date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    lunar_date = lunardate.LunarDate.fromSolarDate(date.year, date.month, date.day)
    return int(lunar_date.year)



def calculate_kua_number(
    birth_year: int,
    gender: str
) -> int:
    
    year_sum = sum(map(int, str(birth_year)[-2:]))

    while year_sum > 9:
        year_sum = sum(map(int, str(year_sum)))
    
    kua_number = 0

    if gender.lower() == "male":
        kua_number = 10 - year_sum
        kua_number = 9 if kua_number == 0 else (2 if kua_number == 5 else kua_number)
    elif gender.lower() == "female":
        kua_number = year_sum + 5
        kua_number = sum(map(int, str(kua_number))) if kua_number > 9 else kua_number
        kua_number = 9 if kua_number == 0 else (8 if kua_number == 5 else kua_number)

    return kua_number



async def decade_buttons(bot, chat_id, callback_prefix="decade_"):
    decades = [f"{year}" for year in range(1320, 1420, 10)]
    markup = create_inline_keyboard(
        options=decades,
        columns=2,
        callback_prefix=callback_prefix
    )
    await bot.send_message(
        chat_id=chat_id,
        text="لطفاً دهه سال تولد خود را انتخاب کنید:",
        reply_markup=markup
    )



async def year_buttons(bot, chat_id, start_year, end_year, callback_prefix="year_"):
    years = range(start_year, end_year + 1)
    markup = create_inline_keyboard(
        options=years,
        columns=3,
        callback_prefix=callback_prefix
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً سال تولد خود را انتخاب کند:",
        reply_markup=markup
    )



async def month_buttons(bot, chat_id, callback_prefix="month_"):
    months = range(1, 13)
    markup = create_inline_keyboard(
        options=months,
        columns=3,
        callback_prefix=callback_prefix
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً ماه تولد خود را انتخاب کنید:", 
        reply_markup=markup
    )



async def day_buttons(bot, chat_id, callback_prefix="day_"):
    days = range(1, 32)
    markup = create_inline_keyboard(
        options=days,
        columns=3, 
        callback_prefix=callback_prefix
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً روز تولد خود را انتخاب کنید:",
        reply_markup=markup
    )



async def gender_buttons(bot, chat_id, callback_prefix="gender_"):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("مرد", callback_data=callback_prefix + "male"),
        InlineKeyboardButton("زن", callback_data=callback_prefix + "female")
    )
    await bot.send_message(
        chat_id=chat_id, 
        text="لطفاً جنسیت خود را انتخاب کنید:",
        reply_markup=markup
    )



def insert_to_kua_table(
    engine, user_id, gender, birth_date, kua_number, count_visit
):
    tmp = Kua(
        user_id=user_id,
        gender=gender,
        birth_date=birth_date,
        kua_number=kua_number,
        count_visit=count_visit
    )
    with Session(engine) as session:
        session.merge(tmp)
        session.commit()


def insert_to_zodiac_table(
    engine, user_id, birth_date, chinese_sign, chinese_element, count_visit
):
    tmp = Zodiac(
        user_id=user_id,
        birth_date=birth_date,
        chinese_sign=chinese_sign,
        chinese_element=chinese_element,
        count_visit=count_visit
    )
    with Session(engine) as session:
        session.merge(tmp)
        session.commit()


def insert_to_user_table(
    engine, user_id, username, phone_number, first_name, last_name, given_name, city
):
    tmp = User(
        user_id=user_id,
        username=username,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name,
        given_name=given_name,
        city=city,
    )
    with Session(engine) as session:
        session.merge(tmp)
        session.commit()