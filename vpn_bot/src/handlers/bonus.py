"""
Обработчики для бонусов и акций VPN сервиса
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime

from ..models.user import User
from ..keyboards.bonus import get_bonus_keyboard, get_back_to_bonus_keyboard
from ..keyboards.main import get_back_to_main_keyboard
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("bonus"))
@router.message(F.text == "💫 Бонусы и акции")
async def cmd_bonus(message: Message, user: User):
    """
    Обработчик команды /bonus и кнопки 'Бонусы и акции'
    Показывает доступные бонусы и акции
    """
    try:
        text = "💫 <b>БОНУСЫ И АКЦИИ</b>\n\n"
        
        # Проверяем доступные бонусы пользователя
        has_bonus_days = user.referral_bonus_days > 0
        
        text += "🎁 <b>Текущие бонусы:</b>\n"
        if has_bonus_days:
            text += f"• У вас есть <b>{user.referral_bonus_days}</b> бонусных дней по реферальной программе!\n"
            text += "  <i>Используйте их для продления своей подписки</i>\n\n"
        else:
            text += "• Сейчас у вас нет накопленных бонусных дней\n"
            text += "  <i>Приглашайте друзей по реферальной программе, чтобы получить бонусные дни</i>\n\n"
        
        # Проверяем наличие активных акций
        now = datetime.now()
        is_new_year = now.month == 12 and now.day >= 20 or now.month == 1 and now.day <= 10
        is_spring = now.month == 3 and now.day >= 1 and now.day <= 10
        
        text += "🔥 <b>Специальные предложения:</b>\n"
        
        if is_new_year:
            text += "• 🎄 <b>Новогодняя акция!</b> Скидка 20% на все тарифы до 10 января\n"
            text += "  <i>Скидка применяется автоматически при покупке</i>\n\n"
        elif is_spring:
            text += "• 🌷 <b>Весенняя акция!</b> Скидка 15% на тарифы от 3 месяцев до 10 марта\n"
            text += "  <i>Скидка применяется автоматически при покупке</i>\n\n"
        else:
            text += "• В данный момент нет активных акций. Следите за обновлениями!\n\n"
        
        text += "🔄 <b>Постоянные бонусы:</b>\n"
        text += "• <b>Реферальная программа:</b> Приглашайте друзей и получайте до 30 дней бесплатного VPN\n"
        text += "• <b>Длительные подписки:</b> Чем дольше срок подписки, тем выгоднее цена за месяц\n"
        text += "• <b>Бонус за отзыв:</b> Получите 7 дней бесплатно за отзыв о нашем сервисе\n\n"
        
        text += "💡 <i>Нажмите на соответствующую кнопку ниже, чтобы узнать подробности</i>"
        
        await message.answer(
            text,
            reply_markup=get_bonus_keyboard(has_bonus_days=has_bonus_days)
        )
    except Exception as e:
        logger.error(f"Error in bonus command: {e}")
        await message.answer(
            "Произошла ошибка при получении информации о бонусах. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )


@router.callback_query(F.data == "bonus")
async def on_bonus_button(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку бонусов в других меню
    """
    try:
        await cmd_bonus(callback.message, user)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error handling bonus button: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "bonus:referral")
async def on_referral_bonus_info(callback: CallbackQuery, user: User):
    """
    Показывает информацию о реферальной программе
    """
    try:
        text = "👥 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        
        text += "Приглашайте друзей и получайте бонусы!\n\n"
        
        text += "<b>Как это работает:</b>\n"
        text += "1. Поделитесь своей реферальной ссылкой с друзьями\n"
        text += "2. Когда ваш друг регистрируется по ссылке, вы становитесь его реферером\n"
        text += "3. Когда ваш друг оплачивает подписку, вы получаете бонусные дни:\n"
        text += "   • 7 дней бонуса при покупке другом месячной подписки\n"
        text += "   • 15 дней бонуса при покупке другом 3-месячной подписки\n"
        text += "   • 30 дней бонуса при покупке другом 6-месячной или годовой подписки\n\n"
        
        text += "<b>Ваша реферальная ссылка:</b>\n"
        text += f"<code>https://t.me/your_bot_username?start={user.referral_code}</code>\n\n"
        
        text += "<b>Статистика:</b>\n"
        text += f"• Приглашено пользователей: {user.referral_count}\n"
        text += f"• Накоплено бонусных дней: {user.referral_bonus_days}\n\n"
        
        text += "💡 <i>Бонусные дни можно использовать для продления любой активной подписки</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_bonus_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing referral bonus info: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "bonus:review")
