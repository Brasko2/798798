"""
Обработчики для покупки VPN-подписок с красивым оформлением сообщений и лучшим пользовательским опытом
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime

from ..models.user import User
from ..models.tariff import Tariff
from ..models.payment import Payment
from ..models.subscription import Subscription
from ..keyboards.buy import get_tariff_selection_kb, get_payment_kb, get_payment_success_kb
from ..services.payment_service import payment_service
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("buy"))
@router.message(F.text == "🚀 Купить VPN")
async def cmd_buy(message: Message, user: User):
    """
    Обработчик команды /buy и кнопки 'Купить VPN'
    Отображает список доступных тарифов
    """
    try:
        # Получаем список активных тарифов
        tariffs = await Tariff.get_active()
        
        if not tariffs:
            await message.answer(
                "😔 <b>К сожалению, в данный момент нет доступных тарифов.</b>\n\n"
                "Пожалуйста, попробуйте позже или обратитесь в поддержку."
            )
            return
        
        # Формируем красивое сообщение с предложением тарифов
        text = "🚀 <b>ПРЕМИУМ VPN-ДОСТУП</b>\n\n"
        text += "Выберите подходящий вам тарифный план:\n\n"
        
        # Добавляем описание каждого тарифа
        for idx, tariff in enumerate(tariffs, 1):
            # Определяем эмодзи на основе типа тарифа
            if tariff.is_trial:
                emoji = "🎁"  # Пробный тариф
            elif tariff.price < 300:
                emoji = "🔹"  # Базовый тариф
            elif tariff.price < 700:
                emoji = "🔶"  # Стандартный тариф
            else:
                emoji = "💎"  # Премиум тариф
                
            # Форматируем цену
            price_text = f"{tariff.price:.0f}" if tariff.price == int(tariff.price) else f"{tariff.price:.2f}"
            
            # Добавляем информацию о тарифе
            text += f"{emoji} <b>{tariff.name}</b> — {price_text}₽\n"
            text += f"    ✓ {tariff.duration_days} дней доступа\n"
            text += f"    ✓ До {tariff.max_devices} {'устройств' if tariff.max_devices > 1 else 'устройства'}\n"
            
            # Добавляем информацию о трафике, если он ограничен
            if tariff.traffic_limit_mb > 0:
                traffic_gb = tariff.traffic_limit_mb / 1024
                text += f"    ✓ {traffic_gb:.1f} ГБ трафика\n"
            else:
                text += f"    ✓ Безлимитный трафик\n"
                
            # Добавляем описание тарифа, если оно есть
            if tariff.description:
                text += f"    {tariff.description}\n"
                
            text += "\n"
            
        text += "🛡️ <b>Все тарифы включают:</b>\n"
        text += "• Полную анонимность и безопасность\n"
        text += "• Высокую скорость соединения\n"
        text += "• Доступ к любым сайтам и сервисам\n"
        text += "• Бесплатную поддержку 24/7\n\n"
        
        text += "👇 <b>Выберите тариф из списка ниже:</b>"
        
        # Отправляем сообщение с клавиатурой выбора тарифа
        await message.answer(
            text,
            reply_markup=get_tariff_selection_kb(tariffs)
        )
        
    except Exception as e:
        logger.error(f"Error in buy command: {e}")
        await message.answer(
            "🙁 Произошла ошибка при получении тарифов. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )


@router.callback_query(F.data.startswith("tariff:"))
async def on_tariff_selected(callback: CallbackQuery, user: User):
    """
    Обработчик выбора тарифа
    Создает платеж и отправляет информацию об оплате
    """
    try:
        # Получаем ID выбранного тарифа
        tariff_id = int(callback.data.split(":")[1])
        
        # Получаем тариф из базы данных
        tariff = await Tariff.get_by_id(tariff_id)
        
        if not tariff:
            await callback.answer("Выбранный тариф больше не доступен", show_alert=True)
            return
        
        # Создаем платеж
        payment = await payment_service.create_payment(user.id, tariff.id, tariff.price)
        
        if not payment:
            await callback.answer("Не удалось создать платеж. Попробуйте позже.", show_alert=True)
            return
        
        # Формируем сообщение о платеже с приятным дизайном
        text = "💳 <b>ИНФОРМАЦИЯ ОБ ОПЛАТЕ</b>\n\n"
        text += f"📦 <b>Тариф:</b> {tariff.name}\n"
        text += f"⏱️ <b>Период:</b> {tariff.duration_days} дней\n"
        text += f"💻 <b>Устройств:</b> до {tariff.max_devices}\n"
        
        # Добавляем информацию о трафике, если он ограничен
        if tariff.traffic_limit_mb > 0:
            traffic_gb = tariff.traffic_limit_mb / 1024
            text += f"📊 <b>Трафик:</b> {traffic_gb:.1f} ГБ\n"
        else:
            text += "📊 <b>Трафик:</b> Безлимитный\n"
            
        text += f"💰 <b>Сумма к оплате:</b> {tariff.price:.2f}₽\n\n"
        
        text += "🔄 <b>Статус платежа:</b> Ожидает оплаты\n\n"
        
        text += "👉 Для оплаты нажмите кнопку «Перейти к оплате»\n"
        text += "⚠️ После оплаты нажмите «Проверить оплату»\n\n"
        
        text += "<i>Платеж действителен в течение 30 минут</i>"
        
        # Отправляем сообщение с инструкциями по оплате
        await callback.message.edit_text(
            text,
            reply_markup=get_payment_kb(payment.payment_url)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in tariff selection: {e}")
        await callback.answer("Произошла ошибка при обработке тарифа", show_alert=True)


@router.callback_query(F.data == "check_payment")
async def on_check_payment(callback: CallbackQuery, user: User):
    """
    Обработчик проверки платежа
    Проверяет статус платежа и создает подписку, если платеж успешен
    """
    try:
        # Получаем последний неоплаченный платеж пользователя
        payment = await Payment.get_latest_pending(user.id)
        
        if not payment:
            await callback.answer("Активных платежей не найдено", show_alert=True)
            return
        
        # Проверяем статус платежа
        payment_status = await payment_service.check_payment(payment.payment_id)
        
        # Обрабатываем различные статусы платежа
        if payment_status == "succeeded":
            # Платеж успешен, обновляем статус и создаем подписку
            await payment.set_paid()
            
            # Получаем тариф
            tariff = await Tariff.get_by_id(payment.tariff_id)
            
            # Создаем подписку
            subscription = await Subscription.create(
                user_id=user.id,
                tariff_id=tariff.id,
                payment_id=payment.id,
                duration_days=tariff.duration_days,
                max_devices=tariff.max_devices,
                traffic_limit_mb=tariff.traffic_limit_mb
            )
            
            # Формируем сообщение об успешной оплате
            text = "✅ <b>ОПЛАТА УСПЕШНО ЗАВЕРШЕНА!</b>\n\n"
            text += f"🎉 Поздравляем! Вы приобрели тариф <b>{tariff.name}</b>\n\n"
            text += f"📆 <b>Срок действия:</b> {subscription.expires_at.strftime('%d.%m.%Y')}\n"
            text += f"🔑 <b>ID подписки:</b> {subscription.id}\n\n"
            
            text += "📲 <b>ЧТО ДАЛЬШЕ?</b>\n"
            text += "1. Перейдите в раздел «Мои подписки»\n"
            text += "2. Получите конфигурацию для вашего устройства\n"
            text += "3. Следуйте инструкциям по настройке\n\n"
            
            text += "💡 <b>Совет:</b> В разделе «Инструкции по настройке» вы найдете подробное руководство для всех устройств."
            
            # Отправляем сообщение с успешной оплатой
            await callback.message.edit_text(
                text,
                reply_markup=get_payment_success_kb()
            )
            
        elif payment_status == "pending":
            # Платеж в обработке
            await callback.answer("Платеж находится в обработке. Пожалуйста, подождите.", show_alert=True)
            
        elif payment_status == "canceled":
            # Платеж отменен
            await payment.set_canceled()
            
            text = "❌ <b>ПЛАТЕЖ ОТМЕНЕН</b>\n\n"
            text += "Ваш платеж был отменен.\n"
            text += "Вы можете попробовать снова или выбрать другой способ оплаты.\n\n"
            text += "Если вы столкнулись с проблемами, обратитесь в нашу службу поддержки."
            
            await callback.message.edit_text(
                text,
                reply_markup=get_tariff_selection_kb(await Tariff.get_active())
            )
            
        else:
            # Неизвестный статус платежа
            await callback.answer("Не удалось определить статус платежа. Пожалуйста, попробуйте позже.", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await callback.answer("Произошла ошибка при проверке платежа", show_alert=True)


@router.callback_query(F.data == "cancel_payment")
async def on_cancel_payment(callback: CallbackQuery, user: User):
    """
    Обработчик отмены платежа
    Отменяет текущий платеж и возвращает к выбору тарифа
    """
    try:
        # Получаем последний неоплаченный платеж пользователя
        payment = await Payment.get_latest_pending(user.id)
        
        if payment:
            # Отмечаем платеж как отмененный
            await payment.set_canceled()
        
        # Показываем тарифы снова
        await cmd_buy(callback.message, user)
        await callback.answer("Платеж отменен")
        
    except Exception as e:
        logger.error(f"Error canceling payment: {e}")
        await callback.answer("Произошла ошибка при отмене платежа", show_alert=True) 