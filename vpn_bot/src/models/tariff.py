from dataclasses import dataclass, asdict
from typing import Optional, List, ClassVar

from ..database.db import db
from ..exceptions import TariffNotFoundError


@dataclass
class Tariff:
    """Модель тарифа VPN"""
    id: int
    name: str
    description: str
    price: float
    duration: int  # в днях
    traffic_limit: Optional[float] = None  # в ГБ
    devices: int = 1
    is_active: bool = True
    is_trial: bool = False  # Является ли тариф пробным
    
    # Коллекция в MongoDB
    collection: ClassVar[str] = "tariffs"

    def to_dict(self):
        """Преобразует объект в словарь для сохранения в базу"""
        return asdict(self)
    
    @classmethod
    async def get(cls, tariff_id: int) -> 'Tariff':
        """Получить тариф по ID"""
        tariff_data = await db.tariffs.find_one({"id": tariff_id})
        if not tariff_data:
            raise TariffNotFoundError(tariff_id)
            
        return cls(**tariff_data)
    
    @classmethod
    async def get_all(cls, only_active: bool = True, include_trial: bool = True) -> List['Tariff']:
        """
        Получить все тарифы
        
        Args:
            only_active: Включать только активные тарифы
            include_trial: Включать пробные тарифы
            
        Returns:
            Список тарифов
        """
        query = {}
        
        if only_active:
            query["is_active"] = True
            
        if not include_trial:
            query["is_trial"] = False
            
        tariffs_data = await db.tariffs.find(query).to_list(length=None)
        return [cls(**tariff_data) for tariff_data in tariffs_data]
    
    async def save(self) -> None:
        """Сохранить тариф в базу данных"""
        tariff_dict = self.to_dict()
        
        await db.tariffs.update_one(
            {"id": self.id}, 
            {"$set": tariff_dict}, 
            upsert=True
        )
    
    async def deactivate(self) -> None:
        """Деактивировать тариф"""
        self.is_active = False
        await self.save()
    
    async def activate(self) -> None:
        """Активировать тариф"""
        self.is_active = True
        await self.save()
    
    @classmethod
    async def create(cls, 
                    name: str, 
                    description: str, 
                    price: float, 
                    duration: int,
                    traffic_limit: Optional[float] = None,
                    devices: int = 1,
                    is_trial: bool = False) -> 'Tariff':
        """Создать новый тариф"""
        # Получаем следующий доступный ID
        next_id = await db.get_next_id("tariffs")
        
        tariff = cls(
            id=next_id,
            name=name,
            description=description,
            price=price,
            duration=duration,
            traffic_limit=traffic_limit,
            devices=devices,
            is_active=True,
            is_trial=is_trial
        )
        
        await tariff.save()
        return tariff
    
    @classmethod
    async def get_trial_tariff(cls) -> Optional['Tariff']:
        """Получить пробный тариф (если существует)"""
        tariff_data = await db.tariffs.find_one({"is_trial": True, "is_active": True})
        if not tariff_data:
            return None
            
        return cls(**tariff_data)
    
    @classmethod
    async def create_default_trial(cls) -> 'Tariff':
        """Создать стандартный пробный тариф (если он еще не существует)"""
        # Проверяем, существует ли уже пробный тариф
        existing_trial = await cls.get_trial_tariff()
        if existing_trial:
            return existing_trial
            
        # Создаем новый пробный тариф
        return await cls.create(
            name="Бесплатный пробный период",
            description="Попробуйте наш VPN бесплатно в течение 7 дней",
            price=0.0,
            duration=7,  # 7 дней
            traffic_limit=2.0,  # 2 ГБ трафика
            devices=1,
            is_trial=True
        ) 