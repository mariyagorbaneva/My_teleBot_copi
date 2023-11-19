from telebot import types

from main import bot
from states.user_states import state
from handlers import survey_hendlers
from tg_API.util.api_reqiest import request_to_api


@bot.message_handler(commands=['high'])
def send_welcome(message: types.Message):
    bot.delete_state(message.from_user.id, message.chat.id)         #очищаем все состояния
    bot.set_state(message.from_user.id, state.cities, message.chat.id)
    bot.send_message(message.from_user.id, "Введите город для поиска отелей")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['last_command'] = 'high'
