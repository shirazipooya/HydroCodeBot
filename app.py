import os
import json
import asyncio
from sqlmodel import SQLModel, create_engine, Session, select
from utils import jalali
from utils.assets import (
    CHINESE_SIGNS,
    CHINESE_ELEMENTS,
    PERSIAN_MONTHS,
    CHINESE_SIGNS_FARSI,
    CHINESE_ELEMENTS_FARSI,
    is_user_member,
    is_valid_date,
    user_channel_check,
    insert_to_kua_table,
    insert_to_zodiac_table,
    extract_chinese_year,
    calculate_kua_number,
    send_join_channel_button,
    decade_buttons,
    year_buttons,
    month_buttons,
    day_buttons,
    gender_buttons
)
from models import Kua, Zodiac
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    BotCommand,
)



# ------------------------------------------------------------------------------
# Initials
# ------------------------------------------------------------------------------

# Load Environment Variables
load_dotenv()

# Temporary Storage For User Input Data
user_kua_data = {}
user_zodiac_data = {}

# Your Channel Username
CHANNEL_USERNAME = ["weri_fum", "HydroCode"]
CHANNELS = ["weri_fum", "PopiTvSerise"]

# Maximum Visit
MAX_VISIT = 1


with open('utils/zodiac.json', 'r', encoding='utf-8') as file:
    zodiac_data = json.load(file)



# ------------------------------------------------------------------------------
# Create Bot
# ------------------------------------------------------------------------------

# Create Bot
bot = AsyncTeleBot(
    token=os.getenv("WERIFUMBOT_API_TOKEN")
)



# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------
DATABASE_NAME = 'database.db'
engine = create_engine(f"sqlite:///{DATABASE_NAME}")
SQLModel.metadata.create_all(engine)



# ------------------------------------------------------------------------------ #
#                           Handle /start Command
# ------------------------------------------------------------------------------ #

@bot.message_handler(commands=['start'])
async def start_command(message):    
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            "سلام عشق فرشته 💚😍\n\n"
            "خیلی خوشحالم که همراه آموزش‌ها بودی. قراره با استفاده از این ربات به صورت رایگان عدد کوا و زودیاک خودت و اعضای خانوادتو محاسبه کنم و بهت بگم.\n\n"
            "لیست دستورهای ما:\n\n"
            "تا خیالت از انرژی های ۲۰۲۵ راحت باشه!"
            "کافیه به ترتیب سال / ماه / روز تولدت و جنسیت رو انتخاب کنی!"
            "تا من بهت بگم عدد شانس و زودیاکت چی هست!"
            "بیا شروع کنیم:"
        ),
        parse_mode="HTML",
    )



# ------------------------------------------------------------------------------ #
#                              Handle /kua Command
# ------------------------------------------------------------------------------ #

@bot.message_handler(commands=['kua'])
async def kua_command(message):    
    user_id = message.from_user.id    
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                "اولین محاسبه‌گر دقیق عدد کوا با در نظر گرفتن تمامی استثنائات\n\n"
                "عدد کوا یا عدد کی یا عدد شانس، تنها یکی از عناصر وجودی ماست که در چیدمان محیط به ما کمک می‌کند. کوانامبر نمایانگر جهات خوب و بد نشستن، ایستادن، کار کردن و خوابیدن است که به نوبه خود، روشی مجزا در فنگ‌شویی، تحت عنوان روش فنگ شویی فردی است.\n\n"
                "برای محاسبه عدد کوا کافیست تارخ تولد و جنسیت خود را در ادامه وارد کنید.\n\n"
            ),
            parse_mode="HTML",
        )
        await decade_buttons(
            bot=bot,
            chat_id=message.chat.id,
            callback_prefix="kua_decade_"
        )
            
        

@bot.callback_query_handler(func=lambda call: call.data.startswith("kua_decade_"))
async def kua_command_handle_decade_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        selected_decade = call.data.split("_")[2]
        start_year = int(selected_decade)
        end_year = start_year + 9
        await year_buttons(
            bot=bot,
            chat_id=call.message.chat.id,
            start_year=start_year,
            end_year=end_year,
            callback_prefix="kua_year_"
        )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("kua_year_"))
async def kua_command_handle_year_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        birth_year = int(call.data.split("_")[2])
        user_kua_data[call.message.chat.id] = {"birth_year": birth_year }
        await month_buttons(
            bot=bot, 
            chat_id=call.message.chat.id,
            callback_prefix="kua_month_"
            )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("kua_month_"))
async def kua_command_handle_month_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        birth_month = int(call.data.split("_")[2])
        user_kua_data[call.message.chat.id]["birth_month"] = birth_month
        await day_buttons(
            bot=bot,
            chat_id=call.message.chat.id,
            callback_prefix="kua_day_"
        )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("kua_day_"))
