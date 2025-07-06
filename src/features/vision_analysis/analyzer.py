"""GPT-4 Vision analyzer for Instagram Reels."""

import logging
from typing import List, Optional, Dict, Any
import httpx
import json
from datetime import datetime

from .prompts import VISION_SYSTEM_PROMPT, VISION_ANALYSIS_PROMPT, VISUAL_PATTERNS_PROMPT, AUDIO_ANALYSIS_PROMPT
from .video_processor import VideoProcessor
from src.domain.models import ReelData

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """Analyze Instagram Reels using GPT-4 Vision API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize analyzer with OpenAI API credentials.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for vision analysis
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.video_processor = VideoProcessor()
    
    async def analyze_reel(self, reel: ReelData, video_url: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive analysis of Instagram Reel.
        
        Args:
            reel: ReelData object with reel information
            video_url: Direct URL to video file (if available)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            analysis_result = {
                "reel_id": reel.id,
                "visual_analysis": None,
                "audio_analysis": None,
                "patterns": None,
                "error": None
            }
            
            # Download video if URL provided
            if video_url:
                try:
                    logger.info(f"Downloading video for reel {reel.id}")
                    video_path = await self.video_processor.download_video(video_url)
                    
                    # Extract key frames
                    logger.info("Extracting key frames")
                    frame_paths = self.video_processor.extract_key_frames(video_path, num_frames=5)
                    
                    # Convert frames to base64
                    base64_frames = self.video_processor.frames_to_base64(frame_paths)
                    
                    # Analyze frames
                    logger.info("Analyzing frames with GPT-4 Vision")
                    visual_analysis = await self._analyze_frames(base64_frames)
                    analysis_result["visual_analysis"] = visual_analysis
                    
                except Exception as e:
                    logger.warning(f"Could not download/analyze video for reel {reel.id}: {e}")
                    analysis_result["visual_analysis"] = "Видео анализ недоступен - не удалось загрузить видеофайл"
                    analysis_result["error"] = f"Video download failed: {str(e)}"
                
                # Extract patterns
                if visual_analysis:
                    patterns = await self._extract_patterns(visual_analysis)
                    analysis_result["patterns"] = patterns
                
                # Clean up temp files
                self.video_processor.cleanup_temp_files(frame_paths + [video_path])
            
            # Analyze transcript if available
            if reel.transcript:
                logger.info("Analyzing transcript")
                audio_analysis = await self._analyze_transcript(reel.transcript)
                analysis_result["audio_analysis"] = audio_analysis
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in full analysis for reel {reel.id}: {e}", exc_info=True)
            return {"error": str(e)}

    async def analyze_reel_by_url(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Shortcut to analyze a reel directly from a video URL.

        Args:
            video_url: The direct URL to the video file.

        Returns:
            A dictionary with analysis results or None on failure.
        """
        from datetime import datetime
        mock_reel = ReelData(
            id="from_url", 
            title="Vision Analysis Reel",
            author="Unknown",
            author_username="unknown",
            url=video_url, 
            video_url=video_url, 
            views=0, 
            likes=0, 
            comments=0,
            shares=0,
            engagement_rate=0.0,
            date=datetime.now()
        )
        return await self.analyze_reel(mock_reel, video_url)
    
    async def _analyze_frames(self, base64_frames: List[str]) -> Optional[str]:
        """Analyze video frames using GPT-4 Vision.
        
        Args:
            base64_frames: List of base64 encoded frame images
            
        Returns:
            Analysis text or None
        """
        try:
            # Prepare messages with images
            messages = [
                {
                    "role": "system",
                    "content": VISION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": VISION_ANALYSIS_PROMPT
                        }
                    ]
                }
            ]
            
            # Add images to the message
            for i, frame_base64 in enumerate(base64_frames):
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame_base64}",
                        "detail": "high"
                    }
                })
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 1500,
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
            
            if response.status_code == 200:
                data = response.json()
                analysis = data["choices"][0]["message"]["content"]
                logger.info("Successfully analyzed frames")
                return analysis
            else:
                logger.error(f"Vision API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in frame analysis: {str(e)}")
            return None
    
    async def _extract_patterns(self, visual_analysis: str) -> Optional[str]:
        """Extract success patterns from visual analysis.
        
        Args:
            visual_analysis: Previous visual analysis text
            
        Returns:
            Patterns text or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты эксперт по созданию вирусного контента."
                            },
                            {
                                "role": "user",
                                "content": f"{VISUAL_PATTERNS_PROMPT}\n\nАнализ:\n{visual_analysis}"
                            }
                        ],
                        "max_tokens": 800,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                patterns = data["choices"][0]["message"]["content"]
                return patterns
            else:
                logger.error(f"Patterns API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting patterns: {str(e)}")
            return None
    
    async def _analyze_transcript(self, transcript: str) -> Optional[str]:
        """Analyze audio transcript.
        
        Args:
            transcript: Audio transcript text
            
        Returns:
            Analysis text or None
        """
        try:
            prompt = AUDIO_ANALYSIS_PROMPT.format(transcript=transcript)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты эксперт по анализу контента в социальных сетях."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 600,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                analysis = data["choices"][0]["message"]["content"]
                return analysis
            else:
                logger.error(f"Audio analysis API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return None
    
    def format_analysis_for_display(self, analysis_result: Dict[str, Any]) -> str:
        """Format analysis results for display to user.
        
        Args:
            analysis_result: Analysis results dictionary
            
        Returns:
            Formatted text
        """
        sections = []
        
        if analysis_result.get("visual_analysis"):
            sections.append(analysis_result["visual_analysis"])
        
        if analysis_result.get("audio_analysis"):
            sections.append(f"\n🎤 АНАЛИЗ АУДИО\n\n{analysis_result['audio_analysis']}")
        
        if analysis_result.get("patterns"):
            sections.append(f"\n📊 ПАТТЕРНЫ УСПЕХА\n\n{analysis_result['patterns']}")
        
        if analysis_result.get("error"):
            sections.append(f"\n❌ Ошибка анализа: {analysis_result['error']}")
        
        return "\n".join(sections) if sections else "Анализ не выполнен"