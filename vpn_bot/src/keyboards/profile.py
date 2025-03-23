"""
Клавиатуры для профиля пользователя
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_profile_kb(is_admin: bool = False, has_active_subs: bool = False, has_bonus_days: bool = False) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для профиля пользователя
    
    Args:
        is_admin: Является ли пользователь администратором
        has_active_subs: Есть ли у пользователя активные подписки
        has_bonus_days: Есть ли у пользователя бонусные дни
        
    Returns:
        Инлайн-клавиатура с кнопками профиля
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для просмотра подписок
    if has_active_subs:
        builder.button(
            text="🔑 Мои подписки",
            callback_data="my_subscriptions"
        )
    
    # Кнопка для покупки VPN
    builder.button(
        text="💰 Купить VPN",
        callback_data="buy_vpn"
    )
    
    # Кнопка для просмотра реферальной программы
    builder.button(
        text="🔗 Реферальная программа",
        callback_data="show_referral"
    )
    
    # Кнопка для применения бонусных дней (если они есть)
    if has_bonus_days:
        builder.button(
            text="🎁 Применить бонусные дни",
            callback_data="apply_referral_bonus"
        )
    
    # Кнопка для инструкций
    builder.button(
        text="📋 Инструкции",
        callback_data="instructions"
    )
    
    # Кнопка для обращения в поддержку
    builder.button(
        text="🆘 Поддержка",
        callback_data="open_support"
    )
    
    # Если пользователь администратор, добавляем кнопку админ-панели
    if is_admin:
        builder.button(
            text="⚙️ Админ-панель",
            callback_data="admin_panel"
        )
    
    # Кнопка для возврата в главное меню
    builder.button(
        text="🏠 Главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup() 