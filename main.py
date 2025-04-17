from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

from app.database.db_requests import get_all_trainings, deactive_training
from app.database.models import async_main
from app.handlers.info_update_handler import router as router1
from app.handlers.registration_handler import router as router2
from app.handlers.training_handler import router as router3
from app.handlers.static_handler import router as router4



load_dotenv()

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # render.com domain, e.g., https://fitnesspo.onrender.com/webhook

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(router1)
dp.include_router(router2)
dp.include_router(router3)
dp.include_router(router4)

# Уведомления
async def notify_users():
    trainings = await get_all_trainings()
    for training in trainings:
        now = datetime.now()
        diff = now - training.time
        minutes = diff.total_seconds() / 60
        if abs(minutes) <= 30:
            await bot.send_message(training.tg_id, f"⏰ Через 30 минут тренировка: {training.type}")
            await deactive_training(training.id)

# Стартовые команды и cron
async def on_startup(app):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))
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
    ])
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_users, CronTrigger(minute="*"))
    scheduler.start()

# Запуск как aiohttp-приложение
async def main():
    await async_main()

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    app.on_startup.append(on_startup)
    setup_application(app, dp, bot=bot)
    return app

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    web.run_app(main(), port=int(os.getenv("PORT", 5000)))
