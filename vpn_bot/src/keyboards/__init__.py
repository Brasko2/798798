"""
Модуль клавиатур для бота
"""

from .main import get_main_keyboard, get_back_to_main_keyboard
from .admin import get_admin_keyboard, get_admin_tariff_keyboard, get_admin_edit_user_keyboard
from .tariff import get_tariff_keyboard, get_pagination_keyboard
from .payment import get_payment_keyboard, get_check_payment_keyboard
from .user import get_user_keyboard, get_subscription_keyboard
from .support import get_support_keyboard, get_support_ticket_keyboard, get_callback_keyboard
from .buy import get_tariff_selection_kb, get_payment_kb, get_payment_success_kb
from .server import get_server_keyboard, get_server_edit_keyboard
from .cluster import get_cluster_keyboard, get_cluster_edit_keyboard
from .referral import get_referral_keyboard, get_bonus_days_keyboard, get_referrer_keyboard
from .instructions import get_instructions_keyboard, get_instructions_back_keyboard
from .bonus import get_bonus_keyboard, get_back_to_bonus_keyboard

__all__ = [
    'get_main_keyboard',
    'get_back_to_main_keyboard',
    'get_admin_keyboard',
    'get_admin_tariff_keyboard',
    'get_admin_edit_user_keyboard',
    'get_tariff_keyboard',
    'get_pagination_keyboard',
    'get_payment_keyboard',
    'get_check_payment_keyboard',
    'get_user_keyboard',
    'get_subscription_keyboard',
    'get_support_keyboard',
    'get_support_ticket_keyboard',
    'get_callback_keyboard',
    'get_tariff_selection_kb',
    'get_payment_kb',
    'get_payment_success_kb',
    'get_server_keyboard',
    'get_server_edit_keyboard',
    'get_cluster_keyboard',
    'get_cluster_edit_keyboard',
    'get_referral_keyboard',
    'get_bonus_days_keyboard',
    'get_referrer_keyboard',
    'get_instructions_keyboard',
    'get_instructions_back_keyboard',
    'get_bonus_keyboard',
    'get_back_to_bonus_keyboard',
] 