from telebot.types import Message
from main import bot
#from database.db_controller import save_user
from loguru import logger


@bot.message_handler(commands=['help'])
@logger.catch
def bot_start(message: Message) -> None:

    #save_user(message)
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, f" /start - запустить БОТ\n/help - список команд\n/low-дешевые отели\n/high-дорогие отели\n/bestdeal-диапазон значений\n/history — вывод истории последних 10 запросов", parse_mode="html")