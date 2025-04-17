import asyncio
import logging
from datetime import datetime
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.db_requests import get_all_trainings, deactive_training
from app.database.models import async_main

# Роутеры с командами
from app.handlers.info_update_handler import router as router1
from app.handlers.registration_handler import router as router2
from app.handlers.training_handler import router as router3
from app.handlers.static_handler import router as router4

from aiogram.client.default import DefaultBotProperties 

load_dotenv()
TOKEN = "7721057554:AAEDIiSfxeN3jzFPTe2MRY4hT0PrqCcmtXU"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Подключаем обработчики
dp.include_router(router1)
dp.include_router(router2)
dp.include_router(router3)
dp.include_router(router4)

# Уведомление о тренировках
async def notify_users():
    trainings = await get_all_trainings()
    for training in trainings:
        now = datetime.now()
        diff = now - training.time
        minutes_passed = diff.total_seconds() / 60
        if abs(minutes_passed) <= 30:
            await bot.send_message(
                chat_id=training.tg_id,
                text=f"⏰ Через 30 минут тренировка: {training.type}"
            )
            await deactive_training(training.id)

async def main():
    await async_main()

    # Добавляем команды
    await bot.set_my_commands([
        BotCommand(command='my_info', description='Информация о Вас'),
        BotCommand(command='set_aim', description='Установить цель тренировок'),
        BotCommand(command='set_age', description='Сменить возраст'),
        BotCommand(command='set_weight', description='Сменить вес'),
        BotCommand(command='set_height', description='Сменить рост'),
        BotCommand(command='set_plan', description='Добавить тренировку'),
        BotCommand(command='view_plan', description='Мои тренировки'),
        BotCommand(command='get_advice', description='Совет от тренера'),
        BotCommand(command='menu', description='Меню')
    ], scope=BotCommandScopeDefault())

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_users, CronTrigger(minute="*"))
    scheduler.start()

    # Стартуем обычный polling
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
