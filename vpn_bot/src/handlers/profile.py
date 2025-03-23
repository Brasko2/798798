"""
Обработчики для профиля пользователя
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime

from ..models.user import User
from ..models.subscription import Subscription
from ..keyboards.profile import get_profile_kb
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("profile"))
@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: Message, user: User):
    """Обработчик команды /profile и кнопки 'Мой профиль'"""
    try:
        # Получаем статистику подписок пользователя
        subscriptions = await user.get_subscriptions(active_only=True)
        active_subs_count = len(subscriptions)
        
        # Форматируем время регистрации
        joined_date = user.joined_at.strftime("%d.%m.%Y")
        
        # Получаем количество рефералов
        referral_count = user.referral_count
        
        # Формируем текст профиля
        text = f"👤 <b>Профиль пользователя</b>\n\n"
        text += f"🆔 ID: <code>{user.id}</code>\n"
        
        if user.username:
            text += f"👤 Имя пользователя: @{user.username}\n"
            
        text += f"📅 Дата регистрации: {joined_date}\n"
        text += f"💳 Баланс: {user.balance:.2f} ₽\n\n"
        
        # Информация о подписках
        text += f"🔑 Активные подписки: {active_subs_count}\n"
        
        # Информация о рефералах
        text += f"👥 Приглашено пользователей: {referral_count}\n"
        text += f"⏳ Бонусные дни: {user.referral_bonus_days}\n\n"
        
        if user.is_admin:
            text += "👑 <b>Вы администратор</b>\n\n"
        
        # Формируем клавиатуру профиля
        keyboard = get_profile_kb(user.is_admin, active_subs_count > 0, user.referral_bonus_days > 0)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        await message.answer(
            "Произошла ошибка при получении профиля. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )

@router.callback_query(F.data == "show_referral")
async def on_show_referral(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку "Реферальная программа" в профиле
    Перенаправляет на основной обработчик реферальной системы
    """
    from .referral import cmd_referral
    await cmd_referral(callback.message, user)
    await callback.answer() 