from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, ClassVar, Dict
import logging

from ..database.db import db
from ..exceptions import SubscriptionNotFoundError, DatabaseError


logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    """Статусы подписки"""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class Subscription:
    """Модель подписки VPN"""
    id: int
    user_id: int
    tariff_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    traffic_used: int = 0  # в мегабайтах
    traffic_limit: int = 0  # в мегабайтах, 0 = безлимитный
    max_devices: int = 1
    server_id: Optional[int] = None  # ID сервера
    cluster_id: Optional[int] = None  # ID кластера
    vpn_uuid: Optional[str] = None  # UUID учетной записи VPN на сервере
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Коллекция в MongoDB
    collection: ClassVar[str] = "subscriptions"

    def to_dict(self):
        """Преобразует объект в словарь для сохранения в базу"""
        data = asdict(self)
        # Преобразуем datetime и enum объекты
        for date_field in ["start_date", "end_date", "created_at", "updated_at"]:
            if isinstance(data[date_field], datetime):
                data[date_field] = data[date_field].isoformat()
        
        # Преобразуем enum в строку
        if isinstance(data["status"], SubscriptionStatus):
            data["status"] = data["status"].value
            
        return data
    
    @classmethod
    async def get(cls, subscription_id: int) -> 'Subscription':
        """Получить подписку по ID"""
        subscription_data = await db.subscriptions.find_one({"id": subscription_id})
        if not subscription_data:
            raise SubscriptionNotFoundError(subscription_id)
            
        # Преобразуем строковый статус в enum
        if "status" in subscription_data and isinstance(subscription_data["status"], str):
            subscription_data["status"] = SubscriptionStatus(subscription_data["status"])
            
        # Преобразуем строковые даты в datetime
        for date_field in ["start_date", "end_date", "created_at", "updated_at"]:
            if date_field in subscription_data and isinstance(subscription_data[date_field], str):
                subscription_data[date_field] = datetime.fromisoformat(subscription_data[date_field])
            
        return cls(**subscription_data)
    
    @classmethod
    async def get_by_user(cls, user_id: int, active_only: bool = False) -> List['Subscription']:
        """Получить подписки пользователя"""
        query = {"user_id": user_id}
        if active_only:
            query["status"] = SubscriptionStatus.ACTIVE.value
            
        subscriptions_data = await db.subscriptions.find(query).to_list(length=None)
        result = []
        
        for subscription_data in subscriptions_data:
            # Преобразуем строковый статус в enum
            if "status" in subscription_data and isinstance(subscription_data["status"], str):
                subscription_data["status"] = SubscriptionStatus(subscription_data["status"])
                
            # Преобразуем строковые даты в datetime
            for date_field in ["start_date", "end_date", "created_at", "updated_at"]:
                if date_field in subscription_data and isinstance(subscription_data[date_field], str):
                    subscription_data[date_field] = datetime.fromisoformat(subscription_data[date_field])
            
            result.append(cls(**subscription_data))
            
        return result
    
    async def save(self) -> None:
        """Сохранить подписку в базу данных"""
        self.updated_at = datetime.now()
        subscription_dict = self.to_dict()
        
        await db.subscriptions.update_one(
            {"id": self.id}, 
            {"$set": subscription_dict}, 
            upsert=True
        )
    
    async def cancel(self) -> None:
        """Отменить подписку"""
        self.status = SubscriptionStatus.CANCELLED
        await self.save()
    
    async def activate(self) -> None:
        """Активировать подписку"""
        self.status = SubscriptionStatus.ACTIVE
        await self.save()
    
    @classmethod
    async def create_from_tariff(cls, user_id: int, tariff_id: int, xray_client_id: Optional[str] = None) -> 'Subscription':
        """Создать подписку на основе тарифа"""
        from .tariff import Tariff
        
        # Получаем тариф
        tariff = await Tariff.get(tariff_id)
        
        # Рассчитываем даты
        start_date = datetime.now()
        end_date = start_date + timedelta(days=tariff.duration)
        
        # Получаем следующий доступный ID
        next_id = await db.get_next_id("subscriptions")
        
        subscription = cls(
            id=next_id,
            user_id=user_id,
            tariff_id=tariff_id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            xray_client_id=xray_client_id
        )
        
        await subscription.save()
        return subscription
    
    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли подписка"""
        return (
            self.status == SubscriptionStatus.ACTIVE and 
            self.start_date <= datetime.now() <= self.end_date
        )
    
    @property
    def days_left(self) -> int:
        """Возвращает количество дней до окончания подписки"""
        if not self.is_active:
            return 0
        
        delta = self.end_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def is_expired(self) -> bool:
        """Истекла ли подписка"""
        return self.end_date < datetime.now() or not self.is_active
    
    @property
    def traffic_left(self) -> int:
        """Оставшийся трафик в МБ (0 = безлимитный)"""
        if self.traffic_limit == 0:
            return 0  # безлимитный трафик
        
        return max(0, self.traffic_limit - self.traffic_used)
    
    @property
    def traffic_used_gb(self) -> float:
        """Использованный трафик в ГБ"""
        return round(self.traffic_used / 1024, 2)
    
    @property
    def traffic_limit_gb(self) -> float:
        """Лимит трафика в ГБ (0 = безлимитный)"""
        if self.traffic_limit == 0:
            return 0  # безлимитный трафик
        
        return round(self.traffic_limit / 1024, 2)
    
    @property
    def traffic_left_gb(self) -> float:
        """Оставшийся трафик в ГБ (0 = безлимитный)"""
        if self.traffic_limit == 0:
            return 0  # безлимитный трафик
        
        return round(self.traffic_left / 1024, 2)
    
    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tariff_id": self.tariff_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "traffic_used": self.traffic_used,
            "traffic_limit": self.traffic_limit,
            "max_devices": self.max_devices,
            "server_id": self.server_id,
            "cluster_id": self.cluster_id,
            "vpn_uuid": self.vpn_uuid,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_document(cls, document: dict) -> 'Subscription':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            user_id=document["user_id"],
            tariff_id=document["tariff_id"],
            start_date=document["start_date"],
            end_date=document["end_date"],
            is_active=document.get("is_active", True),
            traffic_used=document.get("traffic_used", 0),
            traffic_limit=document.get("traffic_limit", 0),
            max_devices=document.get("max_devices", 1),
            server_id=document.get("server_id"),
            cluster_id=document.get("cluster_id"),
            vpn_uuid=document.get("vpn_uuid"),
            created_at=document.get("created_at", datetime.now()),
            updated_at=document.get("updated_at", datetime.now())
        )
    
    @classmethod
    async def create(cls, user_id: int, tariff_id: int, days: int, 
                    traffic_limit: int = 0, max_devices: int = 1,
                    server_id: Optional[int] = None, 
                    cluster_id: Optional[int] = None,
                    vpn_uuid: Optional[str] = None) -> 'Subscription':
        """
        Создает новую подписку
        
        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа
            days: Длительность подписки в днях
            traffic_limit: Лимит трафика в МБ (0 = безлимитный)
            max_devices: Максимальное количество устройств
            server_id: ID сервера
            cluster_id: ID кластера
            vpn_uuid: UUID учетной записи VPN
            
        Returns:
            Новый объект подписки
        """
        try:
            # Получение следующего ID
            next_id = await db.get_next_id("subscriptions")
            
            # Даты начала и окончания
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            # Создание объекта подписки
            subscription = cls(
                id=next_id,
                user_id=user_id,
                tariff_id=tariff_id,
                start_date=start_date,
                end_date=end_date,
                traffic_limit=traffic_limit,
                max_devices=max_devices,
                server_id=server_id,
                cluster_id=cluster_id,
                vpn_uuid=vpn_uuid
            )
            
            # Сохранение в базу данных
            await db.subscriptions.insert_one(subscription.document)
            
            logger.info(f"Created subscription {subscription.id} for user {user_id}")
            return subscription
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise DatabaseError(f"Failed to create subscription: {str(e)}")
    
    @classmethod
    async def get_by_id(cls, subscription_id: int) -> 'Subscription':
        """Получает подписку по ID"""
        try:
            document = await db.subscriptions.find_one({"id": subscription_id})
            if not document:
                raise SubscriptionNotFoundError(subscription_id)
            
            return cls.from_document(document)
        except SubscriptionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting subscription by ID {subscription_id}: {str(e)}")
            raise DatabaseError(f"Failed to get subscription: {str(e)}")
    
    @classmethod
    async def get_by_user(cls, user_id: int) -> List['Subscription']:
        """Получает все подписки пользователя"""
        try:
            cursor = db.subscriptions.find({"user_id": user_id}).sort("created_at", -1)
            subscriptions = []
            
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting subscriptions for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get subscriptions: {str(e)}")
    
    @classmethod
    async def get_active_by_user(cls, user_id: int) -> List['Subscription']:
        """Получает активные подписки пользователя"""
        try:
            # Получаем текущую дату
            now = datetime.now()
            
            # Ищем активные подписки, которые еще не истекли
            cursor = db.subscriptions.find({
                "user_id": user_id,
                "is_active": True,
                "end_date": {"$gt": now}
            }).sort("end_date", 1)
            
            subscriptions = []
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting active subscriptions for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get active subscriptions: {str(e)}")
    
    @classmethod
    async def get_by_server(cls, server_id: int) -> List['Subscription']:
        """Получает все подписки на сервере"""
        try:
            cursor = db.subscriptions.find({"server_id": server_id}).sort("created_at", -1)
            subscriptions = []
            
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting subscriptions for server {server_id}: {str(e)}")
            raise DatabaseError(f"Failed to get subscriptions: {str(e)}")
    
    @classmethod
    async def get_active_by_server(cls, server_id: int) -> List['Subscription']:
        """Получает активные подписки на сервере"""
        try:
            # Получаем текущую дату
            now = datetime.now()
            
            # Ищем активные подписки, которые еще не истекли
            cursor = db.subscriptions.find({
                "server_id": server_id,
                "is_active": True,
                "end_date": {"$gt": now}
            }).sort("end_date", 1)
            
            subscriptions = []
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting active subscriptions for server {server_id}: {str(e)}")
            raise DatabaseError(f"Failed to get subscriptions for server: {str(e)}")
    
    @classmethod
    async def get_all_active(cls) -> List['Subscription']:
        """Получает все активные подписки"""
        try:
            # Получаем текущую дату
            now = datetime.now()
            
            # Ищем активные подписки, которые еще не истекли
            cursor = db.subscriptions.find({
                "is_active": True,
                "end_date": {"$gt": now}
            }).sort("end_date", 1)
            
            subscriptions = []
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting all active subscriptions: {str(e)}")
            raise DatabaseError(f"Failed to get all active subscriptions: {str(e)}")
    
    @classmethod
    async def get_expiring_soon(cls, days: int = 3) -> List['Subscription']:
        """Получает подписки, истекающие в ближайшие дни"""
        try:
            # Получаем текущую дату и дату через указанное количество дней
            now = datetime.now()
            expiry_date = now + timedelta(days=days)
            
            # Ищем активные подписки, которые истекают в указанный период
            cursor = db.subscriptions.find({
                "is_active": True,
                "end_date": {"$gt": now, "$lt": expiry_date}
            }).sort("end_date", 1)
            
            subscriptions = []
            async for document in cursor:
                subscriptions.append(cls.from_document(document))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting expiring subscriptions: {str(e)}")
            raise DatabaseError(f"Failed to get expiring subscriptions: {str(e)}")
    
    async def update(self, **kwargs) -> bool:
        """Обновляет данные подписки"""
        try:
            # Добавляем время обновления
            kwargs["updated_at"] = datetime.now()
            
            # Обновляем атрибуты объекта
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Выполняем обновление в базе данных
            result = await db.subscriptions.update_one(
                {"id": self.id},
                {"$set": kwargs}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated subscription {self.id}")
            else:
                logger.warning(f"Subscription not updated: {self.id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating subscription {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to update subscription: {str(e)}")
    
    async def deactivate(self) -> bool:
        """Деактивирует подписку"""
        try:
            return await self.update(is_active=False)
        except Exception as e:
            logger.error(f"Error deactivating subscription {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to deactivate subscription: {str(e)}")
    
    async def extend(self, days: int) -> bool:
        """Продлевает подписку на указанное количество дней"""
        try:
            # Рассчитываем новую дату окончания
            if self.end_date < datetime.now():
                # Если подписка уже истекла, считаем от текущей даты
                new_end_date = datetime.now() + timedelta(days=days)
            else:
                # Если подписка активна, продлеваем от текущей даты окончания
                new_end_date = self.end_date + timedelta(days=days)
            
            return await self.update(
                end_date=new_end_date,
                is_active=True
            )
        except Exception as e:
            logger.error(f"Error extending subscription {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to extend subscription: {str(e)}")
    
    async def add_traffic(self, mb_amount: int) -> bool:
        """Добавляет трафик к лимиту подписки"""
        try:
            # Если трафик безлимитный, не изменяем его
            if self.traffic_limit == 0:
                return True
            
            # Увеличиваем лимит трафика
            new_limit = self.traffic_limit + mb_amount
            
            return await self.update(traffic_limit=new_limit)
        except Exception as e:
            logger.error(f"Error adding traffic to subscription {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to add traffic: {str(e)}")
    
    async def log_traffic_usage(self, mb_used: int) -> bool:
        """Логирует использование трафика"""
        try:
            # Обновляем использованный трафик
            new_traffic_used = self.traffic_used + mb_used
            
            # Проверяем, не превышен ли лимит
            if self.traffic_limit > 0 and new_traffic_used >= self.traffic_limit:
                # Если лимит превышен, деактивируем подписку
                return await self.update(
                    traffic_used=new_traffic_used,
                    is_active=False
                )
            else:
                # Иначе просто обновляем счетчик
                return await self.update(traffic_used=new_traffic_used)
        except Exception as e:
            logger.error(f"Error logging traffic for subscription {self.id}: {str(e)}")
            raise DatabaseError(f"Failed to log traffic: {str(e)}")
    
    async def get_vpn_config(self) -> Dict:
        """
        Получает конфигурацию VPN для подписки
        
        Returns:
            Словарь с конфигурацией VPN
        """
        try:
            # Проверяем, назначен ли подписке сервер
            if not self.server_id or not self.vpn_uuid:
                raise Exception("VPN server or account not assigned to this subscription")
            
            # Здесь можно получить данные сервера и сгенерировать конфигурационный файл
            # или ссылку для подключения
            from ..models.cluster import VPNServer
            
            # Получаем данные сервера
            server = await VPNServer.get_by_id(self.server_id)
            if not server:
                raise Exception(f"VPN server with ID {self.server_id} not found")
            
            # Возвращаем базовые данные для подключения
            # Реальный конфиг будет зависеть от используемой VPN технологии
            config = {
                "subscription_id": self.id,
                "server": {
                    "ip": server.ip_address,
                    "country": server.country,
                    "city": server.city,
                    "name": server.name
                },
                "account": {
                    "uuid": self.vpn_uuid,
                    "expires": self.end_date.timestamp(),
                    "protocol": "vless",  # Пример протокола
                    "connection_string": f"vless://{self.vpn_uuid}@{server.ip_address}:443?security=tls"
                },
                "expiry_date": self.end_date.strftime("%Y-%m-%d %H:%M:%S"),
                "days_left": self.days_left,
                "traffic_used_gb": self.traffic_used_gb,
                "traffic_limit_gb": self.traffic_limit_gb,
                "is_unlimited_traffic": self.traffic_limit == 0,
                "max_devices": self.max_devices
            }
            
            return config
        
        except Exception as e:
            logger.error(f"Error getting VPN config for subscription {self.id}: {str(e)}")
            raise Exception(f"Failed to get VPN configuration: {str(e)}") 