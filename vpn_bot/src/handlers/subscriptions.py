from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..database import User
from ..services import VPNService, PaymentService
from ..keyboards import (
    get_user_keyboard, get_subscription_keyboard,
    get_callback_keyboard, get_payment_keyboard
)


router = Router()


@router.message(Command("subscriptions"))
@router.message(F.text == "🔑 Мои подписки")
async def cmd_subscriptions(message: Message, user: User, vpn_service: VPNService):
    """Обработчик команды /subscriptions"""
    # Получаем подписки пользователя
    subscriptions = await vpn_service.get_user_subscriptions(user.user_id)
    
    if not subscriptions:
        # Если подписок нет, сообщаем об этом
        await message.answer(
            "У вас пока нет активных подписок. Для покупки VPN нажмите '💰 Купить VPN'."
        )
        return
    
    # Отправляем список подписок с клавиатурой
    await message.answer(
        "🔑 <b>Ваши подписки:</b>\n"
        "(Выберите подписку для управления)",
        reply_markup=get_user_keyboard(subscriptions),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("subscription:details:"))
async def subscription_details(callback: CallbackQuery, user: User, vpn_service: VPNService):
    """Обработчик запроса деталей подписки"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Получаем подписки пользователя
    subscriptions = await vpn_service.get_user_subscriptions(user.user_id)
    
    # Находим подписку по ID
    subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
    
    if not subscription:
        await callback.answer("⚠️ Подписка не найдена.", show_alert=True)
        return
    
    # Формируем текст с информацией о подписке
    status_emoji = "✅" if subscription["status"] == "active" else "⏳"
    
    text = (
        f"{status_emoji} <b>Подписка #{subscription['subscription_id']}</b>\n\n"
        f"📋 Тариф: {subscription['tariff_name']}\n"
        f"🗓 Дата окончания: {subscription['end_date'][:10]}\n"
        f"⏱ Осталось дней: {subscription['days_left']}\n"
    )
    
    # Добавляем статистику по трафику, если она доступна
    if "total_traffic_gb" in subscription:
        text += (
            f"\n📊 <b>Статистика:</b>\n"
            f"⬆️ Отправлено: {subscription['upload_traffic_gb']} ГБ\n"
            f"⬇️ Получено: {subscription['download_traffic_gb']} ГБ\n"
            f"🔄 Всего: {subscription['total_traffic_gb']} ГБ\n"
        )
        
        if subscription['total_limit_gb'] != "∞":
            text += f"💾 Осталось: {subscription['remaining_traffic_gb']} ГБ\n"
        else:
            text += f"💾 Лимит трафика: {subscription['total_limit_gb']}\n"
    
    # Отправляем информацию о подписке с клавиатурой для управления
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_keyboard(subscription),
        parse_mode="HTML"
    )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:url:"))
async def subscription_url(callback: CallbackQuery, user: User, vpn_service: VPNService):
    """Обработчик запроса ссылки на подписку"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Получаем подписки пользователя
    subscriptions = await vpn_service.get_user_subscriptions(user.user_id)
    
    # Находим подписку по ID
    subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
    
    if not subscription or not subscription.get("subscription_url"):
        await callback.answer("⚠️ Ссылка для подключения недоступна.", show_alert=True)
        return
    
    # Отправляем ссылку для подключения в отдельном сообщении
    await callback.message.answer(
        f"🔗 <b>Ссылка для подключения:</b>\n\n"
        f"<code>{subscription['subscription_url']}</code>\n\n"
        f"Используйте эту ссылку для настройки VPN в клиенте. "
        f"Для получения инструкции нажмите '💻 Инструкция'.",
        parse_mode="HTML"
    )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:renew:"))
