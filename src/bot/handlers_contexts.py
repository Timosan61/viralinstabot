"""
Обработчики для управления контекстами пользователей.
"""

import logging
from typing import Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from src.bot.states import ContextManagementStates
from src.bot.keyboards import (
    get_contexts_main_keyboard,
    get_contexts_list_keyboard,
    get_context_view_keyboard,
    get_context_delete_keyboard,
    get_context_edit_keyboard,
    get_context_edit_cancel_keyboard,
    get_back_to_main_keyboard
)
from src.features.user_context import get_context_manager
from src.storage.sqlite import db
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="contexts")


@router.callback_query(F.data == "contexts:main")
async def show_contexts_main_menu(callback: CallbackQuery, state: FSMContext):
    """Показать главное меню управления контекстами."""
    try:
        await state.clear()
        
        text = """📋 УПРАВЛЕНИЕ КОНТЕКСТАМИ

Контексты помогают генерировать персонализированные сценарии для ваших проектов.

Примеры контекстов:
• 🏢 Бизнес-проект (товары, услуги)
• 👤 Персональный блог (хобби, жизнь)
• 🎨 Творческий проект (искусство, дизайн)
• 📚 Образовательный контент

Выберите действие:"""

        await callback.message.edit_text(
            text,
            reply_markup=get_contexts_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in show_contexts_main_menu: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "contexts:list")
async def show_contexts_list(callback: CallbackQuery, state: FSMContext):
    """Показать список контекстов пользователя."""
    try:
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Получить контексты пользователя
        contexts = await context_manager.get_user_contexts(user.id)
        
        if not contexts:
            text = """📝 У вас пока нет сохраненных контекстов

💡 Создайте контекст, чтобы генерировать персонализированные сценарии для ваших проектов, товаров или тематик."""
            
            await callback.message.edit_text(
                text,
                reply_markup=get_contexts_main_keyboard()
            )
            return
        
        # Конвертировать в список словарей для клавиатуры
        contexts_data = []
        for context in contexts:
            contexts_data.append({
                'id': context.id,
                'name': context.name,
                'description': context.description
            })
        
        text = f"📋 Ваши контексты ({len(contexts)} шт.)\n\nВыберите контекст для просмотра:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_contexts_list_keyboard(contexts_data)
        )
        
        await state.set_state(ContextManagementStates.viewing_contexts)
        
    except Exception as e:
        logger.error(f"Error in show_contexts_list: {e}")
        await callback.answer("Произошла ошибка при загрузке контекстов", show_alert=True)


