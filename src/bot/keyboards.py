"""Keyboards for the updated bot interface."""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


# Main menu keyboard
def get_main_menu_keyboard():
    """Returns the main menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="📊 Анализ по @аккаунту", callback_data="type:account")],
        [InlineKeyboardButton(text="#️⃣ Анализ по #хэштегу", callback_data="type:hashtag")],
        [InlineKeyboardButton(text="📍 Анализ по локац��и", callback_data="type:location")],
        [InlineKeyboardButton(text="🔗 Анализ по ссылке на Reel", callback_data="type:reel_url")],
        [InlineKeyboardButton(text="🔬 Анализ с AI Vision", callback_data="vision_analysis")],
        [InlineKeyboardButton(text="📋 Мои контексты", callback_data="contexts:main")],
        [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about_project")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Period selection keyboard
def get_period_keyboard() -> InlineKeyboardMarkup:
    """Get period selection keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3 дня", callback_data="period:3"),
                InlineKeyboardButton(text="7 дней", callback_data="period:7"),
                InlineKeyboardButton(text="14 дней", callback_data="period:14")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# Sample size keyboard
def get_sample_size_keyboard() -> InlineKeyboardMarkup:
    """Get sample size selection keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5 Reels", callback_data="sample:5"),
                InlineKeyboardButton(text="7 Reels", callback_data="sample:7"),
                InlineKeyboardButton(text="10 Reels", callback_data="sample:10")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_period")
            ]
        ]
    )
    return keyboard


# Confirmation keyboard
def get_confirmation_keyboard(price_rub: float) -> InlineKeyboardMarkup:
    """Get analysis confirmation keyboard with price."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Подтвердить ({price_rub:.0f} ₽)",
                    callback_data="confirm_analysis"
                )
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_analysis")
            ]
        ]
    )
    return keyboard


# Back to main menu button
def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Get back to main menu button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
            ]
        ]
    )
    return keyboard


# New analysis button
def get_new_analysis_keyboard() -> InlineKeyboardMarkup:
    """Get new analysis button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Новый анализ", callback_data="new_analysis")
            ]
        ]
    )
    return keyboard


# Cancel button (for any stage)
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get cancel button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_analysis")
            ]
        ]
    )
    return keyboard


# Export formats keyboard
def get_export_keyboard() -> InlineKeyboardMarkup:
    """Get export formats keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 JSON", callback_data="export_json")
            ],
            [
                InlineKeyboardButton(text="📊 Новый анализ", callback_data="new_analysis")
            ]
        ]
    )
    return keyboard