async def on_review_bonus_info(callback: CallbackQuery, user: User):
    """
    Показывает информацию о бонусе за отзыв
    """
    try:
        text = "⭐ <b>БОНУС ЗА ОТЗЫВ</b>\n\n"
        
        text += "Поделитесь своим опытом использования нашего VPN и получите 7 дней бесплатно!\n\n"
        
        text += "<b>Как получить бонус:</b>\n"
        text += "1. Оставьте честный отзыв о нашем сервисе в одном из следующих мест:\n"
        text += "   • В нашем телеграм-канале @vpn_channel\n"
        text += "   • На сайте trustpilot.com\n"
        text += "   • В AppStore или Google Play (если используете мобильное приложение)\n\n"
        
        text += "2. Отправьте скриншот или ссылку на отзыв в поддержку с пометкой «Бонус за отзыв»\n\n"
        
        text += "3. После проверки модератором, бонусные дни будут начислены на ваш аккаунт\n\n"
        
        text += "⚠️ <i>Бонус предоставляется только за развернутые и конструктивные отзывы. Отзыв должен содержать не менее 3-4 предложений с описанием вашего опыта использования сервиса.</i>\n\n"
        
        text += "💬 <i>Для отправки скриншота отзыва, воспользуйтесь кнопкой «Поддержка» в главном меню</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_bonus_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing review bonus info: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "bonus:loyalty")
async def on_loyalty_bonus_info(callback: CallbackQuery, user: User):
    """
    Показывает информацию о программе лояльности
    """
    try:
        text = "🔄 <b>ПРОГРАММА ЛОЯЛЬНОСТИ</b>\n\n"
        
        text += "Мы ценим наших постоянных клиентов и предлагаем выгодные условия для длительных подписок!\n\n"
        
        text += "<b>Преимущества длительных подписок:</b>\n"
        text += "• <b>3 месяца:</b> Экономия 15% по сравнению с месячной оплатой\n"
        text += "• <b>6 месяцев:</b> Экономия 25% по сравнению с месячной оплатой\n"
        text += "• <b>12 месяцев:</b> Экономия 40% по сравнению с месячной оплатой + приоритетная поддержка\n\n"
        
        text += "<b>Постоянные клиенты получают:</b>\n"
        text += "• Скидки на продление подписки\n"
        text += "• Приоритетную техническую поддержку\n"
        text += "• Возможность тестирования новых функций\n"
        text += "• Персональные предложения и акции\n\n"
        
        text += "💡 <i>Чем дольше вы с нами, тем больше привилегий получаете!</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_bonus_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing loyalty bonus info: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "bonus:apply")
async def on_apply_bonus(callback: CallbackQuery, user: User):
    """
    Обработчик применения бонусных дней к активной подписке
    """
    from ..models.subscription import Subscription
    
    try:
        # Проверяем наличие бонусных дней
        if user.referral_bonus_days <= 0:
            await callback.answer("У вас нет накопленных бонусных дней", show_alert=True)
            return
        
        # Проверяем наличие активной подписки
        active_subscriptions = await Subscription.get_active_by_user_id(user.user_id)
        
        if not active_subscriptions:
            await callback.message.edit_text(
                "⚠️ <b>У вас нет активных подписок</b>\n\n"
                "Для использования бонусных дней необходимо иметь активную подписку.\n"
                "Приобретите подписку в разделе «Купить VPN».",
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        # Если есть только одна активная подписка, применяем бонус к ней
        subscription = active_subscriptions[0]
        
        # Обновляем дату окончания подписки
        days_to_add = user.referral_bonus_days
        await subscription.extend_days(days_to_add)
        
        # Обнуляем бонусные дни пользователя
        user.referral_bonus_days = 0
        await user.save()
        
        # Отправляем сообщение об успешном применении бонуса
        await callback.message.edit_text(
            f"✅ <b>Бонус успешно применен!</b>\n\n"
            f"<b>{days_to_add}</b> бонусных дней добавлено к вашей подписке.\n\n"
            f"Новая дата окончания подписки: <b>{subscription.end_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"Благодарим за использование нашего сервиса!",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer("Бонус успешно применен!")
    except Exception as e:
        logger.error(f"Error applying bonus: {e}")
        await callback.answer("Произошла ошибка при применении бонуса", show_alert=True) 