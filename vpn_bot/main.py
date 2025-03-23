"""
VPN Bot - Telegram бот для покупки и управления VPN подписками.
"""
import os
import logging
import asyncio
import sys
from pathlib import Path

# Добавляем директорию проекта в sys.path для корректного импорта
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "bot.log"))
    ]
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        from src.main import main
        
        # Запускаем бот
        logger.info("Starting VPN Bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot was stopped manually")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True) 