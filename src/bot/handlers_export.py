"""Handlers for export functionality."""

import logging
import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from src.features.export.json_export import JsonExporter
from src.storage.sqlite import db
from src.utils.logger import get_logger
from src.utils.message_formatter import format_reel_scenario_message
from src.utils.formatters import format_number, format_percentage
from src.bot.keyboards import get_back_to_main_keyboard

logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data.startswith("export_"))
async def handle_export(callback: CallbackQuery, state: FSMContext):
    """Handle export button clicks from analytics message."""
    try:
        # Parse export format from callback data
        format_type = callback.data.split("_")[1]  # excel, csv, or json
        
        # Get user's last report from database
        user = await db.get_or_create_user(telegram_id=callback.from_user.id)
        last_report = await db.get_last_user_report(user.id)
        
        if not last_report:
            await callback.answer("❌ Отчет не найден", show_alert=True)
            return
        
        # Get analysis result and raw data
        analysis_result = last_report.analysis_result
        # Raw data is not stored in database, pass empty list
        raw_data = []
        
        # Only JSON export is supported
        if format_type == "json":
            exporter = JsonExporter()
            await callback.answer("📋 Генерирую JSON файл...")
        else:
            await callback.answer("❌ Поддерживается только JSON формат", show_alert=True)
            return
        
        # Export data (not async)
        export_path = exporter.export(analysis_result, raw_data)
        
        # Send file to user
        with open(export_path, "rb") as export_file:
            await callback.message.answer_document(
                document=FSInputFile(export_path, filename=export_path.name),
                caption=f"✅ Данные экспортированы в формате {format_type.upper()}\n\n"
                        f"📊 Всего записей: {len(analysis_result.reels)}"
            )
        
        # Clean up file after sending
        os.remove(export_path)
        
    except Exception as e:
        logger.error(f"Error during export: {e}")
        await callback.answer(
            "❌ Ошибка при экспорте данных",
            show_alert=True
        )


@router.callback_query(F.data == "download_pdf")
async def handle_download_pdf(callback: CallbackQuery, state: FSMContext):
    """Handle PDF download button."""
    try:
        # Get user's last report
        user = await db.get_or_create_user(telegram_id=callback.from_user.id)
        last_report = await db.get_last_user_report(user.id)
        
        if not last_report or not last_report.pdf_path:
            await callback.answer("❌ PDF отчет не найден", show_alert=True)
            return
        
        # Check if file exists
        pdf_path = Path(last_report.pdf_path)
        if not pdf_path.exists():
            await callback.answer("❌ Файл отчета не найден", show_alert=True)
            return
        
        await callback.answer("📑 Отправляю PDF отчет...")
        
        # Send PDF
        with open(pdf_path, "rb") as pdf_file:
            await callback.message.answer_document(
                document=FSInputFile(pdf_path, filename=f"reels_analysis_{last_report.id}.pdf"),
                caption="📑 Полный PDF отчет с кликабельными ссылками"
            )
    
    except Exception as e:
        logger.error(f"Error sending PDF: {e}")
        await callback.answer("❌ Ошибка при отправке PDF", show_alert=True)


@router.callback_query(F.data == "download_excel")
async def handle_download_excel(callback: CallbackQuery, state: FSMContext):
    """Handle Excel download from PDF report."""
    await handle_export(callback, state)


@router.callback_query(F.data.startswith("scenario:"))
async def handle_scenario_view(callback: CallbackQuery, state: FSMContext):
    """Handle scenario view for individual reels."""
    try:
        # Parse reel ID from callback data
        reel_id = callback.data.split(":")[1]
        
        # Get user's last report
        user = await db.get_or_create_user(telegram_id=callback.from_user.id)
        last_report = await db.get_last_user_report(user.id)
        
        if not last_report:
            await callback.answer("❌ Отчет не найден", show_alert=True)
            return
        
        # Find the reel in the report
        analysis_result = last_report.analysis_result
        reel = None
        for r in analysis_result.reels:
            if str(r.id) == reel_id or r.url.endswith(reel_id):
                reel = r
                break
        
        if not reel:
            await callback.answer("❌ Reel не найден", show_alert=True)
            return
        
        # Generate scenario (placeholder for now)
        scenario_text = f"""
🎬 <b>Вирусный сценарий на основе анализа</b>

<b>Хук (0-3 сек):</b>
Начните с провокационного вопроса или утверждения, которое заставит зрителя остановиться.

<b>Основная часть (3-15 сек):</b>
• Покажите проблему или ситуацию
• Добавьте эмоциональный элемент
• Используйте быстрые переходы

<b>Кульминация (15-25 сек):</b>
Неожиданный поворот или решение проблемы.

<b>Призыв к действию (25-30 сек):</b>
Задайте вопрос или предложите поделиться мнением в комментариях.

<b>Ключевые элементы успеха:</b>
✅ Просмотры: {format_number(reel.views)}
✅ ER: {format_percentage(reel.engagement_rate)}
✅ Тренды: использованы актуальные звуки и эффекты
"""
        
        # Send scenario message
        await callback.message.answer(
            format_reel_scenario_message(scenario_text, reel.url),
            parse_mode="HTML",
            reply_markup=get_back_to_main_keyboard()
        )
        
        await callback.answer("✍️ Сценарий сгенерирован")
        
    except Exception as e:
        logger.error(f"Error showing scenario: {e}")
        await callback.answer("❌ Ошибка при генерации сценария", show_alert=True)