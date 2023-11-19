from telebot.types import Message
from loader import bot

from states.user_states import state
from tg_API.util.get_hotels import process_hotels_info

from loguru import logger
from tg_API.util.adress import get_hotel_address
from tg_API.util.answer import show_info, count_amount_nights
from tg_API.util.api_reqiest import request_to_api



@bot.message_handler(commands=['bestdeal'])

def bot_best_deal(message: Message):
    """
    Функция, реагирующая на команду 'bestdeal'.
    Записывает состояние пользователя 'last_command' и предлагает ввести город для поиска отелей.

    :param message: Сообщение Telegram
    """

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, state.cities, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['last_command'] = 'bestdeal'