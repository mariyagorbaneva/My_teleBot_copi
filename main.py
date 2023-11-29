from database.models import User, History, SearchResult
from loader import bot, db
from loguru import logger
from keyboards.filters import CityCallbackFilter, HistoryCallbackFilter
from telebot.custom_filters import StateFilter, IsDigitFilter
from tg_API.util.set_default_commands import set_default_commands



def run_bot() -> None:
    with db:
        db.create_tables([User, History, SearchResult])
    set_default_commands(bot)
    bot.add_custom_filter(StateFilter(bot))
    bot.add_custom_filter(IsDigitFilter())
    bot.add_custom_filter(CityCallbackFilter())
    bot.add_custom_filter(HistoryCallbackFilter())
    bot.infinity_polling()


if __name__ == '__main__':
    run_bot()
