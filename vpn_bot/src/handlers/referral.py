"""
Обработчики для реферальной системы
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging
from datetime import datetime

from ..models.user import User
from ..models.subscription import Subscription
from ..keyboards.referral import get_referral_keyboard, get_referral_stats_kb, get_referral_apply_bonus_kb, get_bonus_days_keyboard, get_referrer_keyboard
from ..middleware import AuthMiddleware
from ..exceptions import DatabaseError

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("referral"))
async def cmd_referral(message: Message, user: User):
    """
    Обработчик команды /referral - основная команда реферальной системы
    Показывает информацию о реферальной программе, реферальный код и статистику
    """
    try:
        # Формируем сообщение с информацией о реферальной программе
        text = "🔗 <b>Реферальная программа</b>\n\n"
        text += "Приглашайте друзей в наш VPN-сервис и получайте бонусы!\n\n"
        
        text += "🎁 <b>Ваши бонусы:</b>\n"
        text += "• <b>3 дня</b> бесплатного VPN за каждого приглашенного друга\n"
        text += "• <b>1 день</b> дополнительно за каждого, кого пригласит ваш друг\n\n"
        
        # Добавляем информацию о реферальном коде пользователя
        text += f"🔑 <b>Ваш реферальный код:</b> <code>{user.referral_code}</code>\n\n"
        
        # Добавляем реферальную ссылку
        bot_username = (await message.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"
        text += f"🔗 <b>Ваша реферальная ссылка:</b>\n<code>{referral_link}</code>\n\n"
        
        # Статистика
        text += f"👥 <b>Ваша статистика:</b>\n"
        text += f"• Приглашено друзей: {user.referral_count}\n"
        text += f"• Бонусные дни: {user.referral_bonus_days}\n"
        
        # Если есть бонусные дни, добавляем информацию о том, как их использовать
        if user.referral_bonus_days > 0:
            text += "\nНажмите кнопку «Применить бонус», чтобы добавить бонусные дни к вашей активной подписке."
        
        # Отправляем сообщение с клавиатурой действий
        await message.answer(
            text,
            reply_markup=get_referral_keyboard(user.referral_bonus_days > 0)
        )
        
    except Exception as e:
        logger.error(f"Error in referral command: {e}")
        await message.answer(
            "Произошла ошибка при получении информации о реферальной программе. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )


@router.message(Command("start"))
async def cmd_start_with_referral(message: Message, user: User):
    """
    Обработчик команды /start с реферальным кодом
    Если пользователь новый и использовал чью-то реферальную ссылку,
    записываем реферера и выдаем бонус
    """
    # Проверяем, есть ли в команде /start параметр (реферальный код)
    command_parts = message.text.split()
    if len(command_parts) != 2:
        # Если нет параметра, это обычный /start, передаем управление стандартному обработчику
        return
    
    referral_code = command_parts[1]
    
    try:
        # Игнорируем, если это существующий пользователь, у которого уже есть реферер
        if user.referrer_id is not None:
            # Но продолжаем обработку команды /start
            return
        
        # Получаем пользователя по реферальному коду
        referrer = await User.get_by_referral_code(referral_code)
        
        # Проверяем, найден ли реферер и не является ли он тем же пользователем
        if referrer and referrer.id != user.id:
            # Устанавливаем реферера для пользователя
            user.referrer_id = referrer.id
            await user.save()
            
            # Увеличиваем счетчик рефералов и добавляем бонусные дни рефереру
            await User.increment_referral_count(referrer.id)
            
            # Отправляем уведомление пользователю
            await message.answer(
                f"🎁 Вы присоединились по приглашению пользователя и получите дополнительные бонусы "
                f"при покупке подписки!"
            )
            
            # Пытаемся отправить уведомление рефереру
            try:
                await message.bot.send_message(
                    chat_id=referrer.telegram_id,
                    text=f"🎉 Поздравляем! По вашей реферальной ссылке зарегистрировался новый пользователь.\n\n"
                         f"Вам начислено 3 бонусных дня! Используйте команду /referral, чтобы узнать подробности."
                )
            except Exception as notify_error:
                logger.error(f"Failed to notify referrer {referrer.id}: {notify_error}")
        
    except Exception as e:
        logger.error(f"Error processing referral code: {e}")
    
    # В любом случае продолжаем обработку команды /start
    return


@router.callback_query(F.data == "referral_stats")
async def on_referral_stats(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку статистики рефералов
    Показывает подробную статистику по реферальной программе
    """
    try:
        # Получаем список рефералов пользователя
        referrals = await user.get_referrals()
        
        text = "📊 <b>Статистика вашей реферальной программы</b>\n\n"
        text += f"🔑 Ваш реферальный код: <code>{user.referral_code}</code>\n\n"
        text += f"👥 Всего приглашено: {user.referral_count}\n"
        text += f"⏳ Бонусные дни: {user.referral_bonus_days}\n\n"
        
        if referrals:
            text += "<b>Список ваших рефералов:</b>\n"
            for i, ref in enumerate(referrals, 1):
                joined_date = ref.joined_at.strftime("%d.%m.%Y")
                text += f"{i}. {ref.full_name or ref.username or f'User {ref.id}'} (с {joined_date})\n"
        else:
            text += "У вас пока нет приглашенных пользователей. Поделитесь своей реферальной ссылкой с друзьями!"
        
        # Создаем клавиатуру для статистики
        keyboard = get_referral_stats_kb()
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing referral stats: {e}")
        await callback.answer("Ошибка при получении статистики", show_alert=True)


