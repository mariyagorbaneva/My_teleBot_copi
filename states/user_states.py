from telebot.handler_backends import State, StatesGroup


class state(StatesGroup):
    city = State()
    count_hotel = State()
    choose_data = State()
    last_command = State()
    start_price = State()