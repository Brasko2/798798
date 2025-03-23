"""
Клавиатуры для реферальной системы
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_referral_kb(has_bonus: bool = False) -> InlineKeyboardMarkup:
    """
    Создает основную клавиатуру реферальной системы
    
    Args:
        has_bonus: Есть ли у пользователя бонусные дни
        
    Returns:
        Инлайн-клавиатура с кнопками реферальной системы
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для просмотра статистики рефералов
    builder.button(
        text="📊 Статистика рефералов",
        callback_data="referral_stats"
    )
    
    # Кнопка для применения бонуса (если есть бонусные дни)
    if has_bonus:
        builder.button(
            text="🎁 Применить бонус",
            callback_data="apply_referral_bonus"
        )
    
    # Кнопка для получения реферальной ссылки
    builder.button(
        text="🔗 Поделиться реферальной ссылкой",
        callback_data="share_referral"
    )
    
    # Кнопка для возврата в главное меню
    builder.button(
        text="🏠 Вернуться в главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_referral_stats_kb() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для экрана статистики рефералов
    
    Returns:
        Инлайн-клавиатура с кнопками навигации
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для возврата к экрану рефералов
    builder.button(
        text="◀️ Назад",
        callback_data="back_to_referral"
    )
    
    # Кнопка для получения реферальной ссылки
    builder.button(
        text="🔗 Поделиться реферальной ссылкой",
        callback_data="share_referral"
    )
    
    # Кнопка для возврата в главное меню
    builder.button(
        text="🏠 Вернуться в главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_referral_apply_bonus_kb(max_days: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора количества дней при применении бонуса
    
    Args:
        max_days: Максимальное количество доступных бонусных дней
        
    Returns:
        Инлайн-клавиатура с кнопками выбора дней
    """
    builder = InlineKeyboardBuilder()
    
    # Создаем кнопки для различных вариантов дней
    days_options = [1, 3, 5, 10, max_days]
    
    # Отфильтровываем варианты, которые больше доступных дней
    days_options = [days for days in days_options if days <= max_days]
    
    # Добавляем уникальные значения (без дубликатов)
    unique_days = set(days_options)
    for days in sorted(unique_days):
        builder.button(
            text=f"{days} {_days_text(days)}",
            callback_data=f"apply_days:{days}"
        )
    
    # Кнопка отмены
    builder.button(
        text="❌ Отмена",
        callback_data="back_to_referral"
    )
    
    # Устанавливаем ширину строки в 2 кнопки для дней, и 1 для отмены
    if len(unique_days) > 1:
        builder.adjust(2, 2, 1)
    else:
        builder.adjust(1)
    
    return builder.as_markup()


def _days_text(days: int) -> str:
    """
    Возвращает правильное склонение слова 'день' в зависимости от числа
    
    Args:
        days: Количество дней
        
    Returns:
        Правильное склонение слова 'день'
    """
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return "дня"
    else:
        return "дней"


def get_referral_keyboard(has_bonus_days: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для реферальной системы"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Моя статистика", callback_data="referral:stats")
        ],
        [
            InlineKeyboardButton(text="🔗 Поделиться ссылкой", callback_data="referral:share")
        ]
    ]
    
    # Если у пользователя есть бонусные дни, добавляем кнопку для их применения
    if has_bonus_days:
        buttons.insert(1, [
            InlineKeyboardButton(text="🎁 Использовать бонус", callback_data="referral:apply_bonus")
        ])
    
    # Добавляем кнопку возврата в меню
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main:menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bonus_days_keyboard(max_days: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора количества бонусных дней"""
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с разным количеством дней
    days_options = [1, 3, 5, 10]
    
    # Фильтруем опции на основе доступных дней
    available_options = [days for days in days_options if days <= max_days]
    
    # Если у пользователя больше дней, чем максимальная опция, добавляем все дни
    if max_days > max(days_options, default=0):
        available_options.append(max_days)
    
    # Добавляем кнопки по 2 в ряд
    for i in range(0, len(available_options), 2):
        row = []
        for days in available_options[i:i+2]:
            row.append(InlineKeyboardButton(
                text=f"{days} {_days_text(days)}",
                callback_data=f"referral:apply_days:{days}"
            ))
        builder.row(*row)
    
    # Добавляем кнопку отмены
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="referral:back")
    )
    
    return builder.as_markup()


def get_referrer_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с приглашением в реферальную программу"""
    buttons = [
        [
            InlineKeyboardButton(text="🎁 Стать рефералом", callback_data="referral:join")
        ],
        [
            InlineKeyboardButton(text="❓ Узнать подробнее", callback_data="referral:info")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main:menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 