@router.callback_query(F.data.startswith("context:view:"))
async def view_context(callback: CallbackQuery, state: FSMContext):
    """Просмотр отдельного контекста."""
    try:
        context_id = int(callback.data.split(":")[2])
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Получить контекст
        context = await context_manager.get_context_by_id(user.id, context_id)
        
        if not context:
            await callback.answer("Контекст не найден", show_alert=True)
            return
        
        # Форматировать для отображения
        text = context_manager.format_context_details(context)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_context_view_keyboard(context_id)
        )
        
    except Exception as e:
        logger.error(f"Error in view_context: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "contexts:create")
async def start_context_creation(callback: CallbackQuery, state: FSMContext):
    """Начать создание нового контекста."""
    try:
        text = """➕ СОЗДАНИЕ НОВОГО КОНТЕКСТА

Шаг 1/3: Введите название контекста

Примеры:
• "Фитнес-блог"
• "Кофейня в центре"
• "Курсы по дизайну"
• "Личный стиль"

Введите название (до 50 символов):"""

        await callback.message.edit_text(
            text,
            reply_markup=get_context_edit_cancel_keyboard(0)
        )
        
        await state.set_state(ContextManagementStates.creating_name)
        
    except Exception as e:
        logger.error(f"Error in start_context_creation: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(ContextManagementStates.creating_name)
async def handle_context_name(message: Message, state: FSMContext):
    """Обработать название контекста."""
    try:
        name = message.text.strip()
        
        if len(name) > 50:
            await message.answer("❌ Название слишком длинное. Максимум 50 символов.")
            return
        
        if len(name) < 3:
            await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
            return
        
        # Сохранить название
        await state.update_data(context_name=name)
        
        text = f"""✅ Название: "{name}"

Шаг 2/3: Введите краткое описание контекста

Опишите в 1-2 предложениях, для чего этот контекст (до 200 символов):

Примеры:
• "Фитнес-контент для женщин 25-35 лет, мотивация и тренировки"
• "Семейная кофейня, уютная атмосфера и качественный кофе"
• "Онлайн-курсы UI/UX дизайна для начинающих"

Введите описание:"""

        await message.answer(text)
        await state.set_state(ContextManagementStates.creating_description)
        
    except Exception as e:
        logger.error(f"Error in handle_context_name: {e}")
        await message.answer("Произошла ошибка при сохранении названия")


@router.message(ContextManagementStates.creating_description)
async def handle_context_description(message: Message, state: FSMContext):
    """Обработать описание контекста."""
    try:
        description = message.text.strip()
        
        if len(description) > 200:
            await message.answer("❌ Описание слишком длинное. Максимум 200 символов.")
            return
        
        if len(description) < 10:
            await message.answer("❌ Описание слишком короткое. Минимум 10 символов.")
            return
        
        # Сохранить описание
        await state.update_data(context_description=description)
        
        text = f"""✅ Описание сохранено

Шаг 3/3: Введите подробные данные контекста

Опишите максимально подробно:
• Ваша ниша/сфера деятельности
• Целевая аудитория
• Ваши цели и задачи
• Особенности и уникальность
• Стиль коммуникации
• Доступные ресурсы

Чем подробнее опишете - тем лучше будут сценарии!

Введите подробные данные контекста:"""

        await message.answer(text)
        await state.set_state(ContextManagementStates.creating_data)
        
    except Exception as e:
        logger.error(f"Error in handle_context_description: {e}")
        await message.answer("Произошла ошибка при сохранении описания")


@router.message(ContextManagementStates.creating_data)
async def handle_context_data(message: Message, state: FSMContext):
    """Обработать данные контекста."""
    try:
        context_data = message.text.strip()
        
        if len(context_data) > 2000:
            await message.answer("❌ Данные слишком длинные. Максимум 2000 символов.")
            return
        
        if len(context_data) < 50:
            await message.answer("❌ Данные слишком короткие. Минимум 50 символов для качественного контекста.")
            return
        
        # Сохранить данные
        await state.update_data(context_data=context_data)
        
        # Получить все данные
        data = await state.get_data()
        name = data.get('context_name')
        description = data.get('context_description')
        
        text = f"""📋 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР КОНТЕКСТА

📝 Название: {name}

📄 Описание: {description}

💼 Данные: {context_data[:300]}{'...' if len(context_data) > 300 else ''}

✅ Сохранить контекст?"""

        await message.answer(
            text,
            reply_markup=get_context_view_keyboard(0)  # Временно используем 0
        )
        
        await state.set_state(ContextManagementStates.confirming_creation)
        
    except Exception as e:
        logger.error(f"Error in handle_context_data: {e}")
        await message.answer("Произошла ошибка при сохранении данных")


@router.callback_query(F.data.startswith("context:delete:"))
async def confirm_context_deletion(callback: CallbackQuery, state: FSMContext):
    """Подтвердить удаление контекста."""
    try:
        context_id = int(callback.data.split(":")[2])
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Получить контекст для отображения названия
        context = await context_manager.get_context_by_id(user.id, context_id)
        
        if not context:
            await callback.answer("Контекст не найден", show_alert=True)
            return
        
        text = f"""🗑 УДАЛЕНИЕ КОНТЕКСТА

Вы уверены, что хотите удалить контекст:
"{context.name}"?

⚠️ Это действие нельзя отменить!"""

        await callback.message.edit_text(
            text,
            reply_markup=get_context_delete_keyboard(context_id)
        )
        
    except Exception as e:
        logger.error(f"Error in confirm_context_deletion: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("context:delete_confirm:"))
async def delete_context(callback: CallbackQuery, state: FSMContext):
    """Удалить контекст."""
    try:
        context_id = int(callback.data.split(":")[2])
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Удалить контекст
        deleted = await context_manager.delete_context(user.id, context_id)
        
        if deleted:
            await callback.answer("✅ Контекст удален", show_alert=True)
            
            # Перейти к списку контекстов
            await show_contexts_list(callback, state)
        else:
            await callback.answer("❌ Не удалось удалить контекст", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error in delete_context: {e}")
        await callback.answer("Произошла ошибка при удалении", show_alert=True)


@router.callback_query(F.data.startswith("context:download:"))
async def download_context_as_text(callback: CallbackQuery, state: FSMContext):
    """Скачать контекст как текстовый файл."""
    try:
        context_id = int(callback.data.split(":")[2])
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Получить контекст
        context = await context_manager.get_context_by_id(user.id, context_id)
        
        if not context:
            await callback.answer("Контекст не найден", show_alert=True)
            return
        
        # Генерировать текстовый отчет
        context_data = {
            'id': context.id,
            'name': context.name,
            'description': context.description,
            'context_data': context.context_data,
            'created_at': context.created_at,
            'updated_at': context.updated_at
        }
        
        # Generate simple text report
        report_text = f"""
📋 Контекст пользователя

📝 Название: {context.name}
📄 Описание: {context.description or 'Не указано'}

💾 Данные контекста:
{context.context_data}

📅 Создан: {context.created_at}
📅 Обновлен: {context.updated_at}
"""
        
        # Отправить как документ
        from io import BytesIO
        
        file_content = report_text.encode('utf-8')
        file_name = f"context_{context.name}_{context.id}.txt"
        
        # Очистить имя файла от недопустимых символов
        import re
        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
        
        file_obj = BytesIO(file_content)
        file_obj.name = file_name
        
        await callback.message.answer_document(
            document=file_obj,
            caption=f"📄 Контекст: {context.name}"
        )
        
        await callback.answer("✅ Файл отправлен")
        
    except Exception as e:
        logger.error(f"Error in download_context_as_text: {e}")
        await callback.answer("Произошла ошибка при создании файла", show_alert=True)


@router.callback_query(F.data == "contexts:refresh")
async def refresh_contexts_list(callback: CallbackQuery, state: FSMContext):
    """Обновить список контекстов."""
    await show_contexts_list(callback, state)