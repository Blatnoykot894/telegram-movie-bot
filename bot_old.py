import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import datetime as d

TOKEN = ""
dp = Dispatcher()

reply_k = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Say something funny"), KeyboardButton(text="What time is it now?")]
    ],
    resize_keyboard=True
)

inline_k = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Cool", callback_data="btn_cool"),
         InlineKeyboardButton(text="Boring", callback_data="btn_bor")]
    ]
)

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Hello! Please select a button:", reply_markup=reply_k)

@dp.message(Command("How_are_you"))
async def how_you_handler(message: Message):
    await message.answer("I am fine, thanks!")

@dp.message(Command("test"))
async def test_cmd2(message: Message):
    await message.answer("What do you prefer?", reply_markup=inline_k)

@dp.message(lambda message: message.text == "Say something funny")
async def send_joke(message: Message):
    await message.answer("kolobok povesilsa!")

@dp.message(lambda message: message.text == "What time is it now?")
async def send_time(message: Message):
    await message.answer(str(d.datetime.now().day))

@dp.callback_query(lambda call: call.data == "btn_cool")
async def press_cool(call: CallbackQuery):
    await call.message.answer("Cool!")
    await call.answer()

@dp.callback_query(lambda call: call.data == "btn_bor")
async def press_boring(call: CallbackQuery):
    await call.message.answer("Boring...")
    await call.answer()

@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    main_menu_commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="test", description="Show Inline buttons"),
        BotCommand(command="how_are_you", description="Ask how I am")
    ]
    await bot.set_my_commands(main_menu_commands)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
