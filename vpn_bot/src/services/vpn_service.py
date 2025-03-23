from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..api import XRayAPI
from ..database import Database, User, Tariff, Subscription, SubscriptionStatus


class VPNService:
    def __init__(self, database: Database, xray_api: XRayAPI, default_inbound_id: int = 1):
        self.db = database
        self.xray_api = xray_api
        self.default_inbound_id = default_inbound_id

    async def create_subscription(
        self, user_id: int, tariff_id: int, payment_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создание новой подписки для пользователя
        
        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа
            payment_id: ID платежа (опционально)
            
        Returns:
            Dict с данными созданной подписки или None в случае ошибки
        """
        # Получаем данные пользователя
        user = await self.db.get_user(user_id)
        if not user:
            return None
            
        # Получаем данные тарифа
        tariff = await self.db.get_tariff(tariff_id)
        if not tariff:
            return None
            
        # Вычисляем даты начала и окончания подписки
        start_date = datetime.now()
        end_date = start_date + timedelta(days=tariff.duration)
        
        # Генерируем email для клиента в формате user_id@tariff_id.vpn
        client_email = f"{user_id}@{tariff_id}.vpn"
        
        # Создаем клиента в XRay
        client_data = await self.xray_api.create_client(
            inbound_id=self.default_inbound_id,
            email=client_email,
            traffic_limit_gb=tariff.traffic_limit,
            expire_days=tariff.duration
        )
        
        if not client_data:
            return None
            
        # Создаем подписку в базе данных
        subscription = Subscription(
            subscription_id=0,  # ID будет присвоен базой данных
            user_id=user_id,
            tariff_id=tariff_id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            xray_client_id=client_data["client_id"]
        )
        
        subscription = await self.db.create_subscription(subscription)
        if not subscription:
            # Если не удалось создать подписку в БД, удаляем клиента в XRay
            await self.xray_api.remove_client(
                inbound_id=self.default_inbound_id,
                client_id=client_data["client_id"]
            )
            return None
            
        # Формируем результат
        return {
            "subscription_id": subscription.subscription_id,
            "user_id": user_id,
            "tariff_id": tariff_id,
            "tariff_name": tariff.name,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "status": subscription.status.value,
            "client_id": client_data["client_id"],
            "subscription_url": client_data["subscription_url"]
        }

    async def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех активных подписок пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список активных подписок
        """
        subscriptions = await self.db.get_user_active_subscriptions(user_id)
        result = []
        
        for subscription in subscriptions:
            # Получаем данные тарифа
            tariff = await self.db.get_tariff(subscription.tariff_id)
            if not tariff:
                continue
                
            # Получаем статистику использования VPN
            stats = None
            if subscription.xray_client_id:
                stats = await self.xray_api.get_client_stats(
                    inbound_id=self.default_inbound_id,
                    client_id=subscription.xray_client_id
                )
                
            # Проверяем, не истекла ли подписка
            if subscription.end_date < datetime.now() and subscription.status == SubscriptionStatus.ACTIVE:
                subscription = await self.db.update_subscription_status(
                    subscription.subscription_id, 
                    SubscriptionStatus.EXPIRED
                )
                
            # Проверяем, не закончился ли трафик
            if stats and stats.get("remaining_traffic") == 0 and subscription.status == SubscriptionStatus.ACTIVE:
                subscription = await self.db.update_subscription_status(
                    subscription.subscription_id, 
                    SubscriptionStatus.EXPIRED
                )
                
            # Получаем ссылку на подписку
            subscription_url = None
            if subscription.xray_client_id and subscription.status == SubscriptionStatus.ACTIVE:
                subscription_url = await self.xray_api.generate_subscription_url(
                    inbound_id=self.default_inbound_id,
                    client_id=subscription.xray_client_id
                )
                
            # Формируем данные о подписке
            subscription_data = {
                "subscription_id": subscription.subscription_id,
                "tariff_id": tariff.tariff_id,
                "tariff_name": tariff.name,
                "status": subscription.status.value,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "days_left": (subscription.end_date - datetime.now()).days,
                "subscription_url": subscription_url
            }
            
            # Добавляем статистику, если она доступна
            if stats:
                subscription_data.update({
                    "upload_traffic_gb": round(stats["upload_traffic"] / (1024**3), 2),
                    "download_traffic_gb": round(stats["download_traffic"] / (1024**3), 2),
                    "total_traffic_gb": round(stats["total_traffic"] / (1024**3), 2),
                    "remaining_traffic_gb": round(stats["remaining_traffic"] / (1024**3), 2) if stats["remaining_traffic"] >= 0 else "∞",
                    "total_limit_gb": round(stats["total_limit"] / (1024**3), 2) if stats["total_limit"] > 0 else "∞",
                })
                
            result.append(subscription_data)
            
        return result

    async def renew_subscription(
        self, subscription_id: int, payment_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Продление существующей подписки
        
        Args:
            subscription_id: ID подписки
            payment_id: ID платежа (опционально)
            
        Returns:
            Dict с данными обновленной подписки или None в случае ошибки
        """
        # Получаем данные подписки
        subscription = await self.db.get_subscription(subscription_id)
        if not subscription:
            return None
            
        # Получаем данные тарифа
        tariff = await self.db.get_tariff(subscription.tariff_id)
        if not tariff:
            return None
            
        # Определяем новую дату окончания
        # Если подписка истекла, считаем от текущей даты, иначе от даты окончания
        if subscription.end_date < datetime.now():
            new_end_date = datetime.now() + timedelta(days=tariff.duration)
        else:
            new_end_date = subscription.end_date + timedelta(days=tariff.duration)
            
        # Обновляем срок действия клиента в XRay
        if subscription.xray_client_id:
            days_to_add = (new_end_date - datetime.now()).days
            success = await self.xray_api.update_client_expiry(
                inbound_id=self.default_inbound_id,
                client_id=subscription.xray_client_id,
                expire_days=days_to_add
            )
            
            if not success:
                return None
                
        # Обновляем статус и дату окончания подписки
        subscription.end_date = new_end_date
        subscription.status = SubscriptionStatus.ACTIVE
        
        # Обновляем подписку в базе данных
        updated_subscription = await self.db.update_subscription_status(
            subscription.subscription_id,
            SubscriptionStatus.ACTIVE
        )
        
        if not updated_subscription:
            return None
            
        # Получаем ссылку на подписку
        subscription_url = None
        if subscription.xray_client_id:
            subscription_url = await self.xray_api.generate_subscription_url(
                inbound_id=self.default_inbound_id,
                client_id=subscription.xray_client_id
            )
            
        # Формируем результат
        return {
            "subscription_id": subscription.subscription_id,
            "user_id": subscription.user_id,
            "tariff_id": subscription.tariff_id,
            "tariff_name": tariff.name,
            "start_date": subscription.start_date.isoformat(),
            "end_date": new_end_date.isoformat(),
            "status": SubscriptionStatus.ACTIVE.value,
            "subscription_url": subscription_url
        }

    async def cancel_subscription(self, subscription_id: int) -> bool:
        """
        Отмена подписки
        
        Args:
            subscription_id: ID подписки
            
        Returns:
            bool: True в случае успеха, иначе False
        """
        # Получаем данные подписки
        subscription = await self.db.get_subscription(subscription_id)
        if not subscription:
            return False
            
        # Удаляем клиента в XRay
        if subscription.xray_client_id:
            success = await self.xray_api.remove_client(
                inbound_id=self.default_inbound_id,
                client_id=subscription.xray_client_id
            )
            
            if not success:
                return False
                
        # Обновляем статус подписки
        updated_subscription = await self.db.update_subscription_status(
            subscription.subscription_id,
            SubscriptionStatus.CANCELLED
        )
        
        return updated_subscription is not None 