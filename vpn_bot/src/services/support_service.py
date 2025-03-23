from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import Database, SupportTicket, User


class SupportService:
    def __init__(self, database: Database):
        self.db = database

    async def create_ticket(
        self, user_id: int, subject: str, message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Создание нового тикета поддержки
        
        Args:
            user_id: ID пользователя
            subject: Тема обращения
            message: Сообщение
            
        Returns:
            Dict с информацией о созданном тикете или None в случае ошибки
        """
        # Проверяем существование пользователя
        user = await self.db.get_user(user_id)
        if not user:
            return None
            
        # Создаем тикет
        ticket = SupportTicket(
            ticket_id=0,  # ID будет присвоен базой данных
            user_id=user_id,
            subject=subject,
            message=message,
            is_resolved=False
        )
        
        ticket = await self.db.create_support_ticket(ticket)
        if not ticket:
            return None
            
        # Формируем результат
        return {
            "ticket_id": ticket.ticket_id,
            "user_id": ticket.user_id,
            "subject": ticket.subject,
            "message": ticket.message,
            "is_resolved": ticket.is_resolved,
            "created_at": ticket.created_at.isoformat()
        }

    async def get_user_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение тикетов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список тикетов пользователя
        """
        tickets = await self.db.get_user_tickets(user_id)
        
        return [
            {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "message": ticket.message,
                "is_resolved": ticket.is_resolved,
                "created_at": ticket.created_at.isoformat()
            }
            for ticket in tickets
        ]

    async def get_all_tickets(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """
        Получение всех тикетов (для администраторов)
        
        Args:
            include_resolved: Включать ли решенные тикеты
            
        Returns:
            Список всех тикетов
        """
        query = 'SELECT * FROM support_tickets'
        if not include_resolved:
            query += ' WHERE is_resolved = FALSE'
        query += ' ORDER BY created_at DESC'
        
        tickets = []
        async with self.db._get_connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            
            for row in rows:
                ticket = SupportTicket(
                    ticket_id=row['ticket_id'],
                    user_id=row['user_id'],
                    subject=row['subject'],
                    message=row['message'],
                    is_resolved=bool(row['is_resolved']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
                # Получаем данные пользователя
                user = await self.db.get_user(ticket.user_id)
                username = user.username if user else "Unknown"
                
                tickets.append({
                    "ticket_id": ticket.ticket_id,
                    "user_id": ticket.user_id,
                    "username": username,
                    "subject": ticket.subject,
                    "message": ticket.message,
                    "is_resolved": ticket.is_resolved,
                    "created_at": ticket.created_at.isoformat()
                })
                
        return tickets

    async def resolve_ticket(self, ticket_id: int) -> bool:
        """
        Отметить тикет как решенный
        
        Args:
            ticket_id: ID тикета
            
        Returns:
            bool: True в случае успеха, иначе False
        """
        ticket = await self.db.resolve_support_ticket(ticket_id)
        return ticket is not None

    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение тикета по ID
        
        Args:
            ticket_id: ID тикета
            
        Returns:
            Dict с информацией о тикете или None в случае ошибки
        """
        ticket = await self.db.get_support_ticket(ticket_id)
        if not ticket:
            return None
            
        # Получаем данные пользователя
        user = await self.db.get_user(ticket.user_id)
        username = user.username if user else "Unknown"
        
        return {
            "ticket_id": ticket.ticket_id,
            "user_id": ticket.user_id,
            "username": username,
            "subject": ticket.subject,
            "message": ticket.message,
            "is_resolved": ticket.is_resolved,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat()
        } 