import logging
import uuid
from typing import Dict, Any, Optional, Union
from datetime import datetime

from yookassa import Payment as YooKassaPayment
from yookassa import Configuration
from yookassa.domain.notification import WebhookNotification

from ..settings import Settings


# Создаем экземпляр настроек
settings = Settings()


class YooKassaPaymentProvider:
    def __init__(self, shop_id: str = None, secret_key: str = None):
        self.shop_id = shop_id or settings.yokassa_account_id
        self.secret_key = secret_key or settings.yokassa_secret_key
        self._logger = logging.getLogger(__name__)
        
        # Инициализация конфигурации YooKassa
        Configuration.account_id = self.shop_id
        Configuration.secret_key = self.secret_key

    async def create_payment(
        self, amount: float, description: str, user_id: int, 
        redirect_url: str, metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Создание нового платежа
        
        Args:
            amount: Сумма платежа в рублях
            description: Описание платежа
            user_id: ID пользователя
            redirect_url: URL для перенаправления после оплаты
            metadata: Дополнительные данные для платежа
            
        Returns:
            Dict с информацией о созданном платеже или None в случае ошибки
        """
        try:
            # Создаем идентификатор платежа
            idempotence_key = str(uuid.uuid4())
            
            # Подготавливаем метаданные
            metadata = metadata or {}
            metadata["user_id"] = str(user_id)
            
            # Создаем платеж
            payment = YooKassaPayment.create({
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": redirect_url
                },
                "capture": True,
                "description": description,
                "metadata": metadata
            }, idempotence_key)
            
            if payment.confirmation and payment.confirmation.confirmation_url:
                return {
                    "id": payment.id,
                    "status": payment.status,
                    "amount": float(payment.amount.value),
                    "currency": payment.amount.currency,
                    "description": payment.description,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                    "payment_url": payment.confirmation.confirmation_url,
                    "metadata": payment.metadata
                }
            else:
                self._logger.error(f"Failed to create payment: no confirmation URL")
                return None
        except Exception as e:
            self._logger.error(f"Error creating payment: {str(e)}")
            return None

    async def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа в системе YooKassa
            
        Returns:
            Dict с информацией о платеже или None в случае ошибки
        """
        try:
            payment = YooKassaPayment.find_one(payment_id)
            
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "description": payment.description,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid": payment.paid,
                "metadata": payment.metadata
            }
        except Exception as e:
            self._logger.error(f"Error checking payment {payment_id}: {str(e)}")
            return None

    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка вебхука от YooKassa
        
        Args:
            data: Данные вебхука
            
        Returns:
            Dict с информацией о платеже или None в случае ошибки
        """
        try:
            notification = WebhookNotification(data)
            payment = notification.object
            
            return {
                "event": notification.event,
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "description": payment.description,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid": payment.paid,
                "metadata": payment.metadata
            }
        except Exception as e:
            self._logger.error(f"Error processing webhook: {str(e)}")
            return None

    @staticmethod
    def is_payment_successful(payment_data: Dict[str, Any]) -> bool:
        """
        Проверка успешности платежа
        
        Args:
            payment_data: Данные платежа
            
        Returns:
            bool: True если платеж успешен, иначе False
        """
        return payment_data and payment_data.get("status") == "succeeded" 