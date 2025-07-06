"""
Генератор сценариев с полным workflow из 4 промтов.
Включает AI Vision анализ, Whisper транскрипцию и интеграцию с контекстами пользователя.
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx
from openai import AsyncOpenAI

from .prompts import (
    VISION_SYSTEM_PROMPT,
    VISION_ANALYSIS_PROMPT,
    ORIGINAL_SCENARIO_PROMPT,
    VARIANT_SCENARIO_PROMPT,
    CONTEXT_BASED_SCENARIO_PROMPT
)
from .video_processor import VideoProcessor
# Whisper service removed
from src.features.user_context import get_context_manager
from src.domain.models import ReelData
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScenarioResult:
    """Результат генерации сценариев."""
    
    vision_analysis: Optional[str] = None
    original_scenario: Optional[str] = None
    variant_scenario: Optional[str] = None
    context_scenario: Optional[str] = None
    audio_transcript: Optional[str] = None
    user_context: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class ScenarioGenerator:
    """Генератор сценариев с полным 4-промтовым workflow."""
    
    def __init__(self, openai_api_key: str):
        """
        Инициализация генератора сценариев.
        
        Args:
            openai_api_key: API ключ OpenAI
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.video_processor = VideoProcessor()
        self.max_frames = 8  # Максимум кадров для анализа
        
    async def generate_complete_scenario(
        self,
        reel_data: ReelData,
        video_url: Optional[str] = None,
        user_id: Optional[int] = None,
        context_id: Optional[int] = None
    ) -> ScenarioResult:
        """
        Генерация полного сценария с использованием всех 4 промтов.
        
        Args:
            reel_data: Данные о Reel
            video_url: Прямая ссылка на видео для Vision анализа
            user_id: ID пользователя для получения контекста
            context_id: ID конкретного контекста пользователя
            
        Returns:
            Результат генерации со всеми сценариями
        """
        start_time = datetime.now()
        result = ScenarioResult()
        
        try:
            logger.info(f"Starting complete scenario generation for reel {reel_data.id}")
            
            # Шаг 1: Анализ видео с AI Vision (если есть URL)
            if video_url:
                try:
                    result.vision_analysis = await self._generate_vision_analysis(video_url)
                    logger.info("Vision analysis completed")
                except Exception as e:
                    logger.warning(f"Vision analysis failed: {e}")
                    result.vision_analysis = "Визуальный анализ недоступен"
            
            # Шаг 2: Транскрипция аудио (если есть видео)
            if video_url:
                try:
                    result.audio_transcript = await self._transcribe_audio(video_url)
                    logger.info("Audio transcription completed")
                except Exception as e:
                    logger.warning(f"Audio transcription failed: {e}")
                    result.audio_transcript = "Аудио транскрипция недоступна"
            
            # Шаг 3: Получить контекст пользователя (если указан)
            if user_id and context_id:
                result.user_context = await self._get_user_context(user_id, context_id)
                logger.info("User context retrieved")
            
            # Шаг 4: Генерация оригинального сценария
            result.original_scenario = await self._generate_original_scenario(
                reel_data=reel_data,
                vision_analysis=result.vision_analysis,
                audio_transcript=result.audio_transcript
            )
            logger.info("Original scenario generated")
            
            # Шаг 5: Генерация вариативного сценария
            if result.original_scenario:
                result.variant_scenario = await self._generate_variant_scenario(
                    original_scenario=result.original_scenario,
                    vision_analysis=result.vision_analysis
                )
                logger.info("Variant scenario generated")
            
            # Шаг 6: Генерация персонализированного сценария (если есть контекст)
            if result.user_context and result.original_scenario and result.variant_scenario:
                result.context_scenario = await self._generate_context_scenario(
                    original_scenario=result.original_scenario,
                    variant_scenario=result.variant_scenario,
                    user_context=result.user_context
                )
                logger.info("Context-based scenario generated")
            
            # Подсчитать время обработки
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            
            logger.info(f"Complete scenario generation finished in {result.processing_time_seconds:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in complete scenario generation: {e}")
            result.error_message = str(e)
            return result
    
    async def _generate_vision_analysis(self, video_url: str) -> Optional[str]:
        """Генерация анализа визуальной составляющей."""
        try:
            # Скачать видео во временный файл
            video_path = await self._download_video(video_url)
            if not video_path:
                logger.error("Failed to download video for vision analysis")
                return None
            
            try:
                # Извлечь кадры из видео
                frames_base64 = await self._extract_video_frames(video_path)
                if not frames_base64:
                    logger.error("Failed to extract frames from video")
                    return None
                
                # Подготовить содержимое для GPT-4o
                content = [{"type": "text", "text": VISION_ANALYSIS_PROMPT}]
                
                # Добавить изображения
                for frame_base64 in frames_base64:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_base64}",
                            "detail": "high"
                        }
                    })
                
                # Отправить запрос к GPT-4o
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": VISION_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                
                return response.choices[0].message.content
                
            finally:
                # Очистить временный файл
                if os.path.exists(video_path):
                    os.unlink(video_path)
                    
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return None
    
    async def _transcribe_audio(self, video_url: str) -> Optional[str]:
        """Транскрипция аудио из видео (заглушка)."""
        # Whisper service removed - return placeholder
        logger.info("Audio transcription not available")
        return None
    
    async def _get_user_context(self, user_id: int, context_id: int) -> Optional[str]:
        """Получить контекст пользователя."""
        try:
            context_manager = get_context_manager()
            if not context_manager:
                logger.warning("Context manager not available")
                return None
            
            context = await context_manager.get_context_by_id(user_id, context_id)
            if context:
                return context.context_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return None
    
    async def _generate_original_scenario(
        self,
        reel_data: ReelData,
        vision_analysis: Optional[str] = None,
        audio_transcript: Optional[str] = None
    ) -> Optional[str]:
        """Генерация сценария оригинального Reel."""
        try:
            # Подготовить данные для промта
            prompt = ORIGINAL_SCENARIO_PROMPT.format(
                vision_analysis=vision_analysis or "Визуальный анализ не доступен"
            )
            
            # Отправить запрос к GPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating original scenario: {e}")
            return None
    
    async def _generate_variant_scenario(
        self,
        original_scenario: str,
        vision_analysis: Optional[str] = None
    ) -> Optional[str]:
        """Генерация вариативного сценария."""
        try:
            prompt = VARIANT_SCENARIO_PROMPT.format(
                original_scenario=original_scenario,
                visual_analysis=vision_analysis or "Визуальный анализ не доступен"
            )
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.8  # Немного больше креативности
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating variant scenario: {e}")
            return None
    
    async def _generate_context_scenario(
        self,
        original_scenario: str,
        variant_scenario: str,
        user_context: str
    ) -> Optional[str]:
        """Генерация персонализированного сценария."""
        try:
            prompt = CONTEXT_BASED_SCENARIO_PROMPT.format(
                original_scenario=original_scenario,
                variant_scenario=variant_scenario,
                user_context=user_context
            )
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating context scenario: {e}")
            return None
    
    async def _download_video(self, video_url: str) -> Optional[str]:
        """Скачать видео во временный файл."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(video_url)
                response.raise_for_status()
                
                # Создать временный файл
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".mp4",
                    delete=False
                )
                temp_file.write(response.content)
                temp_file.close()
                
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    async def _extract_video_frames(self, video_path: str) -> List[str]:
        """Извлечь кадры из видео и конвертировать в base64."""
        import subprocess
        import base64
        
        try:
            frames_base64 = []
            
            # Извлечь кадры с помощью ffmpeg
            for i in range(self.max_frames):
                # Создать временный файл для кадра
                frame_file = tempfile.NamedTemporaryFile(
                    suffix=".jpg",
                    delete=False
                )
                frame_file.close()
                
                try:
                    # Вычислить время кадра (равномерно распределить по видео)
                    seek_time = i * (100 / self.max_frames) / 100  # Процент от длины видео
                    
                    # Команда ffmpeg для извлечения кадра
                    ffmpeg_path = self.video_processor.ffmpeg_path
                    if not ffmpeg_path:
                        raise FileNotFoundError("FFmpeg not found")
                    
                    cmd = [
                        ffmpeg_path,
                        "-i", video_path,
                        "-ss", f"{seek_time}%",
                        "-vframes", "1",
                        "-q:v", "2",  # Высокое качество
                        "-y",
                        frame_file.name
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0 and os.path.exists(frame_file.name):
                        # Прочитать и конвертировать в base64
                        with open(frame_file.name, 'rb') as f:
                            frame_data = f.read()
                            frame_base64 = base64.b64encode(frame_data).decode('utf-8')
                            frames_base64.append(frame_base64)
                
                finally:
                    # Очистить временный файл кадра
                    if os.path.exists(frame_file.name):
                        os.unlink(frame_file.name)
            
            logger.info(f"Extracted {len(frames_base64)} frames from video")
            return frames_base64
            
        except Exception as e:
            logger.error(f"Error extracting video frames: {e}")
            return []


# Глобальный экземпляр
scenario_generator: Optional[ScenarioGenerator] = None


def initialize_scenario_generator(openai_api_key: str) -> ScenarioGenerator:
    """
    Инициализация глобального экземпляра генератора сценариев.
    
    Args:
        openai_api_key: OpenAI API ключ
        
    Returns:
        Экземпляр ScenarioGenerator
    """
    global scenario_generator
    scenario_generator = ScenarioGenerator(openai_api_key)
    return scenario_generator


def get_scenario_generator() -> Optional[ScenarioGenerator]:
    """
    Получение глобального экземпляра генератора сценариев.
    
    Returns:
        Экземпляр ScenarioGenerator или None если не инициализирован
    """
    return scenario_generator