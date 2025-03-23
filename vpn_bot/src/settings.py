"""
Настройки приложения
"""
import os
from typing import List, Optional
from dotenv import load_dotenv


# Загружаем переменные окружения из .env файла
load_dotenv()


class Settings:
    """
    Настройки приложения, загружаемые из переменных окружения
    """
    
    def __init__(self):
        """Инициализация настроек из переменных окружения"""
        # Общие настройки
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Настройки бота
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is not set")
            
        # Преобразуем строку с ID администраторов в список целых чисел
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(",") if admin_id.strip()]
        
        # Настройки базы данных
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "vpn_bot")
        
        # Настройки платежной системы ЮKassa
        self.yokassa_account_id = os.getenv("YOKASSA_ACCOUNT_ID")
        self.yokassa_secret_key = os.getenv("YOKASSA_SECRET_KEY")
        
        # Настройки API для управления VPN серверами
        self.xui_api_url = os.getenv("XUI_API_URL")
        self.xui_api_username = os.getenv("XUI_API_USERNAME")
        self.xui_api_password = os.getenv("XUI_API_PASSWORD")
        
        # URL для возврата после оплаты (необходимо для некоторых платежных систем)
        self.payment_return_url = os.getenv("PAYMENT_RETURN_URL", "https://t.me/your_bot_username")
        
        # Настройки webhook (если используется)
        self.use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"
        self.webhook_url = os.getenv("WEBHOOK_URL")
        self.webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        self.webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
        self.webhook_port = int(os.getenv("WEBHOOK_PORT", "8443"))
        
        # Настройки логирования
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "bot.log")
    
    @property
    def is_production(self) -> bool:
        """Проверяет, запущено ли приложение в продакшн-режиме"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Проверяет, запущено ли приложение в режиме разработки"""
        return self.environment.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Проверяет, запущено ли приложение в тестовом режиме"""
        return self.environment.lower() == "testing"


# Создаем экземпляр настроек для использования в приложении
settings = Settings() 