"""
Модуль для работы с базой данных MongoDB
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError, CollectionInvalid, DuplicateKeyError

from ..exceptions import DatabaseError


logger = logging.getLogger(__name__)


class Database:
    """
    Класс для работы с базой данных MongoDB
    """
    
    def __init__(self, uri: str = None):
        """
        Инициализирует подключение к базе данных
        
        Args:
            uri: URI для подключения к MongoDB
        """
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = None
        self.db = None
        self.users = None
        self.tariffs = None
        self.subscriptions = None
        self.payments = None
        self.support_tickets = None
        self.ticket_messages = None
        self.vpn_clusters = None  # Новая коллекция для кластеров VPN
        self.vpn_servers = None   # Новая коллекция для серверов VPN
        
        # Словарь для отслеживания следующих ID
        self._next_ids = {}
    
    async def connect(self) -> None:
        """
        Устанавливает соединение с базой данных
        
        Raises:
            DatabaseError: если не удалось подключиться к базе данных
        """
        try:
            # Создаем клиента MongoDB
            self.client = AsyncIOMotorClient(self.uri, serverSelectionTimeoutMS=5000)
            
            # Проверяем соединение
            await self.client.admin.command('ping')
            
            # Получаем базу данных 'vpn_bot'
            self.db = self.client.vpn_bot
            
            # Инициализируем коллекции
            self.users = self.db.users
            self.tariffs = self.db.tariffs
            self.subscriptions = self.db.subscriptions
            self.payments = self.db.payments
            self.support_tickets = self.db.support_tickets
            self.ticket_messages = self.db.ticket_messages
            self.vpn_clusters = self.db.vpn_clusters
            self.vpn_servers = self.db.vpn_servers
            
            # Создаем индексы для коллекций
            await self._init_indexes()
            
            # Инициализируем начальные данные, если необходимо
            await self._init_default_data()
            
            logger.info("Успешное подключение к базе данных MongoDB")
        
        except ServerSelectionTimeoutError as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            raise DatabaseError(f"Не удалось подключиться к MongoDB: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise DatabaseError(f"Ошибка инициализации базы данных: {e}")
    
    async def _init_indexes(self) -> None:
        """
        Инициализирует индексы для коллекций
        """
        try:
            # Индексы для пользователей
            await self.users.create_index("id", unique=True)
            await self.users.create_index("telegram_id", unique=True)
            await self.users.create_index("referral_code", unique=True)
            await self.users.create_index("referrer_id")
            
            # Индексы для тарифов
            await self.tariffs.create_index("id", unique=True)
            await self.tariffs.create_index("is_trial")
            
            # Индексы для подписок
            await self.subscriptions.create_index("id", unique=True)
            await self.subscriptions.create_index("user_id")
            await self.subscriptions.create_index([("user_id", 1), ("is_active", 1)])
            
            # Индексы для платежей
            await self.payments.create_index("id", unique=True)
            await self.payments.create_index("user_id")
            await self.payments.create_index("payment_id", unique=True)
            
            # Индексы для тикетов поддержки
            await self.support_tickets.create_index("id", unique=True)
            await self.support_tickets.create_index("user_id")
            await self.support_tickets.create_index("status")
            
            # Индексы для сообщений тикетов
            await self.ticket_messages.create_index("id", unique=True)
            await self.ticket_messages.create_index("ticket_id")
            
            # Индексы для кластеров VPN
            await self.vpn_clusters.create_index("id", unique=True)
            
            # Индексы для серверов VPN
            await self.vpn_servers.create_index("id", unique=True)
            await self.vpn_servers.create_index("cluster_id")
            
            logger.info("Индексы базы данных успешно созданы")
        
        except DuplicateKeyError:
            # Индексы уже существуют, игнорируем ошибку
            logger.info("Индексы базы данных уже существуют")
        
        except Exception as e:
            logger.error(f"Ошибка при создании индексов: {e}")
            # Не вызываем исключение, продолжаем работу
    
    async def get_next_id(self, collection_name: str) -> int:
        """
        Получает следующий доступный ID для коллекции
        
        Args:
            collection_name: Имя коллекции
            
        Returns:
            Следующий доступный ID
            
        Raises:
            DatabaseError: если не удалось получить следующий ID
        """
        try:
            # Получаем коллекцию по имени
            collection = getattr(self, collection_name, None)
            if not collection:
                collection = self.db[collection_name]
            
            # Ищем документ с наибольшим ID
            last_doc = await collection.find_one(
                sort=[("id", -1)],
                projection={"id": 1}
            )
            
            # Если документов нет, начинаем с 1
            if not last_doc:
                return 1
            
            # Иначе возвращаем следующий ID
            return last_doc["id"] + 1
        
        except Exception as e:
            logger.error(f"Ошибка при получении следующего ID для {collection_name}: {e}")
            raise DatabaseError(f"Не удалось получить следующий ID: {e}")
    
    async def _init_default_data(self) -> None:
        """
        Инициализирует базу данных начальными данными, если они отсутствуют
        """
        try:
            # Проверяем, есть ли тарифы
            tariffs_count = await self.tariffs.count_documents({})
            
            # Если тарифов нет, создаем базовые тарифы
            if tariffs_count == 0:
                logger.info("Создание базовых тарифов")
                
                # Базовые тарифы для примера
                default_tariffs = [
                    {
                        "id": 1,
                        "name": "Базовый",
                        "description": "Базовый тариф для одного устройства",
                        "price": 199,
                        "duration_days": 30,
                        "traffic_limit_mb": 0,  # Безлимитный трафик
                        "max_devices": 1,
                        "is_active": True,
                        "created_at": None,  # Будет заполнено автоматически
                        "updated_at": None   # Будет заполнено автоматически
                    },
                    {
                        "id": 2,
                        "name": "Стандарт",
                        "description": "Стандартный тариф для трех устройств",
                        "price": 499,
                        "duration_days": 30,
                        "traffic_limit_mb": 0,  # Безлимитный трафик
                        "max_devices": 3,
                        "is_active": True,
                        "created_at": None,
                        "updated_at": None
                    },
                    {
                        "id": 3,
                        "name": "Премиум",
                        "description": "Премиум тариф для пяти устройств с увеличенной скоростью",
                        "price": 999,
                        "duration_days": 30,
                        "traffic_limit_mb": 0,  # Безлимитный трафик
                        "max_devices": 5,
                        "is_active": True,
                        "created_at": None,
                        "updated_at": None
                    }
                ]
                
                # Добавляем тарифы в базу данных
                for tariff in default_tariffs:
                    # Проверяем, существует ли уже такой тариф
                    existing = await self.tariffs.find_one({"id": tariff["id"]})
                    if not existing:
                        await self.tariffs.insert_one(tariff)
            
            # Проверяем, есть ли кластеры VPN
            clusters_count = await self.vpn_clusters.count_documents({})
            
            # Если кластеров нет, создаем базовый кластер
            if clusters_count == 0:
                logger.info("Создание базового кластера VPN")
                
                # Базовый кластер для примера
                default_cluster = {
                    "id": 1,
                    "name": "Основной кластер",
                    "description": "Основной кластер VPN серверов",
                    "is_active": True,
                    "max_load": 1000,
                    "created_at": None,  # Будет заполнено автоматически
                    "updated_at": None   # Будет заполнено автоматически
                }
                
                # Добавляем кластер в базу данных
                await self.vpn_clusters.insert_one(default_cluster)
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации начальных данных: {e}")
            # Не вызываем исключение, продолжаем работу
    
    async def close(self) -> None:
        """
        Закрывает соединение с базой данных
        """
        if self.client:
            self.client.close()
            logger.info("Соединение с базой данных закрыто")


# Создаем экземпляр для использования в приложении
db = Database()


async def init_db() -> None:
    """
    Инициализирует соединение с базой данных
    """
    await db.connect() 