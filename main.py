import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config_data.conf import conf
from handlers import action_handlers, user_handlers

logger = structlog.get_logger()
bot: Bot = Bot(token=conf.tg_bot.token)

async def main():
    logger.info('Starting bot')

    # Создаем хранилище для FSM
    storage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)
    dp.include_router(action_handlers.router)
    dp.include_router(user_handlers.router)
    
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        admins = conf.tg_bot.admin_ids
        if admins:
            await bot.send_message(
                conf.tg_bot.admin_ids[0], f'Бот запущен.')
    except:
        logger.critical(f'Не могу отправить сообщение', exc_info=True)

    await dp.start_polling(bot, allowed_updates=["message", "my_chat_member", "chat_member", "callback_query"])


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')