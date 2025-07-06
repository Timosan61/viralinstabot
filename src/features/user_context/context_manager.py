"""
Система управления контекстами пользователей.
Позволяет пользователям сохранять/редактировать/удалять несколько контекстов.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import select, insert, update, delete, func

from src.utils.logger import get_logger
from src.storage.models import UserContextModel

logger = get_logger(__name__)


@dataclass
class UserContext:
    """Модель контекста пользователя."""
    id: int
    user_id: int
    name: str
    description: str
    context_data: str
    created_at: datetime
    updated_at: datetime


class ContextManager:
    """Менеджер для управления контекстами пользователей."""
    
    def __init__(self, db_session):
        """
        Инициализация менеджера.
        
        Args:
            db_session: Сессия базы данных
        """
        self.db_session = db_session
    
    async def create_context(self, user_id: int, name: str, description: str, context_data: str) -> UserContext:
        """
        Создать новый контекст пользователя.
        
        Args:
            user_id: ID пользователя
            name: Название контекста
            description: Описание контекста
            context_data: Данные контекста
            
        Returns:
            Созданный контекст
        """
        try:
            # Проверить количество контекстов пользователя
            existing_count = await self.count_user_contexts(user_id)
            
            if existing_count >= 10:  # Максимум 10 контекстов на пользователя
                raise ValueError("Достигнут максимум контекстов (10). Удалите ненужные.")
            
            # Проверить уникальность названия для пользователя
            existing = await self.get_context_by_name(user_id, name)
            if existing:
                raise ValueError(f"Контекст с названием '{name}' уже существует")
            
            now = datetime.now()
            
            # Создать запись в БД
            stmt = insert(UserContextModel).values(
                user_id=user_id,
                name=name,
                description=description,
                context_data=context_data,
                created_at=now,
                updated_at=now
            )
            
            result = await self.db_session.execute(stmt)
            context_id = result.inserted_primary_key[0]
            
            await self.db_session.commit()
            
            context = UserContext(
                id=context_id,
                user_id=user_id,
                name=name,
                description=description,
                context_data=context_data,
                created_at=now,
                updated_at=now
            )
            
            logger.info(f"Created context '{name}' for user {user_id}")
            return context
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating context: {e}")
            raise
    
    async def get_user_contexts(self, user_id: int) -> List[UserContext]:
        """
        Получить все контексты пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список контекстов
        """
        try:
            stmt = select(UserContextModel).where(
                UserContextModel.user_id == user_id
            ).order_by(UserContextModel.updated_at.desc())
            
            result = await self.db_session.execute(stmt)
            rows = result.fetchall()
            
            contexts = []
            for row in rows:
                context_model = row[0]
                context = UserContext(
                    id=context_model.id,
                    user_id=context_model.user_id,
                    name=context_model.name,
                    description=context_model.description,
                    context_data=context_model.context_data,
                    created_at=context_model.created_at,
                    updated_at=context_model.updated_at
                )
                contexts.append(context)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error getting user contexts: {e}")
            return []
    
    async def get_context_by_id(self, user_id: int, context_id: int) -> Optional[UserContext]:
        """
        Получить контекст по ID (с проверкой владельца).
        
        Args:
            user_id: ID пользователя
            context_id: ID контекста
            
        Returns:
            Контекст или None
        """
        try:
            stmt = select(UserContextModel).where(
                UserContextModel.id == context_id,
                UserContextModel.user_id == user_id
            )
            
            result = await self.db_session.execute(stmt)
            context_model = result.scalar_one_or_none()
            
            if not context_model:
                return None
            
            return UserContext(
                id=context_model.id,
                user_id=context_model.user_id,
                name=context_model.name,
                description=context_model.description,
                context_data=context_model.context_data,
                created_at=context_model.created_at,
                updated_at=context_model.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting context by ID: {e}")
            return None
    
    async def get_context_by_name(self, user_id: int, name: str) -> Optional[UserContext]:
        """
        Получить контекст по названию.
        
        Args:
            user_id: ID пользователя
            name: Название контекста
            
        Returns:
            Контекст или None
        """
        try:
            stmt = select(UserContextModel).where(
                UserContextModel.user_id == user_id,
                UserContextModel.name == name
            )
            
            result = await self.db_session.execute(stmt)
            context_model = result.scalar_one_or_none()
            
            if not context_model:
                return None
            
            return UserContext(
                id=context_model.id,
                user_id=context_model.user_id,
                name=context_model.name,
                description=context_model.description,
                context_data=context_model.context_data,
                created_at=context_model.created_at,
                updated_at=context_model.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting context by name: {e}")
            return None
    
    async def update_context(self, user_id: int, context_id: int, name: str = None, 
                           description: str = None, context_data: str = None) -> Optional[UserContext]:
        """
        Обновить контекст.
        
        Args:
            user_id: ID пользователя
            context_id: ID контекста
            name: Новое название (опционально)
            description: Новое описание (опционально)
            context_data: Новые данные (опционально)
            
        Returns:
            Обновленный контекст или None
        """
        try:
            # Проверить существование и владельца
            existing = await self.get_context_by_id(user_id, context_id)
            if not existing:
                return None
            
            # Проверить изменения
            has_changes = False
            
            if name is not None and name != existing.name:
                # Проверить уникальность нового названия
                name_exists = await self.get_context_by_name(user_id, name)
                if name_exists:
                    raise ValueError(f"Контекст с названием '{name}' уже существует")
                has_changes = True
            
            if description is not None and description != existing.description:
                has_changes = True
            
            if context_data is not None and context_data != existing.context_data:
                has_changes = True
            
            if not has_changes:
                return existing  # Нет изменений
            
            # Подготовить данные для обновления
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if description is not None:
                update_data['description'] = description
            if context_data is not None:
                update_data['context_data'] = context_data
            
            update_data['updated_at'] = datetime.now()
            
            stmt = update(UserContextModel).where(
                UserContextModel.id == context_id,
                UserContextModel.user_id == user_id
            ).values(**update_data)
            
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Получить обновленный контекст
            updated = await self.get_context_by_id(user_id, context_id)
            
            logger.info(f"Updated context {context_id} for user {user_id}")
            return updated
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating context: {e}")
            raise
    
    async def delete_context(self, user_id: int, context_id: int) -> bool:
        """
        Удалить контекст.
        
        Args:
            user_id: ID пользователя
            context_id: ID контекста
            
        Returns:
            True если удален, False если не найден
        """
        try:
            # Проверить существование и владельца
            existing = await self.get_context_by_id(user_id, context_id)
            if not existing:
                return False
            
            stmt = delete(UserContextModel).where(
                UserContextModel.id == context_id,
                UserContextModel.user_id == user_id
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted context {context_id} for user {user_id}")
            
            return deleted
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error deleting context: {e}")
            return False
    
    async def count_user_contexts(self, user_id: int) -> int:
        """
        Подсчитать количество контекстов пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество контекстов
        """
        try:
            stmt = select(func.count(UserContextModel.id)).where(
                UserContextModel.user_id == user_id
            )
            result = await self.db_session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting contexts: {e}")
            return 0
    
    def format_context_list(self, contexts: List[UserContext]) -> str:
        """
        Форматировать список контекстов для отображения.
        
        Args:
            contexts: Список контекстов
            
        Returns:
            Отформатированная строка
        """
        if not contexts:
            return "📝 У вас пока нет сохраненных контекстов"
        
        lines = ["📝 Ваши контексты:"]
        
        for i, context in enumerate(contexts, 1):
            # Ограничить длину описания
            desc = context.description
            if len(desc) > 50:
                desc = desc[:47] + "..."
            
            lines.append(f"\n{i}. 📋 {context.name}")
            lines.append(f"   {desc}")
            lines.append(f"   📅 {context.updated_at.strftime('%d.%m.%Y %H:%M')}")
        
        return "\n".join(lines)
    
    def format_context_details(self, context: UserContext) -> str:
        """
        Форматировать подробную информацию о контексте.
        
        Args:
            context: Контекст
            
        Returns:
            Отформатированная строка
        """
        return f"""📋 Контекст: {context.name}

📝 Описание:
{context.description}

💼 Данные контекста:
{context.context_data}

📅 Создан: {context.created_at.strftime('%d.%m.%Y %H:%M')}
🔄 Обновлен: {context.updated_at.strftime('%d.%m.%Y %H:%M')}"""


# Глобальный экземпляр (будет инициализирован в main)
context_manager: Optional[ContextManager] = None


def initialize_context_manager(db_session) -> ContextManager:
    """
    Инициализация глобального экземпляра менеджера контекстов.
    
    Args:
        db_session: Сессия базы данных
        
    Returns:
        Экземпляр ContextManager
    """
    global context_manager
    context_manager = ContextManager(db_session)
    return context_manager


def get_context_manager() -> Optional[ContextManager]:
    """
    Получение глобального экземпляра менеджера контекстов.
    
    Returns:
        Экземпляр ContextManager или None если не инициализирован
    """
    return context_manager