async def kua_command_handle_day_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        birth_day = int(call.data.split("_")[2])
        user_kua_data[call.message.chat.id]["birth_day"] = birth_day
        await gender_buttons(
            bot=bot,
            chat_id=call.message.chat.id,
            callback_prefix="kua_gender_"
        )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("kua_gender_"))
async def kua_command_handle_gender_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Kua,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        chat_id = call.message.chat.id
        gender = call.data.split("_")[2]
        user_kua_data[chat_id]["gender"] = gender
        birth_year = user_kua_data[chat_id]["birth_year"]
        birth_month = user_kua_data[chat_id]["birth_month"]
        birth_day = user_kua_data[chat_id]["birth_day"]

        if not is_valid_date(int(birth_year), int(birth_month), int(birth_day)):
            await bot.send_message(
                chat_id=chat_id, 
                text="تاریخ وارد شده اشتباه است. لطفا تاریخ را به صورت صحیح وارد کن!",
            )
            await decade_buttons(
                    bot=bot,
                    chat_id=chat_id,
                    callback_prefix="kua_decade_"
                )
            return

        birth_year_g, birth_month_g, birth_day_g = jalali.Persian((int(birth_year), int(birth_month), int(birth_day))).gregorian_tuple()
        
        chinese_year = extract_chinese_year(
            date_string=f"{birth_year_g:04d}-{birth_month_g:02d}-{birth_day_g:02d}"
        )

        kua_number = calculate_kua_number(
            birth_year=chinese_year,
            gender=gender
        )

        await bot.send_message(
            chat_id=chat_id,
            text=f"📝 اطلاعات دریافت‌ شده:\n- تاریخ تولد: {birth_year}/{birth_month}/{birth_day}\n- جنسیت: {'مرد' if gender == 'male' else 'زن'}"
        )
        
        # Send Kua Number Result
        file_path = os.path.abspath(f"./data/img/kua_{kua_number}.png")
        if not os.path.exists(file_path):
            print("File not found:", file_path)
        else:
            print("File founded:", file_path)
        with open(file_path, "rb") as photo:
            print("File opened successfully", file_path)
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=f"عدد کوا شما «{kua_number}» می‌باشد!",
            )           
        

        with Session(engine) as session:
            statement = select(Kua).where(Kua.user_id == call.message.chat.id)
            user = session.exec(statement).first()
            if user:
                count_visit = user.count_visit + 1
            else:
                count_visit = 1
                
        
        insert_to_kua_table(
            engine=engine,
            user_id=call.message.chat.id,
            first_name=call.message.chat.first_name,
            last_name=call.message.chat.last_name,
            username=call.message.chat.username,
            gender=gender,
            birth_date=f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
            kua_number=kua_number,
            count_visit=count_visit
        )

        user_kua_data.pop(chat_id, None)
        await bot.answer_callback_query(callback_query_id=call.id)



# ------------------------------------------------------------------------------ #
#                              Handle /zodiac Command
# ------------------------------------------------------------------------------ #

@bot.message_handler(commands=['zodiac'])
async def zodiac_command(message):    
    user_id = message.from_user.id    
    if await user_channel_check(
        engine=engine,
        table=Zodiac,
        bot=bot,
        message=message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                "زودیاک چینی، یا شنگ شیائو (生肖)، یک چرخه 12 ساله تکرار شونده از نشانه های حیوانات و ویژگی های نسبت داده شده به آنها، بر اساس تقویم قمری است. به ترتیب، حیوانات زودیاک عبارتند از: موش، گاو، ببر، خرگوش، اژدها، مار، اسب، بز، میمون، خروس، سگ، خوک. سال نو قمری یا جشنواره بهار، انتقال از یک حیوان به حیوان دیگر را نشان می‌دهد.\n\n"
                "علامت زودیاک شما چیست؟ برای محاسبه علامت زودیاک کافیست تارخ تولد خود را در ادامه وارد کنید.\n\n"
            ),
            parse_mode="HTML",
        )
        await decade_buttons(
            bot=bot,
            chat_id=message.chat.id,
            callback_prefix="zodiac_decade_"
        )
        

@bot.callback_query_handler(func=lambda call: call.data.startswith("zodiac_decade_"))
async def zodiac_command_handle_decade_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Zodiac,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        selected_decade = call.data.split("_")[2]
        start_year = int(selected_decade)
        end_year = start_year + 9
        await year_buttons(
            bot=bot,
            chat_id=call.message.chat.id,
            start_year=start_year,
            end_year=end_year,
            callback_prefix="zodiac_year_"
        )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("zodiac_year_"))
