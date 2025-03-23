"""
Обработчики для управления пробным периодом
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from ..models.user import User
from ..models.tariff import Tariff
from ..models.subscription import Subscription
from ..models.cluster import get_optimal_server
from ..exceptions import DatabaseError, VPNServerError
from ..middleware import AuthMiddleware
from ..keyboards.trial import get_trial_kb

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("trial"))
async def cmd_trial(message: Message, user: User):
    """
    Обработчик команды для получения пробного периода
    """
    try:
        # Проверяем, использовал ли пользователь уже пробный период
        if user.has_used_trial:
            await message.answer(
                "Вы уже использовали пробный период. Чтобы продолжить пользоваться нашим VPN, "
                "пожалуйста, приобретите подписку с помощью команды /buy"
            )
            return
        
        # Проверяем, есть ли у пользователя активные подписки
        active_subs = await user.get_subscriptions(active_only=True)
        if active_subs:
            await message.answer(
                "У вас уже есть активная подписка. Пробный период доступен только для новых пользователей."
            )
            return
        
        # Получаем или создаем пробный тариф
        trial_tariff = await Tariff.get_trial_tariff()
        if not trial_tariff:
            trial_tariff = await Tariff.create_default_trial()
        
        # Отправляем сообщение с информацией о пробном периоде
        text = f"🎁 <b>Бесплатный пробный период</b>\n\n"
        text += f"{trial_tariff.description}\n\n"
        text += f"⏳ Длительность: {trial_tariff.duration} дней\n"
        
        if trial_tariff.traffic_limit:
            text += f"📊 Лимит трафика: {trial_tariff.traffic_limit} ГБ\n"
        else:
            text += "📊 Трафик: Безлимитный\n"
            
        text += f"📱 Устройств: {trial_tariff.devices}\n\n"
        
        text += "Нажмите кнопку ниже, чтобы активировать пробный период."
        
        # Создаем клавиатуру с кнопкой активации пробного периода
        keyboard = get_trial_kb(trial_tariff.id)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in trial command: {e}")
        await message.answer(
            "Произошла ошибка при получении информации о пробном периоде. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )


@router.callback_query(F.data.startswith("activate_trial:"))
async def on_activate_trial(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку активации пробного периода
    """
    try:
        # Извлекаем ID тарифа из данных колбэка
        tariff_id = int(callback.data.split(":")[1])
        
        # Проверяем, использовал ли пользователь уже пробный период
        if user.has_used_trial:
            await callback.answer("Вы уже использовали пробный период", show_alert=True)
            return
        
        # Получаем тариф
        trial_tariff = await Tariff.get(tariff_id)
        
        # Проверяем, является ли тариф пробным
        if not trial_tariff.is_trial:
            await callback.answer("Указанный тариф не является пробным", show_alert=True)
            return
        
        # Выбираем оптимальный сервер
        server = await get_optimal_server()
        if not server:
            await callback.answer(
                "В данный момент нет доступных серверов. Пожалуйста, попробуйте позже.",
                show_alert=True
            )
            return
        
        # Создаем VPN аккаунт на сервере
        account_info = await server.create_vpn_account(
            email=f"trial_{user.id}@vpnbot.com",
            duration_days=trial_tariff.duration
        )
        
        # Создаем подписку
        subscription = await Subscription.create(
            user_id=user.id,
            tariff_id=trial_tariff.id,
            days=trial_tariff.duration,
            traffic_limit=int(trial_tariff.traffic_limit * 1024) if trial_tariff.traffic_limit else 0,
            max_devices=trial_tariff.devices,
            server_id=server.id,
            cluster_id=server.cluster_id,
            vpn_uuid=account_info["uuid"]
        )
        
        # Отмечаем, что пользователь использовал пробный период
        await user.set_trial_used()
        
        # Отправляем сообщение с информацией о подписке
        text = f"✅ <b>Пробный период успешно активирован!</b>\n\n"
        text += f"🕒 Срок действия: {trial_tariff.duration} дней\n"
        text += f"📅 Истекает: {subscription.end_date.strftime('%d.%m.%Y %H:%M')}\n"
        
        if trial_tariff.traffic_limit:
            text += f"📊 Лимит трафика: {trial_tariff.traffic_limit} ГБ\n"
        else:
            text += "📊 Трафик: Безлимитный\n"
            
        text += f"🖥 Сервер: {server.name} ({server.country})\n\n"
        
        text += "Чтобы настроить VPN на вашем устройстве, используйте команду /instructions\n"
        text += "Для просмотра ваших активных подписок используйте команду /subscriptions"
        
        await callback.message.edit_text(text)
        await callback.answer("Пробный период успешно активирован!")
        
    except Exception as e:
        logger.error(f"Error activating trial: {e}")
        await callback.answer(
            "Произошла ошибка при активации пробного периода. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.", 
            show_alert=True
        )


@router.message(Command("reset_trial"))
async def cmd_reset_trial_admin(message: Message, user: User):
    """
    Административная команда для сброса пробного периода пользователя
    (доступна только администраторам)
    """
    if not user.is_admin:
        return
    
    # Проверяем, есть ли в сообщении упоминание пользователя или ID
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.answer(
            "Использование: /reset_trial <user_id>\n"
            "Например: /reset_trial 123456789"
        )
        return
    
    try:
        # Получаем ID пользователя
        target_user_id = int(command_parts[1])
        
        # Получаем пользователя
        target_user = await User.get(target_user_id)
        
        # Сбрасываем флаг использования пробного периода
        target_user.has_used_trial = False
        await target_user.save()
        
        await message.answer(
            f"✅ Пробный период для пользователя {target_user_id} успешно сброшен.\n"
            f"Теперь пользователь может снова активировать пробный период."
        )
        
    except ValueError:
        await message.answer("Некорректный ID пользователя. Укажите числовой ID.")
    except Exception as e:
        logger.error(f"Error resetting trial: {e}")
        await message.answer(f"Ошибка при сбросе пробного периода: {str(e)}") 