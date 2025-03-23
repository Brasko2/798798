"""
Модели для системы поддержки пользователей
"""
from dataclasses import dataclass, field
from typing import List, Optional, ClassVar, Literal
from datetime import datetime
import logging
from enum import Enum

from ..database import db
from ..exceptions import DatabaseError


logger = logging.getLogger(__name__)


class TicketStatus(str, Enum):
    """Статус тикета поддержки"""
    OPEN = "open"       # Открыт
    CLOSED = "closed"   # Закрыт
    ANSWERED = "answered"  # Ответ от администратора, ожидает ответа пользователя


@dataclass
class TicketMessage:
    """Модель сообщения в тикете поддержки"""
    id: int
    ticket_id: int
    user_id: int
    is_admin: bool = False
    text: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "is_admin": self.is_admin,
            "text": self.text,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_document(cls, document: dict) -> 'TicketMessage':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            ticket_id=document["ticket_id"],
            user_id=document["user_id"],
            is_admin=document.get("is_admin", False),
            text=document.get("text", ""),
            created_at=document.get("created_at", datetime.now())
        )
    
    @classmethod
    async def create(cls, ticket_id: int, user_id: int, text: str, is_admin: bool = False) -> 'TicketMessage':
        """Создает новое сообщение в тикете"""
        try:
            # Получение следующего ID
            next_id = await db.get_next_id("ticket_messages")
            
            # Создание объекта сообщения
            message = cls(
                id=next_id,
                ticket_id=ticket_id,
                user_id=user_id,
                is_admin=is_admin,
                text=text
            )
            
            # Сохранение в базу данных
            await db.ticket_messages.insert_one(message.document)
            
            # Обновляем статус тикета, если это сообщение от администратора
            if is_admin:
                await SupportTicket.update_status(ticket_id, TicketStatus.ANSWERED)
            else:
                await SupportTicket.update_status(ticket_id, TicketStatus.OPEN)
            
            logger.info(f"Created new message in ticket {ticket_id} by user {user_id}")
            return message
        except Exception as e:
            logger.error(f"Error creating ticket message: {str(e)}")
            raise DatabaseError(f"Failed to create ticket message: {str(e)}")
    
    @classmethod
    async def get_by_ticket(cls, ticket_id: int) -> List['TicketMessage']:
        """Получает все сообщения для указанного тикета"""
        try:
            cursor = db.ticket_messages.find({"ticket_id": ticket_id}).sort("created_at", 1)
            messages = []
            async for document in cursor:
                messages.append(cls.from_document(document))
            return messages
        except Exception as e:
            logger.error(f"Error getting messages for ticket {ticket_id}: {str(e)}")
            raise DatabaseError(f"Failed to get ticket messages: {str(e)}")


@dataclass
class SupportTicket:
    """Модель тикета поддержки"""
    id: int
    user_id: int
    subject: str
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def document(self) -> dict:
        """Преобразует объект в документ для MongoDB"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subject": self.subject,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_document(cls, document: dict) -> 'SupportTicket':
        """Создает объект из документа MongoDB"""
        return cls(
            id=document["id"],
            user_id=document["user_id"],
            subject=document["subject"],
            status=TicketStatus(document.get("status", TicketStatus.OPEN.value)),
            created_at=document.get("created_at", datetime.now()),
            updated_at=document.get("updated_at", datetime.now())
        )
    
    @classmethod
    async def create(cls, user_id: int, subject: str, initial_message: str) -> 'SupportTicket':
        """Создает новый тикет поддержки"""
        try:
            # Получение следующего ID
            next_id = await db.get_next_id("support_tickets")
            
            # Создание объекта тикета
            ticket = cls(
                id=next_id,
                user_id=user_id,
                subject=subject
            )
            
            # Сохранение тикета в базу данных
            await db.support_tickets.insert_one(ticket.document)
            
            # Создание первого сообщения в тикете
            await TicketMessage.create(
                ticket_id=ticket.id,
                user_id=user_id,
                text=initial_message,
                is_admin=False
            )
            
            logger.info(f"Created new support ticket {ticket.id} by user {user_id}")
            return ticket
        except Exception as e:
            logger.error(f"Error creating support ticket: {str(e)}")
            raise DatabaseError(f"Failed to create support ticket: {str(e)}")
    
    @classmethod
    async def get_by_id(cls, ticket_id: int) -> Optional['SupportTicket']:
        """Получает тикет по ID"""
        try:
            document = await db.support_tickets.find_one({"id": ticket_id})
            if document:
                return cls.from_document(document)
            return None
        except Exception as e:
            logger.error(f"Error getting ticket by ID {ticket_id}: {str(e)}")
            raise DatabaseError(f"Failed to get ticket: {str(e)}")
    
    @classmethod
    async def get_by_user(cls, user_id: int) -> List['SupportTicket']:
        """Получает все тикеты пользователя"""
        try:
            cursor = db.support_tickets.find({"user_id": user_id}).sort("updated_at", -1)
            tickets = []
            async for document in cursor:
                tickets.append(cls.from_document(document))
            return tickets
        except Exception as e:
            logger.error(f"Error getting tickets for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to get user tickets: {str(e)}")
    
    @classmethod
    async def get_all(cls, status: Optional[TicketStatus] = None) -> List['SupportTicket']:
        """Получает все тикеты или тикеты с указанным статусом"""
        try:
            query = {}
            if status:
                query["status"] = status.value
            
            cursor = db.support_tickets.find(query).sort("updated_at", -1)
            tickets = []
            async for document in cursor:
                tickets.append(cls.from_document(document))
            return tickets
        except Exception as e:
            logger.error(f"Error getting all tickets: {str(e)}")
            raise DatabaseError(f"Failed to get tickets: {str(e)}")
    
    @classmethod
    async def update_status(cls, ticket_id: int, status: TicketStatus) -> Optional['SupportTicket']:
        """Обновляет статус тикета"""
        try:
            result = await db.support_tickets.update_one(
                {"id": ticket_id},
                {"$set": {"status": status.value, "updated_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                ticket = await cls.get_by_id(ticket_id)
                logger.info(f"Updated ticket {ticket_id} status to {status.value}")
                return ticket
            
            logger.warning(f"Ticket not found or status not updated: {ticket_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id} status: {str(e)}")
            raise DatabaseError(f"Failed to update ticket status: {str(e)}")
    
    @classmethod
    async def close(cls, ticket_id: int) -> Optional['SupportTicket']:
        """Закрывает тикет"""
        return await cls.update_status(ticket_id, TicketStatus.CLOSED)
    
    @classmethod
    async def reopen(cls, ticket_id: int) -> Optional['SupportTicket']:
        """Открывает закрытый тикет"""
        return await cls.update_status(ticket_id, TicketStatus.OPEN)
    
    @classmethod
    async def get_open_count(cls) -> int:
        """Возвращает количество открытых тикетов"""
        try:
            return await db.support_tickets.count_documents({"status": TicketStatus.OPEN.value})
        except Exception as e:
            logger.error(f"Error counting open tickets: {str(e)}")
            raise DatabaseError(f"Failed to count open tickets: {str(e)}")
    
    async def add_message(self, user_id: int, text: str, is_admin: bool = False) -> TicketMessage:
        """Добавляет сообщение в тикет"""
        return await TicketMessage.create(
            ticket_id=self.id,
            user_id=user_id,
            text=text,
            is_admin=is_admin
        )
    
    async def get_messages(self) -> List[TicketMessage]:
        """Получает все сообщения тикета"""
        return await TicketMessage.get_by_ticket(self.id) 