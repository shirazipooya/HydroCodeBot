import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from sqlmodel import SQLModel, Field, Session, create_engine

# Database setup
DATABASE_URL = "sqlite:///user_data.db"
engine = create_engine(DATABASE_URL)

# Define User model
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    phone: str
    city: str

# Create the database tables
SQLModel.metadata.create_all(engine)

# Bot setup
from dotenv import load_dotenv
import os
load_dotenv()
bot = telebot.TeleBot(os.getenv("WERIFUMBOT_API_TOKEN"))

# User state tracking
user_states = {}

# Start command handler
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Welcome! Let's collect your information.")
    request_name(message)

# Step 1: Request Name
def request_name(message):
    msg = bot.reply_to(message, "What is your name?")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    user_states[message.chat.id] = {"name": message.text}
    request_phone(message)

# Step 2: Request Phone Number
def request_phone(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("Send Phone Number", request_contact=True))
    msg = bot.reply_to(message, "Please share your phone number.", reply_markup=markup)
    bot.register_next_step_handler(msg, process_phone)

def process_phone(message):
    if message.contact:
        print(message.contact)
        phone = message.contact.phone_number
    else:
        phone = message.text
    user_states[message.chat.id]["phone"] = phone
    request_city(message)

# Step 3: Request City
def request_city(message):
    msg = bot.reply_to(message, "What city do you live in?")
    bot.register_next_step_handler(msg, process_city)

def process_city(message):
    user_states[message.chat.id]["city"] = message.text
    save_user_to_db(message.chat.id)
    bot.send_message(message.chat.id, "Thank you! Your information has been saved.")

# Save user data to the database
def save_user_to_db(chat_id):
    user_data = user_states[chat_id]
    with Session(engine) as session:
        user = User(
            name=user_data["name"],
            phone=user_data["phone"],
            city=user_data["city"],
        )
        session.add(user)
        session.commit()
    del user_states[chat_id]

# Run the bot
print("Bot is running...")
bot.polling()
