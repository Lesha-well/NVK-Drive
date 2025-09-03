import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from database import init_db
from handlers import router
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

async def set_bot_commands(bot: Bot):
    """Регистрация команд бота в Telegram."""
    commands = [
        BotCommand(command="/start", description="Начать работу с ботом"),
        BotCommand(command="/profile", description="Просмотреть или отредактировать анкету"),
        BotCommand(command="/search", description="Просмотреть анкеты других пользователей"),
        BotCommand(command="/find", description="Найти пользователей по навыкам"),
        BotCommand(command="/delete_profile", description="Удалить свою анкету"),
        BotCommand(command="/menu", description="Показать меню команд"),
        BotCommand(command="/help", description="Показать эту справку")
    ]
    await bot.set_my_commands(commands)

async def main():
    """Запуск бота."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Инициализация базы данных
    init_db()

    # Регистрация команд
    await set_bot_commands(bot)

    # Запуск бота в режиме polling
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())