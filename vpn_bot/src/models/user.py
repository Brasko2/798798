from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, ClassVar, Dict
import logging
from bson import ObjectId
import random
import string

from ..database.db import db
from ..exceptions import UserNotFoundError, DatabaseError


logger = logging.getLogger(__name__)


@dataclass
class User:
    """Модель пользователя Telegram"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    full_name: str = ""
    language_code: Optional[str] = None
    is_premium: bool = False
    balance: float = 0.0
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    has_used_trial: bool = False  # Использовал ли пользователь пробный период
    joined_at: datetime = field(default_factory=datetime.now)
    
    # Поля для реферальной системы
    referral_code: str = ""  # Код для приглашения других пользователей
    referrer_id: Optional[int] = None  # ID пользователя, который пригласил
    referral_count: int = 0  # Количество приглашенных пользователей
    referral_bonus_days: int = 0  # Бонусные дни за приглашенных пользователей
    
    # Коллекция в MongoDB
    collection: ClassVar[str] = "users"

    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "language_code": self.language_code,
            "is_premium": self.is_premium,
            "balance": self.balance,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "has_used_trial": self.has_used_trial,
            "joined_at": self.joined_at,
            "referral_code": self.referral_code,
            "referrer_id": self.referrer_id,
            "referral_count": self.referral_count,
            "referral_bonus_days": self.referral_bonus_days
        }

    @classmethod
    def from_document(cls, document: dict) -> 'User':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            telegram_id=document["telegram_id"],
            username=document.get("username"),
            first_name=document.get("first_name", ""),
            last_name=document.get("last_name"),
            full_name=document.get("full_name", ""),
            language_code=document.get("language_code"),
            is_premium=document.get("is_premium", False),
            balance=document.get("balance", 0.0),
            is_active=document.get("is_active", True),
            is_admin=document.get("is_admin", False),
            created_at=document.get("created_at", datetime.now()),
            updated_at=document.get("updated_at", datetime.now()),
            has_used_trial=document.get("has_used_trial", False),
            joined_at=document.get("joined_at", datetime.now()),
            referral_code=document.get("referral_code", ""),
            referrer_id=document.get("referrer_id"),
            referral_count=document.get("referral_count", 0),
            referral_bonus_days=document.get("referral_bonus_days", 0)
        )

    @staticmethod
    def generate_referral_code(length: int = 8) -> str:
        """Генерирует уникальный реферальный код"""
        # Генерируем код из букв и цифр
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @classmethod
    async def get_by_id(cls, user_id: int) -> Optional['User']:
        """Получает пользователя по ID"""
        try:
            document = await db.users.find_one({"id": user_id})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user: {str(e)}")

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int) -> Optional['User']:
        """Получает пользователя по Telegram ID"""
        try:
            document = await db.users.find_one({"telegram_id": telegram_id})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID {telegram_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user: {str(e)}")

    @classmethod
    async def get_by_referral_code(cls, referral_code: str) -> Optional['User']:
        """Получает пользователя по его реферальному коду"""
        try:
            document = await db.users.find_one({"referral_code": referral_code})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting user by referral code {referral_code}: {str(e)}")
            raise DatabaseError(f"Failed to get user by referral code: {str(e)}")

    @classmethod
    async def create(cls, user_data: dict) -> 'User':
        """Создает нового пользователя"""
        try:
            # Получение следующего ID
            next_id = await db.get_next_id("users")
            
            # Формирование полного имени
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() if last_name else first_name
            
            # Генерация реферального кода для нового пользователя
            referral_code = cls.generate_referral_code()
            
            # Проверка, что код уникален
            while await db.users.find_one({"referral_code": referral_code}):
                referral_code = cls.generate_referral_code()
            
            # Создание объекта пользователя
            user = cls(
                id=next_id,
                telegram_id=user_data["telegram_id"],
                username=user_data.get("username"),
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                language_code=user_data.get("language_code"),
                is_premium=user_data.get("is_premium", False),
                is_admin=user_data.get("is_admin", False),
                has_used_trial=user_data.get("has_used_trial", False),
                joined_at=datetime.now(),
                referral_code=referral_code,
                referrer_id=user_data.get("referrer_id"),
                referral_count=0,
                referral_bonus_days=0
            )
            
            # Сохранение в базу данных
            await db.users.insert_one(user.document)
            
            # Если пользователь был приглашен другим пользователем,
            # обновляем счетчик рефералов у пригласившего
            if user.referrer_id:
                await cls.increment_referral_count(user.referrer_id)
                
            logger.info(f"Created new user: {user.id} (Telegram ID: {user.telegram_id})")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseError(f"Failed to create user: {str(e)}")

    @classmethod
    async def update(cls, user_id: int, update_data: dict) -> Optional['User']:
        """Обновляет данные пользователя"""
        try:
            # Добавляем время обновления
            update_data["updated_at"] = datetime.now()
            
            # Выполняем обновление
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                # Получаем обновленного пользователя
                updated_user = await cls.get_by_id(user_id)
                logger.info(f"Updated user: {user_id}")
                return updated_user
            
            logger.warning(f"User not found or not updated: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to update user: {str(e)}")

    async def save(self) -> bool:
        """Сохраняет изменения в пользователе"""
        self.updated_at = datetime.now()
        try:
            result = await db.users.update_one(
                {"id": self.id},
                {"$set": self.document}
            )
            success = result.modified_count > 0
            if success:
                logger.info(f"Saved changes to user: {self.id}")
            else:
                logger.warning(f"No changes saved for user: {self.id}")
            return success
        except Exception as e:
            logger.error(f"Error saving user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to save user: {str(e)}")

    async def add_balance(self, amount: float) -> float:
        """Добавляет средства на баланс пользователя"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        try:
            self.balance += amount
            await self.save()
            logger.info(f"Added {amount} to user {self.id} balance. New balance: {self.balance}")
            return self.balance
        except Exception as e:
            logger.error(f"Error adding balance to user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to add balance: {str(e)}")

    async def subtract_balance(self, amount: float) -> float:
        """Снимает средства с баланса пользователя"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        try:
            self.balance -= amount
            await self.save()
            logger.info(f"Subtracted {amount} from user {self.id} balance. New balance: {self.balance}")
            return self.balance
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error subtracting balance from user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to subtract balance: {str(e)}")

    @classmethod
    async def count(cls) -> int:
        """Возвращает количество пользователей"""
        try:
            return await db.users.count_documents({})
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            raise DatabaseError(f"Failed to count users: {str(e)}")

    @classmethod
    async def get_recent(cls, limit: int = 10) -> List['User']:
        """Получает последних зарегистрированных пользователей"""
        try:
            cursor = db.users.find().sort("created_at", -1).limit(limit)
            users = []
            async for document in cursor:
                users.append(cls.from_document(document))
            return users
        except Exception as e:
            logger.error(f"Error getting recent users: {str(e)}")
            raise DatabaseError(f"Failed to get recent users: {str(e)}")

    @classmethod
    async def get_all(cls) -> List['User']:
        """Получает всех пользователей"""
        try:
            cursor = db.users.find()
            users = []
            async for document in cursor:
                users.append(cls.from_document(document))
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise DatabaseError(f"Failed to get all users: {str(e)}")

    async def deactivate(self) -> bool:
        """Деактивирует пользователя"""
        try:
            self.is_active = False
            success = await self.save()
            if success:
                logger.info(f"User {self.id} deactivated")
            return success
        except Exception as e:
            logger.error(f"Error deactivating user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to deactivate user: {str(e)}")

    async def activate(self) -> bool:
        """Активирует пользователя"""
        try:
            self.is_active = True
            success = await self.save()
            if success:
                logger.info(f"User {self.id} activated")
            return success
        except Exception as e:
            logger.error(f"Error activating user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to activate user: {str(e)}")

    @classmethod
    async def make_admin(cls, user_id: int) -> Optional['User']:
        """Делает пользователя администратором"""
        try:
            return await cls.update(user_id, {"is_admin": True})
        except Exception as e:
            logger.error(f"Error making user {user_id} admin: {str(e)}")
            raise DatabaseError(f"Failed to make user admin: {str(e)}")

    @classmethod
    async def remove_admin(cls, user_id: int) -> Optional['User']:
        """Удаляет у пользователя права администратора"""
        try:
            return await cls.update(user_id, {"is_admin": False})
        except Exception as e:
            logger.error(f"Error removing admin rights from user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to remove admin rights: {str(e)}")

    @classmethod
    async def find_by_username(cls, username: str) -> Optional['User']:
        """Найти пользователя по имени пользователя"""
        user_data = await db.users.find_one({"username": username})
        if not user_data:
            return None
        return cls(**user_data)

    async def set_trial_used(self) -> None:
        """Отметить, что пользователь использовал пробный период"""
        self.has_used_trial = True
        await self.save()

    async def can_use_trial(self) -> bool:
        """Проверить, может ли пользователь использовать пробный период"""
        return not self.has_used_trial

    async def get_subscriptions(self, active_only: bool = False) -> List:
        """Получить подписки пользователя"""
        from .subscription import Subscription
        return await Subscription.get_by_user(self.id, active_only=active_only)
        
    async def add_referral_bonus_days(self, days: int) -> int:
        """Добавляет бонусные дни за реферальную программу"""
        if days <= 0:
            raise ValueError("Days must be positive")
            
        try:
            self.referral_bonus_days += days
            await self.save()
            logger.info(f"Added {days} bonus days to user {self.id}. Total bonus days: {self.referral_bonus_days}")
            return self.referral_bonus_days
        except Exception as e:
            logger.error(f"Error adding referral bonus days to user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to add referral bonus days: {str(e)}")

    @classmethod
    async def increment_referral_count(cls, user_id: int, bonus_days: int = 3) -> Optional['User']:
        """
        Увеличивает счетчик рефералов пользователя и добавляет бонусные дни
        
        Args:
            user_id: ID пользователя
            bonus_days: Количество бонусных дней за одного реферала
            
        Returns:
            Обновленный объект пользователя или None, если пользователь не найден
        """
        try:
            # Получаем пользователя
            user = await cls.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found for incrementing referral count: {user_id}")
                return None
                
            # Увеличиваем счетчик рефералов
            user.referral_count += 1
            
            # Добавляем бонусные дни
            user.referral_bonus_days += bonus_days
            
            # Сохраняем изменения
            await user.save()
            
            logger.info(f"Incremented referral count for user {user_id}. New count: {user.referral_count}, bonus days: {user.referral_bonus_days}")
            
            # Проверяем, нужно ли увеличивать бонус для вышестоящего реферера (многоуровневая система)
            if user.referrer_id:
                # Для второго уровня даем меньше бонусных дней
                await cls.increment_referral_count(user.referrer_id, bonus_days=1)
            
            return user
        except Exception as e:
            logger.error(f"Error incrementing referral count for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to increment referral count: {str(e)}")

    async def get_referrals(self) -> List['User']:
        """Получает список пользователей, которые были приглашены данным пользователем"""
        try:
            cursor = db.users.find({"referrer_id": self.id})
            referrals = []
            async for document in cursor:
                referrals.append(self.from_document(document))
            return referrals
        except Exception as e:
            logger.error(f"Error getting referrals for user {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to get referrals: {str(e)}")

    async def apply_referral_bonus_to_subscription(self, days_to_use: Optional[int] = None) -> int:
        """
        Применяет бонусные дни к активной подписке пользователя
        
        Args:
            days_to_use: Количество дней для использования (если не указано, используются все)
            
        Returns:
            Количество использованных бонусных дней
        """
        if self.referral_bonus_days <= 0:
            return 0
            
        # Определяем, сколько бонусных дней использовать
        days = min(days_to_use or self.referral_bonus_days, self.referral_bonus_days)
        
        from .subscription import Subscription
        
        # Получаем активные подписки пользователя
        subscriptions = await Subscription.get_by_user(self.id, active_only=True)
        
        # Если активных подписок нет, просто возвращаем 0
        if not subscriptions:
            return 0
            
        # Выбираем первую активную подписку для продления
        subscription = subscriptions[0]
        
        # Продлеваем подписку на указанное количество дней
        await subscription.extend(days)
        
        # Уменьшаем количество бонусных дней
        self.referral_bonus_days -= days
        await self.save()
        
        logger.info(f"Applied {days} bonus days to subscription for user {self.id}. Remaining bonus days: {self.referral_bonus_days}")
        
        return days 