from telebot.handler_backends import State, StatesGroup


class state(StatesGroup):
    amount_hotels = State()
    choose_data = State()
    last_command = State()
    start_price = State()
    end_price = State()
    end_distance = State()
    bestdeal = State()
    cities = State()
    amount_photo = State()