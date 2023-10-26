from telebot.types import Message

from main import bot
from states.user_states import state

from handlers import survey_hendlers



@bot.message_handler(commands=['bestdeal'])

def bot_best_deal(message: Message):
    """
    Функция, реагирующая на команду 'bestdeal'.
    Записывает состояние пользователя 'last_command' и предлагает ввести город для поиска отелей.

    :param message: Сообщение Telegram
    """

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, state.city, message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['last_command'] = 'bestdeal'