# Analytics message keyboard with export and scenario options
def get_analytics_keyboard(has_pdf: bool = True) -> InlineKeyboardMarkup:
    """Get analytics message keyboard."""
    buttons = []
    
    # First row - export button
    buttons.append([
        InlineKeyboardButton(text="📋 JSON", callback_data="export_json")
    ])
    
    # Second row - PDF if available
    if has_pdf:
        buttons.append([
            InlineKeyboardButton(text="📑 Скачать PDF отчет", callback_data="download_pdf")
        ])
    
    # Third row - new analysis
    buttons.append([
        InlineKeyboardButton(text="📊 Новый анализ", callback_data="new_analysis")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


# Scenario button for individual reels
def get_scenario_keyboard(reel_id: str) -> InlineKeyboardMarkup:
    """Get scenario button for a reel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Сценарий",
                    callback_data=f"scenario:{reel_id}"
                )
            ]
        ]
    )
    return keyboard


# Analysis type messages
ANALYSIS_TYPE_MESSAGES = {
    "@аккаунт": """🔍 @аккаунт

Введите username без @
Пример: nadinka.one

⚠️ Вводите только ОДИН аккаунт за раз.
Если нужно проанализировать несколько — делайте отдельные запросы.""",
    
    "#хэштег": """🏷 #хэштег

Введите хэштег без #
Пример: дизайнчеловека

⚠️ Только ОДИН хэштег за запрос.
Если хотите проанализировать несколько — запускайте поочерёдно.""",
    
    "📍локация": """📍 Локация

Напишите название места или города
Пример: Москва или Sochi Park

⚠️ Если гео не найдено — бот сообщит об этом.""",
    
    "🔗ссылка": """🔗 Ссылка

Вставьте полную ссылку на Reels
Пример: https://www.instagram.com/reel/CojtW7aL8gJ/

⚠️ Поддерживаются только Instagram Reels.
Не используйте ссылки на Stories, IGTV или профили."""
}


def get_user_context_confirmation_keyboard():
    """Returns keyboard for user context confirmation."""
    buttons = [
        [InlineKeyboardButton(text="✅ Все верно, генерируем!", callback_data="confirm_context_correct")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="confirm_context_restart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_generation_mode_keyboard(has_context: bool = False, context_summary: str = None) -> InlineKeyboardMarkup:
    """Get keyboard for selecting generation mode.
    
    Args:
        has_context: Whether user has saved context
        context_summary: Short summary of user context
        
    Returns:
        InlineKeyboardMarkup with generation options
    """
    buttons = []
    
    # Always available option - no context
    buttons.append([
        InlineKeyboardButton(text="🤖 Без контекста", callback_data="gen_mode:no_context")
    ])
    
    # Add context option if user has saved context
    if has_context:
        context_text = "📝 С моим контекстом"
        if context_summary:
            context_text += f" ({context_summary[:20]}...)"
        
        buttons.append([
            InlineKeyboardButton(text=context_text, callback_data="gen_mode:with_context")
        ])
    
    # Option to create new context
    buttons.append([
        InlineKeyboardButton(text="✍️ Создать новый контекст", callback_data="gen_mode:create_context")
    ])
    
    # Cancel button
    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_analysis")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vision_analysis_keyboard(reel_id: str, video_url: str) -> InlineKeyboardMarkup:
    """Get keyboard for Vision Analysis options.
    
    Args:
        reel_id: Reel ID from Apify
        video_url: Direct video URL
        
    Returns:
        InlineKeyboardMarkup with Vision Analysis options
    """
    buttons = [
        [InlineKeyboardButton(
            text="🔬 Анализ с AI Vision", 
            callback_data=f"vision_scenario:{reel_id}:{video_url}"
        )],
        [InlineKeyboardButton(
            text="📊 Обычный сценарий", 
            callback_data=f"basic_scenario:{reel_id}"
        )],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_analysis")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Контексты пользователя - главное меню
def get_contexts_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню управления контекстами."""
    buttons = [
        [InlineKeyboardButton(text="📋 Мои контексты", callback_data="contexts:list")],
        [InlineKeyboardButton(text="➕ Создать контекст", callback_data="contexts:create")],
        [InlineKeyboardButton(text="🔄 Обновить список", callback_data="contexts:refresh")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура для списка контекстов
def get_contexts_list_keyboard(contexts: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком контекстов пользователя."""
    buttons = []
    
    # Рассчитать страницы
    total_contexts = len(contexts)
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_contexts)
    
    # Добавить кнопки контекстов для текущей страницы
    for i in range(start_idx, end_idx):
        context = contexts[i]
        context_id = context.get('id', i)
        name = context.get('name', f'Контекст {i+1}')
        
        # Ограничить длину названия
        if len(name) > 25:
            name = name[:22] + "..."
        
        buttons.append([
            InlineKeyboardButton(
                text=f"📋 {name}", 
                callback_data=f"context:view:{context_id}"
            )
        ])
    
    # Кнопки навигации по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"contexts:page:{page-1}")
        )
    
    if end_idx < total_contexts:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"contexts:page:{page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Кнопки управления
    management_buttons = [
        InlineKeyboardButton(text="➕ Создать", callback_data="contexts:create"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="contexts:refresh")
    ]
    buttons.append(management_buttons)
    
    # Назад
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="contexts:main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура для просмотра отдельного контекста
def get_context_view_keyboard(context_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра отдельного контекста."""
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"context:edit:{context_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"context:delete:{context_id}")
        ],
        [
            InlineKeyboardButton(text="📋 Использовать для анализа", callback_data=f"context:use:{context_id}")
        ],
        [
            InlineKeyboardButton(text="📄 Скачать как текст", callback_data=f"context:download:{context_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ К списку контекстов", callback_data="contexts:list")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура подтверждения удаления контекста
def get_context_delete_keyboard(context_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления контекста."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"context:delete_confirm:{context_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"context:view:{context_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура для выбора, что редактировать в контексте
def get_context_edit_keyboard(context_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора, что редактировать в контексте."""
    buttons = [
        [InlineKeyboardButton(text="📝 Название", callback_data=f"context:edit_name:{context_id}")],
        [InlineKeyboardButton(text="📄 Описание", callback_data=f"context:edit_desc:{context_id}")],
        [InlineKeyboardButton(text="💼 Данные контекста", callback_data=f"context:edit_data:{context_id}")],
        [InlineKeyboardButton(text="◀️ Назад к контексту", callback_data=f"context:view:{context_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура отмены редактирования
def get_context_edit_cancel_keyboard(context_id: int) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования."""
    buttons = [
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"context:view:{context_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура для выбора контекста при анализе
def get_context_selection_keyboard(contexts: list) -> InlineKeyboardMarkup:
    """Клавиатура для выбора контекста при создании сценария."""
    buttons = []
    
    # Добавить первые 5 контекстов
    for i, context in enumerate(contexts[:5]):
        context_id = context.get('id', i)
        name = context.get('name', f'Контекст {i+1}')
        
        # Ограничить длину названия
        if len(name) > 30:
            name = name[:27] + "..."
        
        buttons.append([
            InlineKeyboardButton(
                text=f"📋 {name}", 
                callback_data=f"context:select:{context_id}"
            )
        ])
    
    # Если контекстов больше 5, добавить кнопку "Показать все"
    if len(contexts) > 5:
        buttons.append([
            InlineKeyboardButton(text="📋 Показать все контексты", callback_data="contexts:list_for_selection")
        ])
    
    # Опция без контекста
    buttons.append([
        InlineKeyboardButton(text="🚫 Без контекста", callback_data="context:select:none")
    ])
    
    # Создать новый контекст
    buttons.append([
        InlineKeyboardButton(text="➕ Создать новый", callback_data="contexts:create_for_analysis")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Клавиатура выбора формата генерации сценария
def get_scenario_format_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата генерации сценария."""
    buttons = [
        [
            InlineKeyboardButton(text="📱 В сообщении", callback_data="scenario_format:message"),
            InlineKeyboardButton(text="📄 Текстовый файл", callback_data="scenario_format:file")
        ],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_analysis")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)