@router.callback_query(F.data == "apply_referral_bonus")
async def on_apply_referral_bonus(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку применения бонуса
    Позволяет пользователю применить накопленные бонусные дни к активной подписке
    """
    try:
        # Проверяем, есть ли у пользователя бонусные дни
        if user.referral_bonus_days <= 0:
            await callback.answer("У вас нет бонусных дней для применения", show_alert=True)
            return
        
        # Получаем активные подписки пользователя
        subscriptions = await user.get_subscriptions(active_only=True)
        
        if not subscriptions:
            await callback.answer(
                "У вас нет активных подписок. Приобретите подписку, чтобы использовать бонусные дни.",
                show_alert=True
            )
            return
        
        # Создаем клавиатуру для выбора количества дней
        keyboard = get_referral_apply_bonus_kb(user.referral_bonus_days)
        
        # Отправляем сообщение с выбором количества дней
        await callback.message.edit_text(
            f"⏳ <b>Применение бонусных дней</b>\n\n"
            f"У вас есть {user.referral_bonus_days} бонусных дней.\n"
            f"Выберите, сколько дней вы хотите добавить к вашей подписке:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error applying referral bonus: {e}")
        await callback.answer("Ошибка при применении бонуса", show_alert=True)


@router.callback_query(F.data.startswith("apply_days:"))
async def on_apply_days(callback: CallbackQuery, user: User):
    """
    Обработчик выбора количества дней для применения бонуса
    """
    try:
        # Извлекаем количество дней из данных колбэка
        days_to_apply = int(callback.data.split(":")[1])
        
        # Проверяем, достаточно ли у пользователя бонусных дней
        if days_to_apply > user.referral_bonus_days:
            await callback.answer("У вас недостаточно бонусных дней", show_alert=True)
            return
        
        # Применяем бонусные дни к подписке
        applied_days = await user.apply_referral_bonus_to_subscription(days_to_apply)
        
        if applied_days > 0:
            # Сообщаем об успешном применении бонуса
            await callback.message.edit_text(
                f"✅ Бонус успешно применен!\n\n"
                f"Вы добавили {applied_days} дней к вашей подписке.\n"
                f"Оставшиеся бонусные дни: {user.referral_bonus_days}",
                reply_markup=get_referral_keyboard(user.referral_bonus_days > 0)
            )
        else:
            await callback.answer("Не удалось применить бонус. Возможно, у вас нет активных подписок.", show_alert=True)
            
        await callback.answer()
        
    except ValueError:
        await callback.answer("Некорректное значение", show_alert=True)
    except Exception as e:
        logger.error(f"Error applying days: {e}")
        await callback.answer("Ошибка при применении бонусных дней", show_alert=True)


@router.callback_query(F.data == "share_referral")
async def on_share_referral(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку "Поделиться реферальной ссылкой"
    """
    try:
        bot_username = (await callback.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"
        
        text = "🔗 <b>Поделитесь своей реферальной ссылкой</b>\n\n"
        text += "Отправьте эту ссылку друзьям и получите бонусные дни за каждого нового пользователя!\n\n"
        text += f"<code>{referral_link}</code>\n\n"
        text += "Вы получите:\n"
        text += "• 3 дня бесплатного VPN за каждого приглашенного друга\n"
        text += "• 1 день дополнительно за каждого, кого пригласит ваш друг"
        
        await callback.message.edit_text(text, reply_markup=get_referral_stats_kb())
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error sharing referral link: {e}")
        await callback.answer("Ошибка при формировании реферальной ссылки", show_alert=True)


@router.callback_query(F.data == "back_to_referral")
async def on_back_to_referral(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку возврата к основному меню рефералов
    """
    await cmd_referral(callback.message, user)
    await callback.answer() 