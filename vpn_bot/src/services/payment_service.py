"""
Модуль для работы с платежными системами
"""
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ..database import Database, Payment, PaymentStatus, Tariff, db
from ..payments import YooKassaPaymentProvider
from ..settings import settings
from ..exceptions import PaymentError


logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для работы с платежами"""
    
    def __init__(self, database: Database, payment_provider: YooKassaPaymentProvider):
        self.db = database
        self.payment_provider = payment_provider

    async def create_payment(
        self, user_id: int, tariff_id: int, redirect_url: str,
        subscription_id: Optional[int] = None, description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создание нового платежа
        
        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа
            redirect_url: URL для перенаправления после оплаты
            subscription_id: ID подписки (если продление)
            description: Описание платежа
            
        Returns:
            Dict с информацией о созданном платеже или None в случае ошибки
        """
        # Получаем данные тарифа
        tariff = await self.db.get_tariff(tariff_id)
        if not tariff:
            return None
            
        # Формируем описание платежа, если не указано явно
        if not description:
            description = f"Оплата тарифа {tariff.name} - {tariff.price} руб."
        
        # Формируем метаданные
        metadata = {
            "user_id": str(user_id),
            "tariff_id": str(tariff_id)
        }
        
        if subscription_id:
            metadata["subscription_id"] = str(subscription_id)
        
        # Создаем платеж в платежной системе
        payment_data = await self.payment_provider.create_payment(
            amount=tariff.price,
            description=description,
            user_id=user_id,
            redirect_url=redirect_url,
            metadata=metadata
        )
        
        if not payment_data:
            return None
        
        # Создаем запись о платеже в базе данных
        payment = Payment(
            payment_id=0,  # ID будет присвоен базой данных
            user_id=user_id,
            subscription_id=subscription_id,
            amount=float(payment_data["amount"]),
            status=PaymentStatus.PENDING,
            payment_method="yookassa",
            external_id=payment_data["id"]
        )
        
        payment = await self.db.create_payment(payment)
        if not payment:
            return None
            
        # Формируем результат
        return {
            "payment_id": payment.payment_id,
            "external_id": payment.external_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "payment_url": payment_data["payment_url"],
            "created_at": payment.created_at.isoformat()
        }

    async def check_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Dict с информацией о платеже или None в случае ошибки
        """
        # Получаем данные платежа из базы данных
        payment = await self.db.get_payment(payment_id)
        if not payment:
            return None
            
        # Если платеж уже в финальном статусе, возвращаем его данные
        if payment.status in [PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
            return {
                "payment_id": payment.payment_id,
                "external_id": payment.external_id,
                "amount": payment.amount,
                "status": payment.status.value,
                "created_at": payment.created_at.isoformat(),
                "updated_at": payment.updated_at.isoformat()
            }
            
        # Проверяем статус платежа в платежной системе
        if payment.external_id:
            payment_data = await self.payment_provider.check_payment(payment.external_id)
            
            if payment_data:
                # Определяем новый статус платежа
                new_status = PaymentStatus.PENDING
                if self.payment_provider.is_payment_successful(payment_data):
                    new_status = PaymentStatus.COMPLETED
                elif payment_data.get("status") == "canceled":
                    new_status = PaymentStatus.FAILED
                elif payment_data.get("status") == "refunded":
                    new_status = PaymentStatus.REFUNDED
                    
                # Обновляем статус платежа в базе данных, если он изменился
                if new_status != payment.status:
                    payment = await self.db.update_payment_status(
                        payment.payment_id,
                        new_status
                    )
        
        # Формируем результат
        return {
            "payment_id": payment.payment_id,
            "external_id": payment.external_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat()
        }

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обработка уведомления от платежной системы
        
        Args:
            webhook_data: Данные вебхука
            
        Returns:
            Dict с информацией о платеже или None в случае ошибки
        """
        # Обрабатываем вебхук в платежной системе
        payment_data = await self.payment_provider.process_webhook(webhook_data)
        if not payment_data:
            return None
            
        # Получаем внешний ID платежа
        external_id = payment_data.get("id")
        if not external_id:
            return None
            
        # Находим платеж в базе данных по внешнему ID
        payments = []
        async with self.db._get_connection() as conn:
            cursor = await conn.execute(
                'SELECT payment_id FROM payments WHERE external_id = ?',
                (external_id,)
            )
            rows = await cursor.fetchall()
            for row in rows:
                payments.append(row['payment_id'])
                
        if not payments:
            return None
            
        payment_id = payments[0]
        
        # Определяем новый статус платежа
        new_status = PaymentStatus.PENDING
        if self.payment_provider.is_payment_successful(payment_data):
            new_status = PaymentStatus.COMPLETED
        elif payment_data.get("status") == "canceled":
            new_status = PaymentStatus.FAILED
        elif payment_data.get("status") == "refunded":
            new_status = PaymentStatus.REFUNDED
            
        # Обновляем статус платежа в базе данных
        payment = await self.db.update_payment_status(
            payment_id,
            new_status
        )
        
        if not payment:
            return None
            
        # Формируем результат
        return {
            "payment_id": payment.payment_id,
            "external_id": payment.external_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "subscription_id": payment.subscription_id,
            "user_id": payment.user_id,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat()
        }

    async def get_user_payments(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение истории платежей пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество платежей
            
        Returns:
            Список платежей
        """
        # Получаем платежи пользователя
        async with self.db._get_connection() as conn:
            cursor = await conn.execute(
                '''
                SELECT * FROM payments 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                ''',
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            
        result = []
        for row in rows:
            payment = Payment(
                payment_id=row['payment_id'],
                user_id=row['user_id'],
                subscription_id=row['subscription_id'],
                amount=row['amount'],
                status=PaymentStatus(row['status']),
                payment_method=row['payment_method'],
                external_id=row['external_id'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
            
            # Если есть подписка, получаем данные о тарифе
            tariff_name = None
            if payment.subscription_id:
                subscription = await self.db.get_subscription(payment.subscription_id)
                if subscription:
                    tariff = await self.db.get_tariff(subscription.tariff_id)
                    if tariff:
                        tariff_name = tariff.name
            
            result.append({
                "payment_id": payment.payment_id,
                "amount": payment.amount,
                "status": payment.status.value,
                "payment_method": payment.payment_method,
                "subscription_id": payment.subscription_id,
                "tariff_name": tariff_name,
                "created_at": payment.created_at.isoformat()
            })
            
        return result 

# Создаем глобальный экземпляр для работы с платежами
payment_provider = YooKassaPaymentProvider(settings.yokassa_account_id, settings.yokassa_secret_key)
payment_service = PaymentService(db, payment_provider) 