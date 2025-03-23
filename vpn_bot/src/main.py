"""
Главный модуль бота - точка входа для запуска
"""
import asyncio
import logging
import os
from typing import List
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .middleware import AuthMiddleware
from .database import init_db
from .settings import Settings
from .handlers import router
from .exceptions import DatabaseError
from .models.tariff import Tariff


# Настройка логирования
def setup_logging():
    """Настраивает логирование приложения"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("bot.log")
        ]
    )
    # Отключаем логи от библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    return logger


async def initialize_default_data():
    """Инициализирует дефолтные данные в базе данных"""
    logger = logging.getLogger(__name__)
    
    # Проверяем и создаем пробный тариф, если его еще нет
    try:
        trial_tariff = await Tariff.get_trial_tariff()
        if not trial_tariff:
            trial_tariff = await Tariff.create_default_trial()
            logger.info(f"Создан пробный тариф: {trial_tariff.name}")
        else:
            logger.info(f"Пробный тариф уже существует: {trial_tariff.name}")
    except Exception as e:
        logger.error(f"Ошибка при создании пробного тарифа: {e}")


async def main():
    """Основная функция запуска бота"""
    logger = setup_logging()
    logger.info("Запуск бота...")
    
    # Загружаем настройки
    settings = Settings()
    logger.info(f"Загружены настройки для окружения: {settings.environment}")
    
    # Инициализируем базу данных
    try:
        await init_db()
        logger.info("База данных инициализирована")
        
        # Инициализируем дефолтные данные
        await initialize_default_data()
        logger.info("Дефолтные данные инициализированы")
    except DatabaseError as e:
        logger.critical(f"Ошибка инициализации базы данных: {e}")
        return
    
    # Создаем экземпляр бота
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Регистрируем все роутеры
    dp.include_router(router)
    
    # Удаляем вебхук перед запуском поллинга
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Вебхук удален, старт поллинга...")
    
    try:
        # Запускаем поллинг
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка при работе бота: {e}")
    finally:
        # Всегда закрываем соединение с базой данных
        from .database import db
        await db.close()
        logger.info("Соединение с базой данных закрыто")


if __name__ == "__main__":
    asyncio.run(main()) 