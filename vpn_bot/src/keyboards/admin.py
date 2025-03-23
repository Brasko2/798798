"""
Клавиатуры для админской панели бота
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для админской панели"""
    buttons = [
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="👥 Пользователи")
        ],
        [
            KeyboardButton(text="💵 Финансы"),
            KeyboardButton(text="🔧 Настройки")
        ],
        [
            KeyboardButton(text="🏠 Главное меню")
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def tariff_management_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для управления тарифами"""
    buttons = [
        [
            KeyboardButton(text="➕ Добавить тариф"),
            KeyboardButton(text="✏️ Редактировать тариф")
        ],
        [
            KeyboardButton(text="❌ Удалить тариф"),
            KeyboardButton(text="📋 Список тарифов")
        ],
        [
            KeyboardButton(text="⬅️ Назад к настройкам")
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def user_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для действий с пользователем"""
    buttons = [
        [
            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"admin_add_balance:{user_id}"),
            InlineKeyboardButton(text="🔒 Заблокировать", callback_data=f"admin_block_user:{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔑 Подписки", callback_data=f"admin_view_subs:{user_id}"),
            InlineKeyboardButton(text="📨 Написать", callback_data=f"admin_message_user:{user_id}")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tariff_list_keyboard(tariffs, page=1, items_per_page=5) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру со списком тарифов и пагинацией"""
    # Вычисляем общее количество страниц
    total_pages = (len(tariffs) + items_per_page - 1) // items_per_page
    
    # Получаем тарифы для текущей страницы
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(tariffs))
    current_page_tariffs = tariffs[start_idx:end_idx]
    
    # Создаем кнопки для каждого тарифа
    tariff_buttons = [
        [InlineKeyboardButton(
            text=f"{tariff.name} - {tariff.price} руб.",
            callback_data=f"admin_tariff:{tariff.id}"
        )] for tariff in current_page_tariffs
    ]
    
    # Добавляем кнопки навигации, если необходимо
    nav_buttons = []
    
    if total_pages > 1:
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_tariff_page:{page-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"admin_tariff_page:{page+1}"
            ))
    
    if nav_buttons:
        tariff_buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=tariff_buttons)


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для подтверждения рассылки"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="admin_broadcast_cancel")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def maintenance_mode_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для управления режимом обслуживания"""
    status = "Включен ✅" if is_enabled else "Выключен ❌"
    action = "Выключить" if is_enabled else "Включить"
    
    buttons = [
        [
            InlineKeyboardButton(text=f"Статус: {status}", callback_data="noop")
        ],
        [
            InlineKeyboardButton(
                text=f"{action} режим обслуживания", 
                callback_data="admin_toggle_maintenance"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_tariff_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления тарифами"""
    buttons = [
        [
            InlineKeyboardButton(text="➕ Добавить тариф", callback_data="admin:tariff:add"),
        ],
        [
            InlineKeyboardButton(text="📋 Список тарифов", callback_data="admin:tariff:list"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_edit_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования пользователя"""
    buttons = [
        [
            InlineKeyboardButton(text="💰 Изменить баланс", callback_data=f"admin:user:balance:{user_id}"),
            InlineKeyboardButton(text="🚫 Блокировать", callback_data=f"admin:user:block:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="📈 Статистика", callback_data=f"admin:user:stats:{user_id}"),
            InlineKeyboardButton(text="🔄 Сбросить", callback_data=f"admin:user:reset:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="🎁 Бонус", callback_data=f"admin:user:bonus:{user_id}"),
            InlineKeyboardButton(text="📝 Заметка", callback_data=f"admin:user:note:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin:users:list"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 