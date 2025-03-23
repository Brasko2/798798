from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура бота"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔑 Мои подписки"))
    keyboard.add(KeyboardButton("💰 Купить VPN"))
    keyboard.add(KeyboardButton("💻 Инструкция"))
    keyboard.add(KeyboardButton("🛠 Поддержка"), KeyboardButton("💼 Мой профиль"))
    return keyboard


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администраторов"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔑 Мои подписки"))
    keyboard.add(KeyboardButton("💰 Купить VPN"))
    keyboard.add(KeyboardButton("💻 Инструкция"))
    keyboard.add(KeyboardButton("🛠 Поддержка"), KeyboardButton("💼 Мой профиль"))
    keyboard.add(KeyboardButton("⚙️ Настройки"), KeyboardButton("📊 Статистика"))
    return keyboard


def tariffs_keyboard(tariffs: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифа"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for tariff in tariffs:
        button_text = f"{tariff['name']} - {tariff['price']} руб."
        if tariff.get('traffic_limit'):
            button_text += f" ({tariff['traffic_limit']} ГБ)"
        button_text += f" / {tariff['duration']} дней"
        
        keyboard.add(
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"tariff:{tariff['tariff_id']}"
            )
        )
    
    return keyboard


def subscription_keyboard(subscription: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Клавиатура для управления подпиской"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Кнопка для получения ссылки на подписку
    if subscription.get('subscription_url') and subscription.get('status') == 'active':
        keyboard.add(
            InlineKeyboardButton(
                text="🔗 Получить ссылку", 
                callback_data=f"subscription:url:{subscription['subscription_id']}"
            )
        )
    
    # Кнопки для продления и отмены подписки
    if subscription.get('status') in ['active', 'expired']:
        keyboard.add(
            InlineKeyboardButton(
                text="🔄 Продлить", 
                callback_data=f"subscription:renew:{subscription['subscription_id']}"
            )
        )
    
    if subscription.get('status') == 'active':
        keyboard.add(
            InlineKeyboardButton(
                text="❌ Отменить", 
                callback_data=f"subscription:cancel:{subscription['subscription_id']}"
            )
        )
    
    # Кнопка для просмотра инструкции
    keyboard.add(
        InlineKeyboardButton(
            text="📚 Инструкция", 
            callback_data=f"instruction:{subscription['tariff_id']}"
        )
    )
    
    return keyboard


def subscriptions_list_keyboard(subscriptions: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура со списком подписок пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for subscription in subscriptions:
        status_emoji = "✅" if subscription.get('status') == 'active' else "⏳"
        button_text = f"{status_emoji} {subscription.get('tariff_name')}"
        
        if subscription.get('days_left') is not None:
            days_left = subscription.get('days_left')
            button_text += f" ({days_left} дн.)"
        
        keyboard.add(
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"subscription:details:{subscription['subscription_id']}"
            )
        )
    
    return keyboard


def confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения действия"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Да", 
            callback_data=f"confirm:{action}:{item_id}"
        ),
        InlineKeyboardButton(
            text="❌ Нет", 
            callback_data=f"cancel:{action}:{item_id}"
        )
    )
    
    return keyboard


def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            text="💳 Оплатить", 
            url=payment_url
        )
    )
    
    return keyboard


def support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для раздела поддержки"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            text="🆘 Создать обращение", 
            callback_data="support:create"
        )
    )
    
    keyboard.add(
        InlineKeyboardButton(
            text="📝 Мои обращения", 
            callback_data="support:list"
        )
    )
    
    return keyboard


def support_tickets_keyboard(tickets: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура со списком обращений пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for ticket in tickets:
        status_emoji = "✅" if ticket.get('is_resolved') else "⏳"
        button_text = f"{status_emoji} {ticket.get('subject')}"
        
        keyboard.add(
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"support:view:{ticket['ticket_id']}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(
            text="« Назад", 
            callback_data="support:back"
        )
    )
    
    return keyboard


def admin_tickets_keyboard(tickets: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура со списком обращений (для администраторов)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for ticket in tickets:
        status_emoji = "✅" if ticket.get('is_resolved') else "⏳"
        button_text = f"{status_emoji} #{ticket['ticket_id']} от {ticket.get('username', 'Unknown')}"
        
        keyboard.add(
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"admin:ticket:{ticket['ticket_id']}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(
            text="« Назад", 
            callback_data="admin:back"
        )
    )
    
    return keyboard


def admin_ticket_actions_keyboard(ticket_id: int, is_resolved: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с тикетом (для администраторов)"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if not is_resolved:
        keyboard.add(
            InlineKeyboardButton(
                text="✅ Отметить как решенный", 
                callback_data=f"admin:resolve:{ticket_id}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(
            text="💬 Ответить", 
            callback_data=f"admin:reply:{ticket_id}"
        )
    )
    
    keyboard.add(
        InlineKeyboardButton(
            text="« Назад к списку", 
            callback_data="admin:tickets"
        )
    )
    
    return keyboard


def cancel_keyboard(action: str = "cancel") -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            text="❌ Отмена", 
            callback_data=action
        )
    )
    
    return keyboard


def instruction_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для инструкций"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="📱 Android", 
            callback_data="instruction:android"
        ),
        InlineKeyboardButton(
            text="🍎 iOS", 
            callback_data="instruction:ios"
        )
    )
    
    keyboard.add(
        InlineKeyboardButton(
            text="🪟 Windows", 
            callback_data="instruction:windows"
        ),
        InlineKeyboardButton(
            text="🍏 macOS", 
            callback_data="instruction:macos"
        )
    )
    
    return keyboard 