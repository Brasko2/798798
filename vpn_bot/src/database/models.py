from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class User:
    def __init__(
        self,
        id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_admin: bool = False,
        balance: float = 0.0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.balance = balance
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or str(self.id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_admin": self.is_admin,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get(cls, id: int) -> 'User':
        """Получить пользователя по ID"""
        from .db import db
        
        user_data = await db.users.find_one({"id": id})
        if not user_data:
            raise ValueError(f"User with ID {id} not found")
            
        return cls(**user_data)
        
    @classmethod
    async def get_or_create(cls, id: int, defaults: dict = None) -> 'User':
        """Получить пользователя или создать нового, если его нет"""
        from .db import db
        
        defaults = defaults or {}
        user_data = await db.users.find_one({"id": id})
        
        if user_data:
            return cls(**user_data)
        
        new_user_data = {"id": id, **defaults}
        await db.users.insert_one(new_user_data)
        return cls(**new_user_data)
        
    async def save(self) -> None:
        """Сохранить пользователя в базу данных"""
        from .db import db
        
        self.updated_at = datetime.now()
        user_dict = self.to_dict()
        
        await db.users.update_one(
            {"id": self.id}, 
            {"$set": user_dict}, 
            upsert=True
        )
        
    async def update_balance(self, amount: float) -> None:
        """Обновить баланс пользователя"""
        self.balance += amount
        await self.save()
        
    @classmethod
    async def get_all(cls) -> List['User']:
        """Получить всех пользователей"""
        from .db import db
        
        users_data = await db.users.find().to_list(length=None)
        return [cls(**user_data) for user_data in users_data]


class Tariff:
    def __init__(
        self,
        tariff_id: int,
        name: str,
        description: str,
        price: float,
        duration: int,
        traffic_limit: Optional[float] = None,
        devices: int = 1,
        is_active: bool = True,
    ):
        self.tariff_id = tariff_id
        self.name = name
        self.description = description
        self.price = price
        self.duration = duration  # в днях
        self.traffic_limit = traffic_limit  # в ГБ
        self.devices = devices
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tariff_id": self.tariff_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "duration": self.duration,
            "traffic_limit": self.traffic_limit,
            "devices": self.devices,
            "is_active": self.is_active,
        }


class Subscription:
    def __init__(
        self,
        subscription_id: int,
        user_id: int,
        tariff_id: int,
        status: SubscriptionStatus,
        start_date: datetime,
        end_date: datetime,
        xray_client_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.subscription_id = subscription_id
        self.user_id = user_id
        self.tariff_id = tariff_id
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.xray_client_id = xray_client_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "tariff_id": self.tariff_id,
            "status": self.status.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "xray_client_id": self.xray_client_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Payment:
    def __init__(
        self,
        payment_id: int,
        user_id: int,
        subscription_id: Optional[int],
        amount: float,
        status: PaymentStatus,
        payment_method: str,
        external_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.payment_id = payment_id
        self.user_id = user_id
        self.subscription_id = subscription_id
        self.amount = amount
        self.status = status
        self.payment_method = payment_method
        self.external_id = external_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "amount": self.amount,
            "status": self.status.value,
            "payment_method": self.payment_method,
            "external_id": self.external_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SupportTicket:
    def __init__(
        self,
        ticket_id: int,
        user_id: int,
        subject: str,
        message: str,
        is_resolved: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.subject = subject
        self.message = message
        self.is_resolved = is_resolved
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "subject": self.subject,
            "message": self.message,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class VPNCluster:
    def __init__(
        self,
        cluster_id: int,
        name: str,
        description: str,
        location: str,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.cluster_id = cluster_id
        self.name = name
        self.description = description
        self.location = location
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class VPNServer:
    def __init__(
        self,
        server_id: int,
        cluster_id: int,
        name: str,
        hostname: str,
        port: int,
        username: str,
        password: str,
        load: float = 0.0,
        is_active: bool = True,
        max_users: int = 100,
        current_users: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.server_id = server_id
        self.cluster_id = cluster_id
        self.name = name
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.load = load
        self.is_active = is_active
        self.max_users = max_users
        self.current_users = current_users
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server_id": self.server_id,
            "cluster_id": self.cluster_id,
            "name": self.name,
            "hostname": self.hostname,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "load": self.load,
            "is_active": self.is_active,
            "max_users": self.max_users,
            "current_users": self.current_users,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def available_slots(self) -> int:
        """Возвращает количество доступных слотов на сервере"""
        return max(0, self.max_users - self.current_users) 