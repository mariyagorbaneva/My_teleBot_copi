import json
from datetime import date, timedelta
from typing import Union, Dict

from telebot import types

from main import bot
from states.user_states import state
from tg_API.util import get_hotels, get_cities


@bot.message_handler(commands=['low'])
def send_welcome(message: types.Message):
    bot.send_message(message.from_user.id, "Введите город для поиска отелей")
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, state.cities, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['last_command'] = 'low'