async def zodiac_command_handle_year_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Zodiac,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        birth_year = int(call.data.split("_")[2])
        user_zodiac_data[call.message.chat.id] = {"birth_year": birth_year }
        await month_buttons(
            bot=bot, 
            chat_id=call.message.chat.id,
            callback_prefix="zodiac_month_"
            )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("zodiac_month_"))
async def zodiac_command_handle_month_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Zodiac,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        birth_month = int(call.data.split("_")[2])
        user_zodiac_data[call.message.chat.id]["birth_month"] = birth_month
        await day_buttons(
            bot=bot,
            chat_id=call.message.chat.id,
            callback_prefix="zodiac_day_"
        )
        await bot.answer_callback_query(callback_query_id=call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("zodiac_day_"))
async def zodiac_command_handle_day_selection(call):
    user_id = call.message.chat.id
    if await user_channel_check(
        engine=engine,
        table=Zodiac,
        bot=bot,
        message=call.message,
        user_id=user_id,
        max_visit=MAX_VISIT,
        channels=CHANNELS
    ):
        chat_id = call.message.chat.id
        birth_day = int(call.data.split("_")[2])
        user_zodiac_data[call.message.chat.id]["birth_day"] = birth_day

        birth_year = user_zodiac_data[chat_id]["birth_year"]
        birth_month = user_zodiac_data[chat_id]["birth_month"]
        birth_day = user_zodiac_data[chat_id]["birth_day"]

        if not is_valid_date(int(birth_year), int(birth_month), int(birth_day)):
            await bot.send_message(
                chat_id=chat_id, 
                text="تاریخ وارد شده اشتباه است. لطفا تاریخ را به صورت صحیح وارد کن!",
            )
            await decade_buttons(
                    bot=bot,
                    chat_id=chat_id,
                    callback_prefix="zodiac_decade_"
                )
            return

        birth_year_g, birth_month_g, birth_day_g = jalali.Persian((int(birth_year), int(birth_month), int(birth_day))).gregorian_tuple()
        
        chinese_year = extract_chinese_year(
            date_string=f"{birth_year_g:04d}-{birth_month_g:02d}-{birth_day_g:02d}"
        )


        await bot.send_message(
            chat_id=chat_id,
            text=f"📝 اطلاعات دریافت‌ شده:\n- تاریخ تولد: {birth_year}/{birth_month}/{birth_day}"
        )

        chinese_sign = CHINESE_SIGNS[int(chinese_year % 12)]
        chinese_element = CHINESE_ELEMENTS[int(chinese_year % 10) // 2]
        
        file_path = os.path.abspath(f"./data/img/zodiac_{chinese_sign}.png")
        if not os.path.exists(file_path):
            print("File not found:", file_path)
        else:
            print("File founded:", file_path)
        with open(file_path, "rb") as photo:
            print("File opened successfully", file_path)
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=f"زودیاک تولد شما «{CHINESE_SIGNS_FARSI[chinese_sign]}» می‌باشد!",
            )


        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"{zodiac_data[chinese_sign]["description"]}\n\n"
                # f"عددهای شانس شما: {zodiac_data[chinese_sign]["lucky_numbers"]}\n\n"
                # f"رنگ‌های شانس شما: {zodiac_data[chinese_sign]["lucky_colors"]}\n\n"
            )
        )        
        

        with Session(engine) as session:
            statement = select(Zodiac).where(Zodiac.user_id == call.message.chat.id)
            user = session.exec(statement).first()
            if user:
                count_visit = user.count_visit + 1
            else:
                count_visit = 1
                
        
        insert_to_zodiac_table(
            engine=engine,
            user_id=call.message.chat.id,
            first_name=call.message.chat.first_name,
            last_name=call.message.chat.last_name,
            username=call.message.chat.username,
            birth_date=f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
            chinese_sign=chinese_sign,
            chinese_element=chinese_element,
            count_visit=count_visit
        )

        user_zodiac_data.pop(chat_id, None)
        await bot.answer_callback_query(callback_query_id=call.id)



async def main():
    await bot.set_my_commands(
         commands=[
            BotCommand("start", "صفحه اصلی بات"),
            BotCommand("kua", "عدد شانس (کوا)"),
            BotCommand("zodiac", "محاسبه زودیاک تولد"),
            BotCommand("help", "راهنمایی و توضیحات در مورد دستورها"),
         ]
    )
    
    try:
        print("Bot is running ...")
        await bot.polling()
    except Exception as e:
        print(f"An error occurred: {e}")
        await asyncio.sleep(5)



if __name__ == "__main__":
    asyncio.run(main())
