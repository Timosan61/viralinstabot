"""
Модуль управления контекстами пользователей.
"""

from .context_manager import (
    UserContext,
    ContextManager,
    context_manager,
    initialize_context_manager,
    get_context_manager
)

__all__ = [
    'UserContext',
    'ContextManager',
    'context_manager',
    'initialize_context_manager',
    'get_context_manager'
]