async def subscription_renew(
    callback: CallbackQuery, user: User, vpn_service: VPNService, 
    payment_service: PaymentService, state: FSMContext
):
    """Обработчик запроса на продление подписки"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Получаем подписки пользователя
    subscriptions = await vpn_service.get_user_subscriptions(user.user_id)
    
    # Находим подписку по ID
    subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
    
    if not subscription:
        await callback.answer("⚠️ Подписка не найдена.", show_alert=True)
        return
    
    # Получаем URL для перенаправления после оплаты
    # В реальном боте здесь будет URL с параметрами для проверки оплаты
    redirect_url = "https://t.me/your_bot_username"
    
    # Создаем платеж
    payment_data = await payment_service.create_payment(
        user_id=user.user_id,
        tariff_id=subscription["tariff_id"],
        redirect_url=redirect_url,
        subscription_id=subscription_id,
        description=f"Продление подписки на тариф {subscription['tariff_name']}"
    )
    
    if not payment_data:
        await callback.answer("⚠️ Не удалось создать платеж. Попробуйте позже.", show_alert=True)
        return
    
    # Сохраняем ID платежа и подписки в состоянии
    await state.update_data(
        payment_id=payment_data["payment_id"],
        subscription_id=subscription_id
    )
    
    # Отправляем сообщение с информацией о платеже и кнопкой для оплаты
    await callback.message.edit_text(
        f"💳 <b>Продление подписки #{subscription_id}</b>\n\n"
        f"Тариф: {subscription['tariff_name']}\n"
        f"Сумма к оплате: {payment_data['amount']} руб.\n\n"
        f"Для оплаты нажмите кнопку ниже. После успешной оплаты ваша подписка будет продлена "
        f"автоматически.",
        reply_markup=get_payment_keyboard(payment_data["payment_url"]),
        parse_mode="HTML"
    )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:cancel:"))
async def subscription_cancel(callback: CallbackQuery, user: User):
    """Обработчик запроса на отмену подписки"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Запрашиваем подтверждение отмены подписки
    await callback.message.edit_text(
        f"⚠️ <b>Отмена подписки #{subscription_id}</b>\n\n"
        f"Вы действительно хотите отменить подписку? "
        f"После отмены доступ к VPN будет прекращен.",
        reply_markup=get_callback_keyboard("cancel_subscription", subscription_id),
        parse_mode="HTML"
    )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:cancel_subscription:"))
async def confirm_subscription_cancel(callback: CallbackQuery, user: User, vpn_service: VPNService):
    """Обработчик подтверждения отмены подписки"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Отменяем подписку
    success = await vpn_service.cancel_subscription(subscription_id)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Подписка #{subscription_id} успешно отменена.</b>\n\n"
            f"Доступ к VPN прекращен.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Не удалось отменить подписку #{subscription_id}.</b>\n\n"
            f"Пожалуйста, обратитесь в службу поддержки.",
            parse_mode="HTML"
        )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:cancel_subscription:"))
async def cancel_subscription_cancel(callback: CallbackQuery, user: User, vpn_service: VPNService):
    """Обработчик отмены отмены подписки"""
    # Извлекаем ID подписки из callback data
    subscription_id = int(callback.data.split(":")[-1])
    
    # Получаем подписки пользователя
    subscriptions = await vpn_service.get_user_subscriptions(user.user_id)
    
    # Находим подписку по ID
    subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
    
    if not subscription:
        await callback.answer("⚠️ Подписка не найдена.", show_alert=True)
        return
    
    # Возвращаемся к информации о подписке
    status_emoji = "✅" if subscription["status"] == "active" else "⏳"
    
    text = (
        f"{status_emoji} <b>Подписка #{subscription['subscription_id']}</b>\n\n"
        f"📋 Тариф: {subscription['tariff_name']}\n"
        f"🗓 Дата окончания: {subscription['end_date'][:10]}\n"
        f"⏱ Осталось дней: {subscription['days_left']}\n"
    )
    
    # Добавляем статистику по трафику, если она доступна
    if "total_traffic_gb" in subscription:
        text += (
            f"\n📊 <b>Статистика:</b>\n"
            f"⬆️ Отправлено: {subscription['upload_traffic_gb']} ГБ\n"
            f"⬇️ Получено: {subscription['download_traffic_gb']} ГБ\n"
            f"🔄 Всего: {subscription['total_traffic_gb']} ГБ\n"
        )
        
        if subscription['total_limit_gb'] != "∞":
            text += f"💾 Осталось: {subscription['remaining_traffic_gb']} ГБ\n"
        else:
            text += f"💾 Лимит трафика: {subscription['total_limit_gb']}\n"
    
    # Отправляем информацию о подписке с клавиатурой для управления
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_keyboard(subscription),
        parse_mode="HTML"
    )
    
    # Убираем уведомление о нажатии кнопки
    await callback.answer() 