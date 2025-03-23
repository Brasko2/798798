from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from ..database.models import User
from ..database.db import Database
from ..settings import settings


class AuthMiddleware(BaseMiddleware):
    def __init__(self, database: Database):
        self.db = database
        
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        # Получаем данные пользователя из сообщения или колбэка
        if isinstance(event, Message):
            user_data = event.from_user
        elif isinstance(event, CallbackQuery):
            user_data = event.from_user
        else:
            # Если не можем получить пользователя, пропускаем обработку middleware
            return await handler(event, data)
        
        # Проверяем, является ли пользователь администратором
        is_admin = user_data.id in settings.ADMIN_IDS
        
        try:
            # Пытаемся получить пользователя из базы
            user = await User.get(id=user_data.id)
            
            # Обновляем данные, если они изменились
            need_update = False
            if user.username != user_data.username:
                user.username = user_data.username
                need_update = True
            if user.first_name != user_data.first_name:
                user.first_name = user_data.first_name
                need_update = True
            if user.last_name != user_data.last_name:
                user.last_name = user_data.last_name
                need_update = True
            if is_admin and not user.is_admin:
                user.is_admin = True
                need_update = True
                
            if need_update:
                await user.save()
        
        except ValueError:
            # Пользователь не найден, создаем нового
            user = await User.get_or_create(
                id=user_data.id,
                defaults={
                    "username": user_data.username,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "is_admin": is_admin,
                    "balance": 0.0
                }
            )
        
        # Добавляем пользователя в контекст обработчика
        data["user"] = user
        
        # Продолжаем обработку запроса
        return await handler(event, data) 