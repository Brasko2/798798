"""
Пользовательские исключения для приложения
"""


class BotError(Exception):
    """Базовый класс для всех исключений бота"""
    pass


class DatabaseError(BotError):
    """Ошибка работы с базой данных"""
    pass


class UserNotFoundError(DatabaseError):
    """Пользователь не найден в базе данных"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")


class TariffNotFoundError(DatabaseError):
    """Тариф не найден в базе данных"""
    
    def __init__(self, tariff_id: int):
        self.tariff_id = tariff_id
        super().__init__(f"Tariff with ID {tariff_id} not found")


class SubscriptionNotFoundError(DatabaseError):
    """Подписка не найдена в базе данных"""
    
    def __init__(self, subscription_id: int):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription with ID {subscription_id} not found")


class PaymentError(BotError):
    """Ошибка при работе с платежами"""
    pass


class PaymentCreationError(PaymentError):
    """Ошибка при создании платежа"""
    pass


class PaymentCheckError(PaymentError):
    """Ошибка при проверке статуса платежа"""
    pass


class InsufficientFundsError(PaymentError):
    """Недостаточно средств на балансе"""
    
    def __init__(self, balance: float, required: float):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient funds: balance {balance}, required {required}")


class APIError(BotError):
    """Базовый класс для ошибок взаимодействия с API"""
    pass


class XRayAPIError(APIError):
    """Ошибка при взаимодействии с API XRay"""
    pass


class VPNServerError(APIError):
    """Ошибка при взаимодействии с VPN сервером"""
    pass


class VPNAccountCreationError(VPNServerError):
    """Ошибка при создании учетной записи VPN"""
    pass


class VPNAccountDeletionError(VPNServerError):
    """Ошибка при удалении учетной записи VPN"""
    pass


class ConfigurationError(BotError):
    """Ошибка в конфигурации приложения"""
    pass


class AuthError(Exception):
    """Ошибка авторизации"""
    pass


class SupportTicketError(Exception):
    """Ошибка при работе с тикетами поддержки"""
    pass 