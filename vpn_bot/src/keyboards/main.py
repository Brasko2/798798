"""
Основные клавиатуры бота
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from ..models import Tariff


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Создает главную клавиатуру бота.
    
    Args:
        is_admin: Является ли пользователь администратором
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура с основными кнопками
    """
    builder = ReplyKeyboardBuilder()
    
    # Основные кнопки для всех пользователей
    builder.add(
        KeyboardButton(text="🚀 Купить VPN"),
        KeyboardButton(text="👤 Мой профиль"),
        KeyboardButton(text="🔑 Мои подписки"),
        KeyboardButton(text="👥 Реферальная программа"),
        KeyboardButton(text="📲 Инструкции по настройке"),
        KeyboardButton(text="💫 Бонусы и акции"),
        KeyboardButton(text="💬 Поддержка"),
        KeyboardButton(text="ℹ️ О сервисе")
    )
    
    # Если пользователь администратор, добавляем кнопку админ-панели
    if is_admin:
        builder.add(KeyboardButton(text="⚙️ Админ-панель"))
    
    # Располагаем кнопки в 2 столбца
    builder.adjust(2)
    
    return builder.as_markup(resize_keyboard=True)


def get_tariffs_keyboard(tariffs: List[Tariff]) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру с доступными тарифами"""
    buttons = []
    
    for tariff in tariffs:
        # Форматируем цену для отображения
        price_text = f"{tariff.price:.2f}".rstrip("0").rstrip(".") if tariff.price == int(tariff.price) else f"{tariff.price:.2f}"
        
        # Создаем текст для кнопки
        button_text = f"{tariff.name} - {price_text} руб."
        
        # Добавляем кнопку с колбэком, который содержит ID тарифа
        buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=f"tariff:{tariff.id}")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру с кнопкой оплаты"""
    buttons = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
        ],
        [
            InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для раздела поддержки"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Создать тикет", callback_data="create_ticket")
        ],
        [
            InlineKeyboardButton(text="📋 Мои тикеты", callback_data="my_tickets")
        ],
        [
            InlineKeyboardButton(text="📚 FAQ", callback_data="faq")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для профиля пользователя"""
    buttons = [
        [
            InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="add_balance")
        ],
        [
            InlineKeyboardButton(text="🔑 Мои подписки", callback_data="my_subscriptions")
        ],
        [
            InlineKeyboardButton(text="📝 Изменить имя", callback_data="change_name")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tickets_list_keyboard(tickets, page=1, items_per_page=5) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру со списком тикетов и пагинацией"""
    # Вычисляем общее количество страниц
    total_pages = (len(tickets) + items_per_page - 1) // items_per_page
    
    # Получаем тикеты для текущей страницы
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(tickets))
    current_page_tickets = tickets[start_idx:end_idx]
    
    # Создаем кнопки для каждого тикета
    ticket_buttons = [
        [InlineKeyboardButton(
            text=f"#{ticket.id} - {ticket.subject[:25]}{'...' if len(ticket.subject) > 25 else ''}",
            callback_data=f"ticket:{ticket.id}"
        )] for ticket in current_page_tickets
    ]
    
    # Добавляем кнопки навигации, если необходимо
    nav_buttons = []
    
    if total_pages > 1:
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"tickets_page:{page-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"tickets_page:{page+1}"
            ))
    
    if nav_buttons:
        ticket_buttons.append(nav_buttons)
    
    # Добавляем кнопку для создания нового тикета
    ticket_buttons.append([
        InlineKeyboardButton(text="📝 Создать новый тикет", callback_data="create_ticket")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=ticket_buttons)


def ticket_action_keyboard(ticket_id: int, is_open: bool) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру для действий с тикетом"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Ответить", callback_data=f"reply_ticket:{ticket_id}")
        ]
    ]
    
    # Добавляем кнопку для закрытия/открытия тикета в зависимости от статуса
    if is_open:
        buttons.append([
            InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"close_ticket:{ticket_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔄 Открыть заново", callback_data=f"reopen_ticket:{ticket_id}")
        ])
    
    # Кнопка для возврата к списку тикетов
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="my_tickets")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру с кнопкой отмены"""
    buttons = [
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def instruction_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру с разделами инструкции"""
    buttons = [
        [
            InlineKeyboardButton(text="📱 Android", callback_data="instruction:android")
        ],
        [
            InlineKeyboardButton(text="🍎 iOS", callback_data="instruction:ios")
        ],
        [
            InlineKeyboardButton(text="🖥️ Windows", callback_data="instruction:windows")
        ],
        [
            InlineKeyboardButton(text="🍏 macOS", callback_data="instruction:macos")
        ],
        [
            InlineKeyboardButton(text="🐧 Linux", callback_data="instruction:linux")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с кнопкой возврата в главное меню
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой возврата в главное меню
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Вернуться в главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup() 