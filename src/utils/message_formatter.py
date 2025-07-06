"""Telegram message formatter for analytics display."""

from typing import List, Optional
from src.domain.models import AnalysisResult, ReelData
from src.utils.formatters import format_number, format_percentage


def format_analytics_header(username: str, avatar_url: Optional[str] = None) -> str:
    """Format analytics header with user info."""
    return f"📊 <b>Аналитика Reels</b> @{username}\n"


def format_general_stats(
    result: AnalysisResult,
    period_days: int,
    sample_size: int
) -> str:
    """Format general statistics section."""
    total_likes = sum(r.likes for r in result.reels)
    total_comments = sum(r.comments for r in result.reels)
    avg_er = sum(r.engagement_rate for r in result.reels) / len(result.reels) if result.reels else 0
    
    # Get followers count (might be 0 if not available)
    followers = getattr(result, 'followers_count', 0)
    
    stats = f"""
📋 <b>Общая статистика</b>

👁 <b>Общие просмотры:</b> {format_number(result.total_views)}
❤️ <b>Общие лайки:</b> {format_number(total_likes)}
💬 <b>Общие комментарии:</b> {format_number(total_comments)}
📈 <b>Средний ER:</b> {format_percentage(avg_er)}"""
    
    # Add followers only if available
    if followers > 0:
        stats = f"""
📋 <b>Общая статистика</b>

👥 <b>Подписчики:</b> {format_number(followers)}
👁 <b>Общие просмотры:</b> {format_number(result.total_views)}
❤️ <b>Общие лайки:</b> {format_number(total_likes)}
💬 <b>Общие комментарии:</b> {format_number(total_comments)}
📈 <b>Средний ER:</b> {format_percentage(avg_er)}"""
    
    stats += f"""

📊 <b>Выборка:</b> {len(result.reels)} из {sample_size}
⏱ <b>Период:</b> {period_days} дней
📅 <b>Дата:</b> {result.created_at.strftime('%d.%m.%Y')}
"""
    return stats


def format_reel_details(reel: ReelData, index: int) -> str:
    """Format individual reel details."""
    
    # Format engagement rate
    er_text = f"{format_percentage(reel.engagement_rate)}"
    
    # Format description preview - use title if available
    desc_preview = reel.title if hasattr(reel, 'title') and reel.title else ""
    if len(desc_preview) > 100:
        desc_preview = desc_preview[:100] + "..."
    desc_lines = desc_preview.split('\n')
    if len(desc_lines) > 2:
        desc_preview = '\n'.join(desc_lines[:2]) + "..."
    
    reel_text = f"""
<b>{index}.</b> <a href="{reel.url}">{reel.url.split('/')[-2][:20]}...</a>

👁 <b>Просмотры:</b> {format_number(reel.views)}
❤️ <b>Лайки:</b> {format_number(reel.likes)}
💬 <b>Комментарии:</b> {format_number(reel.comments)}
📈 <b>ER:</b> {er_text}

📝 <b>Описание:</b>
<i>{desc_preview}</i>
"""
    
    # Add scenario button info if available
    if hasattr(reel, 'has_scenario') and reel.has_scenario:
        reel_text += "\n✍️ <b>Сценарий доступен</b>"
    
    return reel_text


def format_export_section() -> str:
    """Format export buttons section."""
    return """
📥 <b>Экспорт данных</b>

Выберите формат для скачивания:
"""


def format_full_analytics_message(
    result: AnalysisResult,
    username: str,
    period_days: int,
    sample_size: int,
    max_reels_to_show: int = 3
) -> str:
    """Format complete analytics message with all sections."""
    
    # Header
    message = format_analytics_header(username)
    
    # General stats
    message += format_general_stats(result, period_days, sample_size)
    
    # Top reels
    message += f"\n🏆 <b>Топ {min(max_reels_to_show, len(result.reels))} Reels</b>\n"
    
    # Show top N reels
    for i, reel in enumerate(result.reels[:max_reels_to_show], 1):
        message += format_reel_details(reel, i)
    
    if len(result.reels) > max_reels_to_show:
        message += f"\n<i>... и еще {len(result.reels) - max_reels_to_show} Reels в полном отчете</i>\n"
    
    # Export section
    message += format_export_section()
    
    return message


def format_reel_scenario_message(scenario_text: str, reel_url: str) -> str:
    """Format scenario display message."""
    return f"""
🎬 <b>Сценарий для Reel</b>

<a href="{reel_url}">Оригинальный Reel</a>

{scenario_text}

💡 <i>Используйте этот сценарий как основу для создания своего уникального контента</i>
"""


def format_error_message(error_type: str, suggestion: str = "") -> str:
    """Format error messages."""
    base_errors = {
        "no_data": "❌ Не найдено данных для анализа",
        "limit_exceeded": "❌ Превышен лимит запросов",
        "invalid_input": "❌ Неверный формат данных",
        "api_error": "❌ Ошибка при получении данных"
    }
    
    error_msg = base_errors.get(error_type, "❌ Произошла ошибка")
    
    if suggestion:
        error_msg += f"\n\n💡 {suggestion}"
    
    return error_msg