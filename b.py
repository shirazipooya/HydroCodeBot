from telebot import TeleBot, types
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Initialize bot with your token
from dotenv import load_dotenv
import os
load_dotenv()
bot = TeleBot(os.getenv("HydroCodeBot_API_Token"))

def set_bot_description():
    description = (
        "🤖 Welcome to the Kua & Zodiac Info Bot! 🎉\n\n"
        "📌 Features:\n"
        "  - Discover your Kua Number and its significance.\n"
        "  - Explore Zodiac Signs and insights.\n"
        "  - Update your personal information for tailored experiences.\n\n"
        "💡 Start interacting by typing /start."
    )
    bot.set_my_description(description)

# Database model
class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int
    name: str
    phone_number: str
    city: str

# Create database engine and tables
DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # Check if the user already exists
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        existing_user = session.exec(statement).first()

    if existing_user:
        # Greet the existing user and show inline buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Kua Info", callback_data="kua_info"),
            types.InlineKeyboardButton("Zodiac Info", callback_data="zodiac_info")
        )
        markup.add(
            types.InlineKeyboardButton("Help", callback_data="help"),
            types.InlineKeyboardButton("Update Info", callback_data="update_info")
        )
        bot.send_message(
            message.chat.id,
            f"Welcome back, {existing_user.name}! Here are some options you can choose:",
            reply_markup=markup
        )
    else:
        # Prompt for phone number if user doesn't exist
        phone_button = types.KeyboardButton(
            text="Share Phone Number", request_contact=True)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # one_time_keyboard=True hides the button after it's clicked
        keyboard.add(phone_button)
        bot.send_message(
            message.chat.id,
            "Hello! Please share your phone number to proceed.",
            reply_markup=keyboard,
        )

# Handle contact sharing
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number

    bot.send_message(
        message.chat.id,
        f"Thank you! Please enter your name:",
        reply_markup=types.ReplyKeyboardRemove()  # Removes the keyboard
    )
    bot.register_next_step_handler(message, get_name, user_id, phone_number)

def get_name(message, user_id, phone_number):
    name = message.text
    bot.send_message(
        message.chat.id,
        "Great! Now, please enter your city:",
    )
    bot.register_next_step_handler(message, get_city, user_id, phone_number, name)

def get_city(message, user_id, phone_number, name):
    city = message.text

    # Store data in the database
    user = User(user_id=user_id, name=name, phone_number=phone_number, city=city)
    with Session(engine) as session:
        session.add(user)
        session.commit()

    # Show options after saving user data
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Kua Info", callback_data="kua_info"),
        types.InlineKeyboardButton("Zodiac Info", callback_data="zodiac_info")
    )
    markup.add(
        types.InlineKeyboardButton("Help", callback_data="help"),
        types.InlineKeyboardButton("Update Info", callback_data="update_info")
    )
    bot.send_message(
        message.chat.id,
        f"Thank you, {name} from {city}! Your information has been saved. Here are some options:",
        reply_markup=markup
    )


# Handle inline button callbacks
@bot.callback_query_handler(func=lambda call: call.data in ["kua_info", "zodiac_info", "help", "update_info"])
def handle_inline_buttons(call):
    if call.data == "kua_info":
        # Simulate /kua command
        kua(call.message)
    elif call.data == "zodiac_info":
        bot.send_message(call.message.chat.id, "This is the Zodiac Info section.")
    elif call.data == "help":
        bot.send_message(
            call.message.chat.id,
            "Here are some options:\n- Kua Info: Learn about Kua.\n- Zodiac Info: Learn about Zodiac signs.\n- Update Info: Update your personal details."
        )
    elif call.data == "update_info":
        bot.send_message(
            call.message.chat.id,
            "Let's update your information. Please enter your new name:"
        )
        bot.register_next_step_handler(call.message, update_name)

# Handle /kua command
@bot.message_handler(commands=['kua'])
def kua(message):
    bot.send_message(message.chat.id, "This is the Kua Info section.")

# Handle updating name
def update_name(message):
    new_name = message.text
    user_id = message.from_user.id

    # Store the updated name in the database
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        user = session.exec(statement).first()
        if user:
            user.name = new_name
            session.add(user)
            session.commit()
            bot.send_message(message.chat.id, "Name updated! Now, please enter your new city:")
            bot.register_next_step_handler(message, update_city)
        else:
            bot.send_message(message.chat.id, "We couldn't find your information. Please use /start to register.")

# Handle updating city
def update_city(message):
    new_city = message.text
    user_id = message.from_user.id

    # Store the updated city in the database
    with Session(engine) as session:
        statement = select(User).where(User.user_id == user_id)
        user = session.exec(statement).first()
        if user:
            user.city = new_city
            session.add(user)
            session.commit()
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Kua Info", callback_data="kua_info"),
                types.InlineKeyboardButton("Zodiac Info", callback_data="zodiac_info")
            )
            markup.add(
                types.InlineKeyboardButton("Help", callback_data="help"),
                types.InlineKeyboardButton("Update Info", callback_data="update_info")
            )
            bot.send_message(
                message.chat.id,
                f"Your information has been updated! Name: {user.name}, City: {user.city}",
                reply_markup=markup
            )
        else:
            bot.send_message(message.chat.id, "We couldn't find your information. Please use /start to register.")

# Polling
if __name__ == "__main__":
    set_bot_description()
    bot.infinity_polling()
