"""Updated Telegram bot handlers for new interface."""

import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from src.bot.states import AnalysisStatesV2, UserData
from src.bot.keyboards import (
    get_main_menu_keyboard, get_period_keyboard,
    get_sample_size_keyboard, get_confirmation_keyboard,
    get_back_to_main_keyboard, get_new_analysis_keyboard,
    get_cancel_keyboard, get_analytics_keyboard, ANALYSIS_TYPE_MESSAGES,
    get_generation_mode_keyboard, get_scenario_format_keyboard,
    get_context_selection_keyboard
)
from src.services.apify_direct import apify_direct_service
from src.services.pdf import pdf_service
from src.services.rate_limiter import rate_limiter
from src.services.monthly_limiter import monthly_limiter
from src.storage.sqlite import db
from src.domain.models import QueryPayload, ReportStatus
from src.domain.constants import USD_TO_RUB, PRICE_MULTIPLIER
from src.utils.logger import get_logger
from src.utils.formatters import format_currency, format_number
from src.utils.message_formatter import format_full_analytics_message
from src.features.vision_analysis import get_scenario_generator
from src.features.user_context import get_context_manager

logger = get_logger(__name__)
router = Router()

# Welcome message
WELCOME_MESSAGE = """👋 Добро пожаловать!

Я — AI-аналитик Reels: ищу, анализирую и помогаю делать вирусный контент.

Что могу:
• Анализ по @аккаунту, #хэштегу, 📍локации или 🔗 ссылке
• Даю метрики 
• Определяю вирусные паттерны
• Анализирую описание и визуал ролика
• На основе анализа генерирую вирусный сценарий Reels с твоим контекстом

Как работает:
1️⃣ Выбери тип запроса кнопкой ниже
2️⃣ Я покажу цену — подтверди
3️⃣ Через 1-2 мин получишь PDF-отчёт с кликабельными ссылками

💡 Нажми на кнопку для начала анализа 👇"""


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    await state.clear()
    
    # Get or create user
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(AnalysisStatesV2.main_menu)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """ℹ️ Помощь по использованию бота

Типы анализа:
• @аккаунт - анализ Reels конкретного пользователя
• #хэштег - анализ Reels по хэштегу
• 📍локация - анализ Reels по геометке
• 🔗ссылка - анализ конкретного Reel

Параметры:
• Период: 3, 7 или 14 дней
• Размер выборки: 50, 100 или 200 Reels

Стоимость зависит от типа и объема анализа.

По всем вопросам: @your_support"""
    
    await message.answer(help_text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle /cancel command."""
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(AnalysisStatesV2.main_menu)


# Analysis type selection handlers
@router.callback_query(StateFilter(AnalysisStatesV2.main_menu), F.data.startswith("type:"))
async def handle_analysis_type_selection(callback: CallbackQuery, state: FSMContext):
    """Handle analysis type selection."""
    analysis_type_map = {
        "type:account": "@аккаунт",
        "type:hashtag": "#хэштег",
        "type:location": "📍локация",
        "type:reel_url": "🔗ссылка"
    }
    
    analysis_type = analysis_type_map.get(callback.data)
    
    # Save analysis type
    user_data = UserData()
    user_data.analysis_type = analysis_type
    await state.update_data(user_data=user_data.to_dict())
    
    # Send instructions and set appropriate state
    await callback.message.answer(
        ANALYSIS_TYPE_MESSAGES[analysis_type]
    )
    
    # Set state based on type
    state_map = {
        "@аккаунт": AnalysisStatesV2.waiting_for_account,
        "#хэштег": AnalysisStatesV2.waiting_for_hashtag,
        "📍локация": AnalysisStatesV2.waiting_for_location,
        "🔗ссылка": AnalysisStatesV2.waiting_for_reel_url
    }
    
    await state.set_state(state_map[analysis_type])
    await callback.answer()


# Universal Reel URL handler (works in any state)
@router.message(F.text.regexp(r'https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+'))
async def handle_reel_url_universal(message: Message, state: FSMContext):
    """Handle Reel URL in any state."""
    url = message.text.strip()
    
    # Create user data for URL analysis
    user_data = UserData()
    user_data.analysis_type = "🔗ссылка"
    user_data.input_value = url
    user_data.generation_mode = "no_context"  # Default mode
    await state.update_data(user_data=user_data.to_dict())
    
    # Start analysis immediately
    await start_reel_vision_analysis(message, state, user_data)


# Input handlers for each analysis type
@router.message(StateFilter(AnalysisStatesV2.waiting_for_account))
async def handle_account_input(message: Message, state: FSMContext):
    """Handle account username input."""
    text = message.text.strip()
    
    # Check if it's an Instagram profile URL
    instagram_url_pattern = r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)/?'
    match = re.match(instagram_url_pattern, text)
    
    if match:
        # Extract username from URL
        username = match.group(1)
    else:
        # Remove @ if present
        username = text.replace("@", "")
    
    # Validate username
    if not re.match(r'^[a-zA-Z0-9._]+$', username):
        await message.answer(
            "❌ Неверный формат username. Используйте только буквы, цифры, точки и подчеркивания."
        )
        return
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.input_value = username
    await state.update_data(user_data=user_data.to_dict())
    
    # Show period selection
    await message.answer(
        "📅 За какой период анализировать?",
        reply_markup=get_period_keyboard()
    )
    await state.set_state(AnalysisStatesV2.selecting_period)


@router.message(StateFilter(AnalysisStatesV2.waiting_for_hashtag))
async def handle_hashtag_input(message: Message, state: FSMContext):
    """Handle hashtag input."""
    hashtag = message.text.strip().replace("#", "")
    
    # Validate hashtag
    if not hashtag or " " in hashtag:
        await message.answer(
            "❌ Введите один хэштег без пробелов."
        )
        return
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.input_value = hashtag
    await state.update_data(user_data=user_data.to_dict())
    
    # Show period selection
    await message.answer(
        "📅 За какой период анализировать?",
        reply_markup=get_period_keyboard()
    )
    await state.set_state(AnalysisStatesV2.selecting_period)


@router.message(StateFilter(AnalysisStatesV2.waiting_for_location))
async def handle_location_input(message: Message, state: FSMContext):
    """Handle location input."""
    location = message.text.strip()
    
    if not location:
        await message.answer(
            "❌ Введите название места или города.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.input_value = location
    await state.update_data(user_data=user_data.to_dict())
    
    # Show period selection
    await message.answer(
        "📅 За какой период анализировать?",
        reply_markup=get_period_keyboard()
    )
    await state.set_state(AnalysisStatesV2.selecting_period)


@router.message(StateFilter(AnalysisStatesV2.waiting_for_reel_url))
async def handle_reel_url_input(message: Message, state: FSMContext):
    """Handle Reel URL input."""
    url = message.text.strip()
    
    # Validate URL
    if not re.match(r'https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+', url):
        await message.answer(
            "❌ Неверный формат ссылки. Отправьте ссылку на Instagram Reel.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.input_value = url
    user_data.generation_mode = "no_context"  # Default mode
    await state.update_data(user_data=user_data.to_dict())
    
    # Start analysis immediately
    await start_reel_vision_analysis(message, state, user_data)


# Period selection callback
@router.callback_query(StateFilter(AnalysisStatesV2.selecting_period), F.data.startswith("period:"))
async def handle_period_selection(callback: CallbackQuery, state: FSMContext):
    """Handle period selection."""
    period_days = int(callback.data.split(":")[1])
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.period_days = period_days
    await state.update_data(user_data=user_data.to_dict())
    
    # Show sample size selection
    await callback.message.edit_text(
        "📊 Размер выборки: сколько Reels анализировать?",
        reply_markup=get_sample_size_keyboard()
    )
    await state.set_state(AnalysisStatesV2.selecting_sample_size)
    await callback.answer()


# Sample size selection callback
@router.callback_query(StateFilter(AnalysisStatesV2.selecting_sample_size), F.data.startswith("sample:"))
async def handle_sample_size_selection(callback: CallbackQuery, state: FSMContext):
    """Handle sample size selection."""
    sample_size = int(callback.data.split(":")[1])
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.sample_size = sample_size
    await state.update_data(user_data=user_data.to_dict())
    
    # Show confirmation
    await show_confirmation(callback.message, state, user_data)
    await callback.answer()


async def show_confirmation(message: Message, state: FSMContext, user_data: UserData):
    """Show analysis confirmation with price."""
    # Get user limits
    user_id = message.chat.id
    _, daily_remaining = rate_limiter.check_limit(user_id)
    monthly_usage = monthly_limiter.get_monthly_usage(user_id)
    
    # Calculate price
    base_price = 30  # Base price in RUB (reduced for smaller samples)
    
    # Price modifiers
    if user_data.analysis_type == "🔗ссылка":
        price_rub = 20  # Fixed price for single reel
    else:
        # Price based on sample size
        size_multiplier = {5: 0.8, 7: 1, 10: 1.2}.get(user_data.sample_size, 1)
        # Price based on period
        period_multiplier = {3: 0.8, 7: 1, 14: 1.3}.get(user_data.period_days, 1)
        price_rub = base_price * size_multiplier * period_multiplier
    
    user_data.price_rub = price_rub
    await state.update_data(user_data=user_data.to_dict())
    
    # Build confirmation message
    if user_data.analysis_type == "🔗ссылка":
        confirmation_text = f"""📋 Подтверждение анализа

🔗 Тип: Анализ Reel по ссылке
📎 URL: {user_data.input_value[:50]}...
💰 Стоимость: {format_currency(price_rub)}

Будет проанализирован указанный Reel с подробными метриками.

📊 Остаток запросов: {monthly_usage['remaining']}/{monthly_usage['limit']} в месяц"""
    else:
        type_emoji = {"@аккаунт": "👤", "#хэштег": "🏷", "📍локация": "📍"}
        confirmation_text = f"""📋 Подтверждение анализа

{type_emoji.get(user_data.analysis_type, "📊")} Тип: {user_data.analysis_type}
🔍 Запрос: {user_data.input_value}
📅 Период: {user_data.period_days} дней
📊 Выборка: {user_data.sample_size} Reels
💰 Стоимость: {format_currency(price_rub)}

Будет проанализировано до {user_data.sample_size} самых популярных Reels.

📊 Остаток запросов: {monthly_usage['remaining']}/{monthly_usage['limit']} в месяц"""
    
    await message.edit_text(
        confirmation_text,
        reply_markup=get_confirmation_keyboard(price_rub)
    )
    await state.set_state(AnalysisStatesV2.confirming_analysis)


# Confirm analysis callback
@router.callback_query(StateFilter(AnalysisStatesV2.confirming_analysis), F.data == "confirm_analysis")
async def handle_confirm_analysis(callback: CallbackQuery, state: FSMContext):
    """Handle analysis confirmation."""
    await callback.answer("🚀 Запускаю анализ...")
    
    # Show processing message
    await callback.message.edit_text(
        "⏳ Анализирую данные...\n\n"
        "Это может занять 1-2 минуты в зависимости от объема данных.\n"
        "Пожалуйста, подождите..."
    )
    
    # Get user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    
    try:
        # Check daily rate limit
        is_allowed, remaining = rate_limiter.check_limit(callback.from_user.id)
        if not is_allowed:
            await callback.message.edit_text(
                "❌ Превышен дневной лимит запросов.\nПопробуйте позже.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        # Check monthly rate limit
        is_monthly_allowed, monthly_remaining, reset_date = monthly_limiter.check_monthly_limit(callback.from_user.id)
        if not is_monthly_allowed:
            reset_str = reset_date.strftime("%d.%m.%Y") if reset_date else "начала следующего месяца"
            await callback.message.edit_text(
                f"❌ Превышен месячный лимит запросов (10 запросов в месяц).\n\n"
                f"Лимит обновится: {reset_str}\n\n"
                "Для увеличения лимита обратитесь к администратору.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        # Add to rate limiters
        rate_limiter.add_request(callback.from_user.id)
        monthly_limiter.add_monthly_request(callback.from_user.id)
        
        # Import progress tracker
        from src.utils.progress import ProgressTracker
        
        # Create message updater for progress tracking
        async def update_progress_message(text: str):
            try:
                await callback.message.edit_text(text)
            except Exception:
                # Ignore errors if message hasn't changed
                pass
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(update_progress_message)
        
        # Run analysis based on type
        if user_data.analysis_type == "@аккаунт":
            result = await apify_direct_service.analyze_account(
                user_data.input_value,
                user_data.period_days,
                user_data.sample_size,
                progress_callback=update_progress_message
            )
        elif user_data.analysis_type == "#хэштег":
            result = await apify_direct_service.analyze_hashtag(
                user_data.input_value,
                user_data.period_days,
                user_data.sample_size,
                progress_callback=update_progress_message
            )
        elif user_data.analysis_type == "📍локация":
            result = await apify_direct_service.analyze_location(
                user_data.input_value,
                user_data.period_days,
                user_data.sample_size,
                progress_callback=update_progress_message
            )
        elif user_data.analysis_type == "🔗ссылка":
            result = await apify_direct_service.analyze_reel_url(
                user_data.input_value,
                progress_callback=update_progress_message
            )
        else:
            raise ValueError(f"Unknown analysis type: {user_data.analysis_type}")
        
        # Update progress for data processing
        await progress_tracker.update("process_data", 0.5)
        
        # Check if we have data
        if not result.reels:
            await callback.message.edit_text(
                "❌ Не удалось найти Reels для анализа.\n\n"
                f"💡 Причина: {result.insights[0] if result.insights else 'Нет данных'}\n\n"
                "Попробуйте:\n"
                "• Другой запрос\n"
                "• Увеличить период\n"
                "• Проверить правильность ввода",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        await progress_tracker.update("process_data", 1.0)
        
        # Create query payload for compatibility
        query_payload = QueryPayload(
            topic=user_data.input_value,
            period=user_data.period_days or 0,
            geo="WORLD",
            user_id=callback.from_user.id
        )
        result.query = query_payload
        
        # Save to database
        user = await db.get_or_create_user(telegram_id=callback.from_user.id)
        report = await db.create_report(
            user_id=user.id,
            query_payload=query_payload,
            price_rub=user_data.price_rub
        )
        
        # Generate PDF
        await progress_tracker.update("generate_pdf", 0.0)
        pdf_path = await pdf_service.generate_report(
            analysis_result=result,
            user_id=callback.from_user.id
        )
        await progress_tracker.update("generate_pdf", 1.0)
        
        # Update report
        await progress_tracker.update("save_db", 0.0)
        await db.update_report(
            report_id=report.id,
            analysis_result=result,
            pdf_path=pdf_path,
            status=ReportStatus.COMPLETED
        )
        await progress_tracker.update("save_db", 1.0)
        
        # Send analytics as text message first
        await callback.message.delete()
        
        # Format and send analytics message
        analytics_message = format_full_analytics_message(
            result=result,
            username=user_data.input_value if user_data.analysis_type == "@аккаунт" else "Analytics",
            period_days=user_data.period_days or 7,
            sample_size=user_data.sample_size or len(result.reels)
        )
        
        await callback.message.answer(
            text=analytics_message,
            parse_mode="HTML",
            reply_markup=get_analytics_keyboard(has_pdf=True)
        )
        
        # Then send PDF as a file
        with open(pdf_path, "rb") as pdf_file:
            await callback.message.answer_document(
                document=FSInputFile(pdf_path, filename=f"reels_analysis_{report.id}.pdf"),
                caption=(
                    f"📑 Полный PDF отчет с кликабельными ссылками\n"
                    f"💰 Стоимость: {format_currency(user_data.price_rub)}\n"
                    f"📊 Осталось запросов: {monthly_remaining - 1}/{monthly_limiter.get_monthly_usage(callback.from_user.id)['limit']}"
                )
            )
        
        # Clear state
        await state.clear()
        
        # Increment user requests
        await db.increment_user_requests(callback.from_user.id)
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        
        error_message = "❌ Произошла ошибка при анализе."
        if "Превышен месячный лимит" in str(e):
            error_message = (
                "❌ Превышен месячный лимит использования сервиса.\n"
                "Обратитесь к администратору для увеличения лимита."
            )
        elif "not found" in str(e).lower():
            error_message = (
                "❌ Не удалось найти данные по вашему запросу.\n"
                "Проверьте правильность ввода и попробуйте снова."
            )
        
        await callback.message.edit_text(
            error_message,
            reply_markup=get_new_analysis_keyboard()
        )
        await state.clear()


# Cancel analysis callback
@router.callback_query(F.data == "cancel_analysis")
async def handle_cancel_analysis(callback: CallbackQuery, state: FSMContext):
    """Handle analysis cancellation."""
    await callback.answer("Операция отменена")
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Анализ отменен",
        reply_markup=get_back_to_main_keyboard()
    )


# New analysis callback
@router.callback_query(F.data == "new_analysis")
async def handle_new_analysis(callback: CallbackQuery, state: FSMContext):
    """Handle new analysis request."""
    await callback.answer()
    await state.clear()
    
    # Delete current message and send welcome
    await callback.message.delete()
    await callback.message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(AnalysisStatesV2.main_menu)


# Back navigation callbacks
@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Handle back to main menu."""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "Выберите тип анализа:",
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(AnalysisStatesV2.main_menu)


@router.callback_query(F.data == "back_to_period")
async def handle_back_to_period(callback: CallbackQuery, state: FSMContext):
    """Handle back to period selection."""
    await callback.answer()
    
    await callback.message.edit_text(
        "📅 За какой период анализировать?",
        reply_markup=get_period_keyboard()
    )
    await state.set_state(AnalysisStatesV2.selecting_period)


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle main menu button."""
    await callback.answer()
    await state.clear()
    
    # Delete and send new message
    await callback.message.delete()
    await callback.message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(AnalysisStatesV2.main_menu)


async def show_generation_mode_selection(message: Message, state: FSMContext, user_data: UserData):
    """Show generation mode selection for URL analysis."""
    # Temporary solution: assume no context for now
    # TODO: Fix UserContextStorage to work with SQLAlchemy async
    has_context = False
    context_summary = None
    
    await message.answer(
        "🎯 Выберите режим генерации сценария:\n\n"
        "🤖 **Без контекста** - базовый анализ\n"
        "📝 **С контекстом** - персонализированный под ваш профиль\n"
        "✍️ **Создать контекст** - заполните информацию о себе",
        reply_markup=get_generation_mode_keyboard(has_context, context_summary),
        parse_mode="Markdown"
    )
    await state.set_state(AnalysisStatesV2.selecting_generation_mode)


# Generation mode selection handlers
@router.callback_query(StateFilter(AnalysisStatesV2.selecting_generation_mode), F.data.startswith("gen_mode:"))
async def handle_generation_mode_selection(callback: CallbackQuery, state: FSMContext):
    """Handle generation mode selection."""
    mode = callback.data.split(":")[1]
    
    # Update user data
    data = await state.get_data()
    user_data = UserData.from_dict(data.get("user_data", {}))
    user_data.generation_mode = mode
    await state.update_data(user_data=user_data.to_dict())
    
    if mode == "no_context":
        await callback.answer("Запускаю анализ без контекста...")
        await start_reel_vision_analysis(callback.message, state, user_data)
    elif mode == "with_context":
        await callback.answer("Запускаю анализ с вашим контекстом...")
        await start_reel_vision_analysis(callback.message, state, user_data)
    elif mode == "create_context":
        await callback.answer("Начинаю сбор контекста...")
        # TODO: Redirect to context collection
        await callback.message.edit_text(
            "📝 Создание контекста пока не реализовано.\n"
            "Выберите другой режим или попробуйте позже.",
            reply_markup=get_generation_mode_keyboard(False)
        )
    
    await callback.answer()


async def start_reel_vision_analysis(message: Message, state: FSMContext, user_data: UserData):
    """Start the full Vision Analysis workflow for a single Reel."""
    status_message = await message.answer(
        "🔄 Запускаю полный анализ рила...\n\n"
        "Этапы:\n"
        "1️⃣ Сбор данных через Apify\n"
        "2️⃣ Анализ визуального контента с AI Vision\n"
        "3️⃣ Генерация персонализированного сценария\n"
        "4️⃣ Создание PDF отчета\n\n"
        "⏳ Это займет 2-3 минуты..."
    )
    
    try:
        # Step 1: Get reel data from Apify
        await status_message.edit_text("1️⃣ Получаю данные рила через Apify...")
        
        result = await apify_direct_service.analyze_reel_url(
            user_data.input_value,
            progress_callback=lambda text: status_message.edit_text(f"1️⃣ {text}")
        )
        
        if not result.reels:
            await status_message.edit_text(
                "❌ Не удалось получить данные рила.\n"
                "Проверьте ссылку и попробуйте снова.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        reel = result.reels[0]  # Get the first (and only) reel
        
        if not reel.video_url:
            await status_message.edit_text(
                "❌ Не удалось получить прямую ссылку на видео.\n"
                "Попробуйте другой рил.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        # Store video URL in user data
        user_data.video_url = reel.video_url
        await state.update_data(user_data=user_data.to_dict())
        
        # Step 2: Vision Analysis
        await status_message.edit_text("2️⃣ Анализирую визуальный контент с AI Vision...")
        
        from src.features.vision_analysis.analyzer import VisionAnalyzer
        from src.utils.config import config
        
        vision_analyzer = VisionAnalyzer(api_key=config.api.openai_api_key)
        vision_result = await vision_analyzer.analyze_reel_by_url(reel.video_url)
        
        if not vision_result or vision_result.get("error"):
            await status_message.edit_text(
                f"❌ Ошибка при анализе видео: {vision_result.get('error', 'Неизвестная ошибка')}\n"
                "Попробуйте позже.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        # Step 3: Generate scenario
        await status_message.edit_text("3️⃣ Генерирую персонализированный сценарий...")
        
        scenario_generator = get_scenario_generator()
        
        # Generate scenario based on mode
        if user_data.generation_mode == "with_context":
            # TODO: Implement context retrieval when UserContextStorage is fixed
            # For now, use basic scenario
            scenario_result = await scenario_generator.generate_complete_scenario(
                reel_data=reel, 
                video_url=reel.video_url
            )
            scenario = scenario_result.original_scenario
        else:
            # Basic scenario without context
            scenario_result = await scenario_generator.generate_complete_scenario(
                reel_data=reel, 
                video_url=reel.video_url
            )
            scenario = scenario_result.original_scenario
        
        if not scenario:
            await status_message.edit_text(
                "❌ Не удалось сгенерировать сценарий.\n"
                "Попробуйте позже.",
                reply_markup=get_new_analysis_keyboard()
            )
            await state.clear()
            return
        
        # Step 4: Skip PDF generation for now due to library issues
        await status_message.edit_text("4️⃣ Подготавливаю результаты...")
        
        # Generate comprehensive results message
        results_message = generate_vision_analysis_message(
            reel=reel,
            vision_result=vision_result,
            scenario=scenario,
            generation_mode=user_data.generation_mode,
            audio_transcript=scenario_result.audio_transcript if scenario_result else None
        )
        
        # Generate and send text report with all scenarios
        await status_message.edit_text("📄 Создаю полный текстовый отчет...")
        
        try:
            # Create mock AnalysisResult for text generator
            class MockAnalysisResult:
                def __init__(self, reel_data, vision_result):
                    self.reels = [reel_data]
                    self.total_views = reel_data.views
                    self.total_likes = reel_data.likes
                    self.average_er = (reel_data.likes / reel_data.views) * 100 if reel_data.views > 0 else 0
                    self.engagement_rate = self.average_er
                    self.popular_hashtags = reel_data.hashtags[:10] if reel_data.hashtags else []
                    self.insights = [
                        f"Анализ {len(self.reels)} Instagram Reel",
                        f"Общий охват: {self.total_views:,} просмотров",
                        f"Уровень вовлеченности: {self.average_er:.2f}%"
                    ]
                    self.recommendations = [
                        "Используйте полученные сценарии для создания собственного контента",
                        "Адаптируйте визуальные элементы под свой стиль",
                        "Учитывайте аудиторию и время публикации оригинального Reel"
                    ]
                    self.usage_cost_usd = 0.05  # Примерная стоимость анализа
                    self.metadata = {
                        'query_type': 'direct_link',
                        'period': 'N/A',
                        'sample_size': 1,
                        'vision_analysis': vision_result.get('visual_analysis', '') if vision_result else ''
                    }
            
            analysis_result = MockAnalysisResult(reel, vision_result)
            
            # Prepare scenarios data
            scenarios = {
                'vision_analysis': vision_result.get('visual_analysis', 'Недоступен') if vision_result else 'Недоступен',
                'audio_transcript': scenario_result.audio_transcript or 'Недоступна',
                'original_scenario': scenario_result.original_scenario or 'Не сгенерирован',
                'variant_scenario': scenario_result.variant_scenario or 'Не сгенерирован', 
                'context_scenario': scenario_result.context_scenario or 'Не сгенерирован'
            }
            
            # Generate simple text report
            report_text = f"""
🎬 Анализ вирусного Reel

📊 Метрики:
• Просмотры: {format_number(reel.views)}
• Лайки: {format_number(reel.likes)}
• Комментарии: {format_number(reel.comments)}
• Шеры: {format_number(reel.shares)}
• ER: {(reel.engagement_rate * 100):.2f}%

✍️ Сгенерированные сценарии:
{scenarios.get('basic_scenario', 'Не сгенерирован')}

🎯 Контекстный сценарий:
{scenarios.get('context_scenario', 'Не сгенерирован')}

🔗 Оригинал: {reel.url}
"""
            
            # Save to file
            from pathlib import Path
            import tempfile
            
            temp_dir = Path("data/reports")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            report_filename = f"viral_analysis_{reel.id}_{message.from_user.id}.txt"
            report_path = temp_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            # Send text file
            from aiogram.types import FSInputFile
            await message.answer_document(
                FSInputFile(report_path),
                caption="📊 Полный отчет анализа с всеми сценариями"
            )
            
            # Clean up file after sending
            report_path.unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Error generating text report: {e}")
        
        # Send results message
        await status_message.edit_text(
            results_message,
            parse_mode="HTML",
            reply_markup=get_new_analysis_keyboard()
        )
        
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in Vision Analysis workflow: {e}", exc_info=True)
        await status_message.edit_text(
            "❌ Произошла ошибка при анализе.\n"
            "Попробуйте позже.",
            reply_markup=get_new_analysis_keyboard()
        )
        await state.clear()


def generate_vision_analysis_message(reel, vision_result, scenario, generation_mode, audio_transcript=None):
    """Generate comprehensive message with Vision Analysis results."""
    
    # Basic reel info
    title = reel.title[:100] + "..." if reel.title and len(reel.title) > 100 else reel.title or "Без названия"
    
    message_parts = [
        "🎬 <b>AI Vision Анализ Reels</b>\n",
        f"📱 <b>Рил:</b> {title}",
        f"👤 <b>Автор:</b> {reel.author_username}",
        f"👀 <b>Просмотры:</b> {reel.views:,}",
        f"❤️ <b>Лайки:</b> {reel.likes:,}",
        f"💬 <b>Комментарии:</b> {reel.comments:,}",
        f"📊 <b>ER:</b> {reel.engagement_rate:.2f}%\n"
    ]
    
    # Visual analysis
    if vision_result.get("visual_analysis"):
        visual_text = vision_result["visual_analysis"][:500] + "..." if len(vision_result["visual_analysis"]) > 500 else vision_result["visual_analysis"]
        message_parts.extend([
            "🔍 <b>Визуальный анализ:</b>",
            f"<i>{visual_text}</i>\n"
        ])
    
    # Patterns
    if vision_result.get("patterns"):
        patterns_text = vision_result["patterns"][:400] + "..." if len(vision_result["patterns"]) > 400 else vision_result["patterns"]
        message_parts.extend([
            "📈 <b>Вирусные паттерны:</b>",
            f"<i>{patterns_text}</i>\n"
        ])
    
    # Audio transcript (Whisper)
    if audio_transcript and audio_transcript != 'Недоступна':
        transcript_text = audio_transcript[:300] + "..." if len(audio_transcript) > 300 else audio_transcript
        message_parts.extend([
            "🎤 <b>Аудио транскрипция (Whisper):</b>",
            f"<i>{transcript_text}</i>\n"
        ])
    
    # Audio analysis
    if vision_result.get("audio_analysis"):
        audio_text = vision_result["audio_analysis"][:300] + "..." if len(vision_result["audio_analysis"]) > 300 else vision_result["audio_analysis"]
        message_parts.extend([
            "🎵 <b>Аудио анализ:</b>",
            f"<i>{audio_text}</i>\n"
        ])
    
    # Generated scenario
    if scenario:
        scenario_text = scenario[:600] + "..." if len(scenario) > 600 else scenario
        mode_text = "С контекстом" if generation_mode == "with_context" else "Без контекста"
        message_parts.extend([
            f"🤖 <b>Сценарий ({mode_text}):</b>",
            f"<i>{scenario_text}</i>\n"
        ])
    
    message_parts.append("📑 <b>Полный отчет в файле ниже</b>")
    
    return "\n".join(message_parts)


# ===========================================
# НОВЫЕ ОБРАБОТЧИКИ ДЛЯ ПОЛНОГО 4-ПРОМТОВОГО WORKFLOW
# ===========================================

@router.callback_query(F.data.startswith("scenario:"))
async def handle_scenario_generation(callback: CallbackQuery, state: FSMContext):
    """Обработка запроса на генерацию сценария для конкретного Reel."""
    try:
        reel_id = callback.data.split(":")[1]
        
        # Получить информацию о пользователе и его контекстах
        user = await db.get_or_create_user(callback.from_user.id)
        context_manager = get_context_manager()
        
        if not context_manager:
            await callback.answer("Сервис контекстов недоступен", show_alert=True)
            return
        
        # Получить контексты пользователя
        contexts = await context_manager.get_user_contexts(user.id)
        
        # Преобразовать в формат для клавиатуры
        contexts_data = []
        for context in contexts:
            contexts_data.append({
                'id': context.id,
                'name': context.name,
                'description': context.description
            })
        
        # Сохранить reel_id в состоянии
        await state.update_data(current_reel_id=reel_id)
        
        text = """🎬 ГЕНЕРАЦИЯ СЦЕНАРИЯ

Выберите контекст для персонализации сценария или создайте новый:"""
        
        await callback.message.edit_text(
            text,
            reply_markup=get_context_selection_keyboard(contexts_data)
        )
        
        await state.set_state(AnalysisStatesV2.selecting_generation_mode)
        
    except Exception as e:
        logger.error(f"Error in scenario generation: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("context:select:"))
async def handle_context_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора контекста для генерации сценария."""
    try:
        context_selection = callback.data.split(":")[2]
        data = await state.get_data()
        reel_id = data.get('current_reel_id')
        
        if not reel_id:
            await callback.answer("Ошибка: не найден ID Reel", show_alert=True)
            return
        
        # Обновить данные состояния
        if context_selection == "none":
            await state.update_data(selected_context_id=None)
            context_text = "без контекста"
        else:
            context_id = int(context_selection)
            await state.update_data(selected_context_id=context_id)
            
            # Получить название контекста для отображения
            user = await db.get_or_create_user(callback.from_user.id)
            context_manager = get_context_manager()
            context = await context_manager.get_context_by_id(user.id, context_id)
            context_text = f"с контекстом '{context.name}'" if context else "с выбранным контекстом"
        
        text = f"""✅ Выбран режим: {context_text}

📄 Выберите формат получения сценария:"""
        
        await callback.message.edit_text(
            text,
            reply_markup=get_scenario_format_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in context selection: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("scenario_format:"))
async def handle_scenario_format_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора формата генерации сценария."""
    try:
        format_type = callback.data.split(":")[1]
        data = await state.get_data()
        reel_id = data.get('current_reel_id')
        context_id = data.get('selected_context_id')
        
        if not reel_id:
            await callback.answer("Ошибка: не найден ID Reel", show_alert=True)
            return
        
        # Показать сообщение о начале генерации
        status_message = await callback.message.edit_text(
            "🔄 Генерируем сценарий...\n\n"
            "⏱ Это может занять 1-2 минуты\n"
            "🧠 Анализируем видео, аудио и создаем сценарии"
        )
        
        # Получить данные Reel из последнего отчета пользователя
        user = await db.get_or_create_user(callback.from_user.id)
        last_report = await db.get_last_user_report(user.id)
        
        if not last_report or not hasattr(last_report, 'analysis_result'):
            await status_message.edit_text(
                "❌ Не найдены данные для анализа\n"
                "Сначала выполните анализ Reels",
                reply_markup=get_new_analysis_keyboard()
            )
            return
        
        # Найти нужный Reel в результатах
        target_reel = None
        for reel in last_report.analysis_result.reels:
            if reel.id == reel_id:
                target_reel = reel
                break
        
        if not target_reel:
            await status_message.edit_text(
                "❌ Reel не найден в результатах анализа",
                reply_markup=get_new_analysis_keyboard()
            )
            return
        
        # Генерация сценариев
        scenario_generator = get_scenario_generator()
        if not scenario_generator:
            await status_message.edit_text(
                "❌ Сервис генерации сценариев недоступен",
                reply_markup=get_new_analysis_keyboard()
            )
            return
        
        # Запустить полную генерацию сценариев
        scenario_result = await scenario_generator.generate_complete_scenario(
            reel_data=target_reel,
            video_url=target_reel.video_url,
            user_id=user.id if context_id else None,
            context_id=context_id
        )
        
        if scenario_result.error_message:
            await status_message.edit_text(
                f"❌ Ошибка при генерации сценариев:\n{scenario_result.error_message}",
                reply_markup=get_new_analysis_keyboard()
            )
            return
        
        # Подготовить данные для отчета
        scenarios_data = {
            'vision_analysis': scenario_result.vision_analysis,
            'original_scenario': scenario_result.original_scenario,
            'variant_scenario': scenario_result.variant_scenario,
            'context_scenario': scenario_result.context_scenario
        }
        
        reel_info = f"{target_reel.author_username} - {target_reel.title[:50]}..."
        
        if format_type == "file":
            # Генерация текстового файла
            report_text = f"""
🎬 Анализ сценариев для Reel
{reel_info}

🔬 AI Vision анализ:
{scenarios_data.get('vision_analysis', 'Не проводился')}

✍️ Оригинальный сценарий:
{scenarios_data.get('original_scenario', 'Не сгенерирован')}

🎯 Вариативный сценарий:
{scenarios_data.get('variant_scenario', 'Не сгенерирован')}

📝 Контекстный сценарий:
{scenarios_data.get('context_scenario', 'Не сгенерирован')}

Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            # Отправить как документ
            from io import BytesIO
            import re
            
            file_content = report_text.encode('utf-8')
            file_name = f"scenarios_{target_reel.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            
            file_obj = BytesIO(file_content)
            file_obj.name = file_name
            
            await status_message.edit_text(
                "✅ Сценарии готовы!\n📄 Отправляю файл..."
            )
            
            await callback.message.answer_document(
                document=file_obj,
                caption=f"🎬 Сценарии для Reel от {target_reel.author_username}"
            )
            
            await status_message.edit_text(
                "✅ Сценарии успешно сгенерированы!",
                reply_markup=get_new_analysis_keyboard()
            )
            
        else:  # format_type == "message"
            # Отправка в сообщениях
            if scenario_result.vision_analysis:
                await callback.message.answer(
                    f"👁️ **ВИЗУАЛЬНЫЙ АНАЛИЗ**\n\n{scenario_result.vision_analysis[:3000]}"
                )
            
            if scenario_result.original_scenario:
                await callback.message.answer(
                    f"🎯 **СЦЕНАРИЙ ОРИГИНАЛА**\n\n{scenario_result.original_scenario[:3000]}"
                )
            
            if scenario_result.variant_scenario:
                await callback.message.answer(
                    f"🔄 **ВАРИАТИВНЫЙ СЦЕНАРИЙ**\n\n{scenario_result.variant_scenario[:3000]}"
                )
            
            if scenario_result.context_scenario:
                await callback.message.answer(
                    f"💼 **ПЕРСОНАЛИЗИРОВАННЫЙ СЦЕНАРИЙ**\n\n{scenario_result.context_scenario[:3000]}"
                )
            
            await status_message.edit_text(
                f"✅ Сценарии готовы!\n⏱ Время обработки: {scenario_result.processing_time_seconds:.1f}с",
                reply_markup=get_new_analysis_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in scenario format selection: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при генерации сценариев",
            reply_markup=get_new_analysis_keyboard()
        )
        await state.clear()