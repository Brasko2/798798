"""
Middleware для авторизации пользователей в боте
"""
import logging
from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from ..models import User
from ..database import db
from ..exceptions import DatabaseError


logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для авторизации пользователей
    
    Проверяет, зарегистрирован ли пользователь в базе данных.
    Если нет, то создает нового пользователя.
    Добавляет объект пользователя в контекст обработчика.
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        """
        Основной метод middleware
        
        Проверяет наличие пользователя в базе данных и добавляет его в контекст.
        Если пользователя нет, то создает нового.
        """
        user = None
        
        # Получаем данные пользователя в зависимости от типа события
        if isinstance(event, Message):
            user_data = event.from_user
        elif isinstance(event, CallbackQuery):
            user_data = event.from_user
        else:
            # Если тип события не поддерживается, пропускаем middleware
            return await handler(event, data)
        
        try:
            # Пытаемся найти пользователя в базе данных
            user = await User.get_by_telegram_id(user_data.id)
            
            # Если пользователь не найден, создаем нового
            if not user:
                logger.info(f"Creating new user: {user_data.id} - {user_data.username}")
                
                # Получаем ID для нового пользователя
                
                # Подготавливаем данные пользователя
                new_user_data = {
                    "telegram_id": user_data.id,
                    "username": user_data.username,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "language_code": user_data.language_code,
                    "is_premium": getattr(user_data, "is_premium", False),
                }
                
                # Создаем нового пользователя
                user = await User.create(new_user_data)
                logger.info(f"New user created: {user.id} - {user.username}")
            
            # Добавляем пользователя в данные контекста
            data["user"] = user
            
            # Проверяем, не заблокирован ли пользователь
            if not user.is_active:
                if isinstance(event, Message):
                    await event.answer(
                        "⛔ Ваш аккаунт заблокирован. Для разблокировки обратитесь в поддержку."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⛔ Ваш аккаунт заблокирован. Для разблокировки обратитесь в поддержку.",
                        show_alert=True
                    )
                return
            
            # Вызываем следующий обработчик
            return await handler(event, data)
        
        except DatabaseError as e:
            # Логируем ошибку
            logger.error(f"Database error in auth middleware: {e}")
            
            # Отправляем сообщение об ошибке
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Произошла ошибка при работе с базой данных. Пожалуйста, попробуйте позже."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Произошла ошибка при работе с базой данных. Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
            
            # Прекращаем обработку запроса
            return
        
        except Exception as e:
            # Логируем ошибку
            logger.error(f"Unexpected error in auth middleware: {e}", exc_info=True)
            
            # Отправляем сообщение об ошибке
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Произошла неизвестная ошибка. Пожалуйста, попробуйте позже."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Произошла неизвестная ошибка. Пожалуйста, попробуйте позже.",
                    show_alert=True
                )
            
            # Прекращаем обработку запроса
            return 