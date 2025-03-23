"""
Модуль для работы с тестовой базой данных SQLite
"""
import os
import logging
import aiosqlite
import json
from typing import Dict, Any, List, Optional, Tuple, Union

from ..exceptions import DatabaseError


logger = logging.getLogger(__name__)


class SQLiteDatabase:
    """
    Класс для работы с базой данных SQLite для тестирования
    """
    
    def __init__(self, db_path: str = None):
        """
        Инициализирует подключение к базе данных
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", "vpn_bot_test.db")
        self.conn = None
        
        # Словарь для отслеживания следующих ID
        self._next_ids = {}
    
    async def connect(self) -> None:
        """
        Устанавливает соединение с базой данных
        
        Raises:
            DatabaseError: если не удалось подключиться к базе данных
        """
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            # Включаем поддержку внешних ключей
            await self.conn.execute("PRAGMA foreign_keys = ON")
            # Инициализируем таблицы
            await self._init_tables()
            logger.info(f"Подключение к SQLite базе данных установлено: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise DatabaseError(f"Не удалось подключиться к базе данных: {e}")
    
    async def _init_tables(self) -> None:
        """
        Инициализирует таблицы в базе данных
        """
        try:
            # Создаем таблицу пользователей
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0.0,
                    is_admin INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    referral_code TEXT UNIQUE,
                    referral_bonus INTEGER DEFAULT 0,
                    registration_date TEXT
                )
            """)
            
            # Создаем таблицу тарифов
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tariffs (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    duration INTEGER NOT NULL,
                    traffic_limit INTEGER,
                    is_trial INTEGER DEFAULT 0,
                    max_connections INTEGER DEFAULT 1,
                    features TEXT
                )
            """)
            
            # Создаем таблицу подписок
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    tariff_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    server_id INTEGER,
                    cluster_id INTEGER,
                    vpn_uuid TEXT,
                    traffic_used INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (tariff_id) REFERENCES tariffs (id)
                )
            """)
            
            # Создаем таблицу платежей
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    payment_id TEXT UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    tariff_id INTEGER,
                    description TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (tariff_id) REFERENCES tariffs (id)
                )
            """)
            
            # Создаем таблицу тикетов поддержки
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Создаем таблицу сообщений тикетов
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY,
                    ticket_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    is_from_admin INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Создаем таблицу кластеров VPN
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS vpn_clusters (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    location TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Создаем таблицу серверов VPN
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS vpn_servers (
                    id INTEGER PRIMARY KEY,
                    cluster_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    load REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    max_users INTEGER DEFAULT 100,
                    current_users INTEGER DEFAULT 0,
                    FOREIGN KEY (cluster_id) REFERENCES vpn_clusters (id)
                )
            """)
            
            await self.conn.commit()
            logger.info("Таблицы базы данных инициализированы")
            
            # Инициализируем дефолтные данные
            await self._init_default_data()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации таблиц базы данных: {e}")
            raise DatabaseError(f"Не удалось инициализировать таблицы: {e}")
    
    async def _init_default_data(self) -> None:
        """
        Инициализирует дефолтные данные в базе данных
        """
        try:
            # Проверяем наличие тарифов
            async with self.conn.execute("SELECT COUNT(*) FROM tariffs") as cursor:
                result = await cursor.fetchone()
                if result and result[0] == 0:
                    # Добавляем дефолтный пробный тариф
                    await self.conn.execute("""
                        INSERT INTO tariffs (name, description, price, duration, traffic_limit, is_trial, max_connections, features)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "Пробный", 
                        "Пробный тариф на 3 дня", 
                        0.0, 
                        3, 
                        5368709120,  # 5 GB в байтах
                        1,
                        1,
                        json.dumps({"speed_limit": 10, "priority_support": False})
                    ))
                    
                    # Добавляем дефолтные тарифы
                    await self.conn.execute("""
                        INSERT INTO tariffs (name, description, price, duration, traffic_limit, is_trial, max_connections, features)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "Базовый", 
                        "Базовый тариф на 30 дней", 
                        299.0, 
                        30, 
                        32212254720,  # 30 GB в байтах
                        0,
                        2,
                        json.dumps({"speed_limit": 50, "priority_support": False})
                    ))
                    
                    await self.conn.execute("""
                        INSERT INTO tariffs (name, description, price, duration, traffic_limit, is_trial, max_connections, features)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "Премиум", 
                        "Премиум тариф на 30 дней", 
                        599.0, 
                        30, 
                        107374182400,  # 100 GB в байтах
                        0,
                        5,
                        json.dumps({"speed_limit": 100, "priority_support": True})
                    ))
                    
                    await self.conn.commit()
                    logger.info("Дефолтные тарифы добавлены в базу данных")
            
            # Проверяем наличие кластеров
            async with self.conn.execute("SELECT COUNT(*) FROM vpn_clusters") as cursor:
                result = await cursor.fetchone()
                if result and result[0] == 0:
                    # Добавляем дефолтные кластеры
                    await self.conn.execute("""
                        INSERT INTO vpn_clusters (name, description, location, is_active)
                        VALUES (?, ?, ?, ?)
                    """, (
                        "RU-Cluster", 
                        "Кластер серверов в России", 
                        "Moscow",
                        1
                    ))
                    
                    await self.conn.execute("""
                        INSERT INTO vpn_clusters (name, description, location, is_active)
                        VALUES (?, ?, ?, ?)
                    """, (
                        "NL-Cluster", 
                        "Кластер серверов в Нидерландах", 
                        "Amsterdam",
                        1
                    ))
                    
                    await self.conn.commit()
                    logger.info("Дефолтные кластеры добавлены в базу данных")
            
            # Проверяем наличие серверов
            async with self.conn.execute("SELECT COUNT(*) FROM vpn_servers") as cursor:
                result = await cursor.fetchone()
                if result and result[0] == 0:
                    # Получаем ID кластеров
                    ru_cluster_id = None
                    nl_cluster_id = None
                    
                    async with self.conn.execute("SELECT id FROM vpn_clusters WHERE name = ?", ("RU-Cluster",)) as cursor:
                        result = await cursor.fetchone()
                        if result:
                            ru_cluster_id = result[0]
                    
                    async with self.conn.execute("SELECT id FROM vpn_clusters WHERE name = ?", ("NL-Cluster",)) as cursor:
                        result = await cursor.fetchone()
                        if result:
                            nl_cluster_id = result[0]
                    
                    if ru_cluster_id:
                        # Добавляем тестовый сервер для российского кластера
                        await self.conn.execute("""
                            INSERT INTO vpn_servers (cluster_id, name, hostname, port, username, password, is_active, max_users)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ru_cluster_id,
                            "RU-Server-1", 
                            "test-ru-server.example.com", 
                            8080,
                            "admin",
                            "testpassword",
                            1,
                            100
                        ))
                    
                    if nl_cluster_id:
                        # Добавляем тестовый сервер для нидерландского кластера
                        await self.conn.execute("""
                            INSERT INTO vpn_servers (cluster_id, name, hostname, port, username, password, is_active, max_users)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            nl_cluster_id,
                            "NL-Server-1", 
                            "test-nl-server.example.com", 
                            8080,
                            "admin",
                            "testpassword",
                            1,
                            100
                        ))
                    
                    await self.conn.commit()
                    logger.info("Дефолтные серверы добавлены в базу данных")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации дефолтных данных: {e}")
            raise DatabaseError(f"Не удалось инициализировать дефолтные данные: {e}")
    
    async def close(self) -> None:
        """
        Закрывает соединение с базой данных
        """
        if self.conn:
            await self.conn.close()
            logger.info("Соединение с базой данных закрыто")


# Глобальный экземпляр базы данных
db = SQLiteDatabase()


async def init_db() -> None:
    """
    Инициализирует глобальный экземпляр базы данных
    """
    try:
        await db.connect()
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise DatabaseError(f"Не удалось инициализировать базу данных: {e}") 