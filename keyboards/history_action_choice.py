from datetime import datetime
from typing import List
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import History
from keyboards.city import for_history


def print_histories(histories_list: List[History]) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками с историей поиска. Каждая кнопка: "дата запроса — тип запроса — город поиска".

    :param histories_list: список с историями поиска пользователя. Каждая история - объект класса History.
    :return: клавиатура InlineKeyboardMarkup.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    for history in histories_list:
        text = f'{datetime.fromtimestamp(history.date).strftime("%d.%m.%Y, %H:%M")} — ' \
               f'{history.command} — {history.city}'
        keyboard.add(InlineKeyboardButton(text=text, callback_data=for_history.new(history_id=history.id)))
    return keyboard
