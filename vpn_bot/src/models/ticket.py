"""
Модель тикета поддержки
"""

from datetime import datetime
from typing import Optional, List
from bson import ObjectId
import logging

from ..database import db

logger = logging.getLogger(__name__)


class Ticket:
    """
    Класс для работы с тикетами поддержки пользователей
    """
    
    def __init__(
        self,
        user_id: int,
        username: str,
        subject: str,
        message: str,
        status: str = "open",
        photo_id: Optional[str] = None,
        admin_reply: Optional[str] = None,
        admin_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        ticket_id: Optional[str] = None,
        _id: Optional[ObjectId] = None
    ):
        self.user_id = user_id
        self.username = username
        self.subject = subject
        self.message = message
        self.status = status
        self.photo_id = photo_id
        self.admin_reply = admin_reply
        self.admin_id = admin_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at
        self.ticket_id = ticket_id
        self._id = _id
    
    @classmethod
    async def get_by_id(cls, ticket_id: str) -> Optional['Ticket']:
        """
        Получает тикет по ID
        
        Args:
            ticket_id: ID тикета
            
        Returns:
            Ticket или None, если тикет не найден
        """
        try:
            ticket_data = await db.tickets.find_one({"ticket_id": ticket_id})
            if not ticket_data:
                return None
            return cls(**ticket_data)
        except Exception as e:
            logger.error(f"Error getting ticket by ID: {e}")
            return None
    
    @classmethod
    async def get_by_user_id(cls, user_id: int) -> List['Ticket']:
        """
        Получает все тикеты пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список тикетов пользователя
        """
        try:
            tickets = []
            cursor = db.tickets.find({"user_id": user_id}).sort("created_at", -1)
            async for ticket_data in cursor:
                tickets.append(cls(**ticket_data))
            return tickets
        except Exception as e:
            logger.error(f"Error getting tickets by user ID: {e}")
            return []
    
    @classmethod
    async def get_all_open_tickets(cls) -> List['Ticket']:
        """
        Получает все открытые тикеты
        
        Returns:
            Список открытых тикетов
        """
        try:
            tickets = []
            cursor = db.tickets.find({"status": "open"}).sort("created_at", 1)
            async for ticket_data in cursor:
                tickets.append(cls(**ticket_data))
            return tickets
        except Exception as e:
            logger.error(f"Error getting open tickets: {e}")
            return []
    
    async def save(self) -> bool:
        """
        Сохраняет тикет в базу данных
        
        Returns:
            True если сохранение успешно, иначе False
        """
        try:
            ticket_data = {
                "user_id": self.user_id,
                "username": self.username,
                "subject": self.subject,
                "message": self.message,
                "status": self.status,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
            
            if self.photo_id:
                ticket_data["photo_id"] = self.photo_id
            
            if self.admin_reply:
                ticket_data["admin_reply"] = self.admin_reply
            
            if self.admin_id:
                ticket_data["admin_id"] = self.admin_id
            
            # Если это новый тикет, генерируем ID
            if not self.ticket_id:
                # Генерируем простой ID на основе времени и user_id
                timestamp = int(datetime.now().timestamp())
                self.ticket_id = f"{timestamp}-{self.user_id}"
                ticket_data["ticket_id"] = self.ticket_id
            else:
                ticket_data["ticket_id"] = self.ticket_id
            
            # Если тикет уже существует, обновляем его
            if self._id:
                await db.tickets.update_one(
                    {"_id": self._id},
                    {"$set": ticket_data}
                )
            else:
                # Иначе создаем новый
                result = await db.tickets.insert_one(ticket_data)
                self._id = result.inserted_id
            
            return True
        except Exception as e:
            logger.error(f"Error saving ticket: {e}")
            return False
    
    async def close(self) -> bool:
        """
        Закрывает тикет
        
        Returns:
            True если закрытие успешно, иначе False
        """
        try:
            self.status = "closed"
            self.updated_at = datetime.now()
            return await self.save()
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            return False
    
    async def reply(self, admin_id: int, reply_text: str) -> bool:
        """
        Добавляет ответ администратора на тикет
        
        Args:
            admin_id: ID администратора
            reply_text: Текст ответа
            
        Returns:
            True если ответ успешно добавлен, иначе False
        """
        try:
            self.admin_id = admin_id
            self.admin_reply = reply_text
            self.updated_at = datetime.now()
            return await self.save()
        except Exception as e:
            logger.error(f"Error replying to ticket: {e}")
            return False
    
    @classmethod
    async def delete_by_id(cls, ticket_id: str) -> bool:
        """
        Удаляет тикет по ID
        
        Args:
            ticket_id: ID тикета
            
        Returns:
            True если удаление успешно, иначе False
        """
        try:
            result = await db.tickets.delete_one({"ticket_id": ticket_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting ticket: {e}")
            return False 