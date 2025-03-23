from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, ClassVar

from ..database.db import db


class PaymentStatus(str, Enum):
    """Статусы платежа"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    """Модель платежа"""
    id: int
    user_id: int
    amount: float
    status: PaymentStatus
    payment_method: str
    subscription_id: Optional[int] = None
    external_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Коллекция в MongoDB
    collection: ClassVar[str] = "payments"

    def to_dict(self):
        """Преобразует объект в словарь для сохранения в базу"""
        data = asdict(self)
        # Преобразуем datetime и enum объекты
        for date_field in ["created_at", "updated_at"]:
            if isinstance(data[date_field], datetime):
                data[date_field] = data[date_field].isoformat()
        
        # Преобразуем enum в строку
        if isinstance(data["status"], PaymentStatus):
            data["status"] = data["status"].value
            
        return data
    
    @classmethod
    async def get(cls, payment_id: int) -> 'Payment':
        """Получить платеж по ID"""
        payment_data = await db.payments.find_one({"id": payment_id})
        if not payment_data:
            return None
            
        # Преобразуем строковый статус в enum
        if "status" in payment_data and isinstance(payment_data["status"], str):
            payment_data["status"] = PaymentStatus(payment_data["status"])
            
        # Преобразуем строковые даты в datetime
        for date_field in ["created_at", "updated_at"]:
            if date_field in payment_data and isinstance(payment_data[date_field], str):
                payment_data[date_field] = datetime.fromisoformat(payment_data[date_field])
            
        return cls(**payment_data)
    
    @classmethod
    async def get_by_external_id(cls, external_id: str) -> Optional['Payment']:
        """Получить платеж по внешнему ID"""
        payment_data = await db.payments.find_one({"external_id": external_id})
        if not payment_data:
            return None
            
        # Преобразуем строковый статус в enum
        if "status" in payment_data and isinstance(payment_data["status"], str):
            payment_data["status"] = PaymentStatus(payment_data["status"])
            
        # Преобразуем строковые даты в datetime
        for date_field in ["created_at", "updated_at"]:
            if date_field in payment_data and isinstance(payment_data[date_field], str):
                payment_data[date_field] = datetime.fromisoformat(payment_data[date_field])
            
        return cls(**payment_data)
    
    @classmethod
    async def get_by_user(cls, user_id: int, limit: int = 10) -> List['Payment']:
        """Получить платежи пользователя"""
        payments_data = await db.payments.find({"user_id": user_id}).sort("created_at", -1).limit(limit).to_list(length=None)
        result = []
        
        for payment_data in payments_data:
            # Преобразуем строковый статус в enum
            if "status" in payment_data and isinstance(payment_data["status"], str):
                payment_data["status"] = PaymentStatus(payment_data["status"])
                
            # Преобразуем строковые даты в datetime
            for date_field in ["created_at", "updated_at"]:
                if date_field in payment_data and isinstance(payment_data[date_field], str):
                    payment_data[date_field] = datetime.fromisoformat(payment_data[date_field])
            
            result.append(cls(**payment_data))
            
        return result
    
    async def save(self) -> None:
        """Сохранить платеж в базу данных"""
        self.updated_at = datetime.now()
        payment_dict = self.to_dict()
        
        await db.payments.update_one(
            {"id": self.id}, 
            {"$set": payment_dict}, 
            upsert=True
        )
    
    async def complete(self) -> None:
        """Отметить платеж как завершенный"""
        self.status = PaymentStatus.COMPLETED
        await self.save()
        
        # Если платеж связан с подпиской и пользователем, обновляем баланс
        if self.subscription_id:
            from .user import User
            try:
                user = await User.get(self.user_id)
                await user.update_balance(self.amount)
            except Exception:
                # Логирование ошибки
                pass
    
    async def fail(self) -> None:
        """Отметить платеж как неуспешный"""
        self.status = PaymentStatus.FAILED
        await self.save()
    
    async def refund(self) -> None:
        """Отметить платеж как возвращенный"""
        if self.status == PaymentStatus.COMPLETED:
            self.status = PaymentStatus.REFUNDED
            await self.save()
            
            # Если платеж был завершен, вычитаем сумму из баланса
            from .user import User
            try:
                user = await User.get(self.user_id)
                await user.update_balance(-self.amount)
            except Exception:
                # Логирование ошибки
                pass
    
    @classmethod
    async def create(cls, 
                    user_id: int, 
                    amount: float, 
                    payment_method: str,
                    subscription_id: Optional[int] = None,
                    external_id: Optional[str] = None) -> 'Payment':
        """Создать новый платеж"""
        # Получаем следующий доступный ID
        next_id = await db.get_next_id("payments")
        
        payment = cls(
            id=next_id,
            user_id=user_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            payment_method=payment_method,
            subscription_id=subscription_id,
            external_id=external_id
        )
        
        await payment.save()
        return payment 