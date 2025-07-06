"""Video processing utilities for Instagram Reels."""

import logging
import os
import tempfile
import base64
from typing import List, Optional, Tuple
from urllib.parse import urlparse
import httpx
import cv2
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process Instagram Reels videos for analysis."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize video processor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)
        self.ffmpeg_path = self._find_ffmpeg()
        
    async def download_video(self, url: str) -> str:
        """Download video from URL.
        
        Args:
            url: Video URL
            
        Returns:
            Path to downloaded video file
        """
        try:
            # Generate temp filename
            parsed_url = urlparse(url)
            filename = f"reel_{hash(url)}.mp4"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Check if already downloaded
            if os.path.exists(filepath):
                logger.info(f"Video already cached: {filepath}")
                return filepath
            
            # Download video
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=60)
                response.raise_for_status()
                
                # Save to file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded video to: {filepath}")
                return filepath
                
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise
    
    def extract_frames(self, video_path: str, fps: float = 0.5, max_frames: int = 10) -> List[str]:
        """Extract frames from video.
        
        Args:
            video_path: Path to video file
            fps: Frames per second to extract (0.5 = 1 frame every 2 seconds)
            max_frames: Maximum number of frames to extract
            
        Returns:
            List of paths to extracted frame images
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Get video properties
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / video_fps if video_fps > 0 else 0
            
            logger.info(f"Video info: {duration:.1f}s, {video_fps:.1f} fps, {total_frames} frames")
            
            # Calculate frame interval
            frame_interval = int(video_fps / fps) if fps < video_fps else 1
            
            frame_paths = []
            frame_count = 0
            
            for i in range(0, total_frames, frame_interval):
                if frame_count >= max_frames:
                    break
                    
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if ret:
                    # Save frame
                    frame_filename = f"frame_{hash(video_path)}_{i}.jpg"
                    frame_path = os.path.join(self.temp_dir, frame_filename)
                    
                    # Resize if too large (max 1920x1080)
                    height, width = frame.shape[:2]
                    if width > 1920 or height > 1080:
                        scale = min(1920/width, 1080/height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frame_paths)} frames")
            return frame_paths
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            raise
    
    def extract_key_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Extract key frames at specific intervals.
        
        Args:
            video_path: Path to video file
            num_frames: Number of key frames to extract
            
        Returns:
            List of paths to key frame images
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frame positions
            if total_frames <= num_frames:
                positions = list(range(total_frames))
            else:
                interval = total_frames // num_frames
                positions = [i * interval for i in range(num_frames)]
                # Add last frame
                if positions[-1] < total_frames - 1:
                    positions[-1] = total_frames - 1
            
            frame_paths = []
            
            for pos in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ret, frame = cap.read()
                
                if ret:
                    frame_filename = f"keyframe_{hash(video_path)}_{pos}.jpg"
                    frame_path = os.path.join(self.temp_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
            
            cap.release()
            return frame_paths
            
        except Exception as e:
            logger.error(f"Error extracting key frames: {str(e)}")
            raise
    
    def frames_to_base64(self, frame_paths: List[str]) -> List[str]:
        """Convert frame images to base64 strings.
        
        Args:
            frame_paths: List of paths to frame images
            
        Returns:
            List of base64 encoded images
        """
        base64_images = []
        
        for path in frame_paths:
            try:
                with open(path, 'rb') as f:
                    image_data = f.read()
                    base64_str = base64.b64encode(image_data).decode('utf-8')
                    base64_images.append(base64_str)
            except Exception as e:
                logger.error(f"Error encoding frame {path}: {str(e)}")
                
        return base64_images
    
    def extract_thumbnail(self, video_path: str, position: float = 0.1) -> Optional[str]:
        """Extract thumbnail from video.
        
        Args:
            video_path: Path to video file
            position: Position in video (0.0-1.0) to extract thumbnail
            
        Returns:
            Path to thumbnail image or None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Get frame at position
            frame_pos = int(total_frames * position)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                thumb_filename = f"thumb_{hash(video_path)}.jpg"
                thumb_path = os.path.join(self.temp_dir, thumb_filename)
                cv2.imwrite(thumb_path, frame)
                return thumb_path
                
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {str(e)}")
            
        return None
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            info = {
                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            }
            
            cap.release()
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files.
        
        Args:
            file_paths: List of file paths to delete
        """
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.debug(f"Deleted temp file: {path}")
            except Exception as e:
                logger.error(f"Error deleting {path}: {str(e)}")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """
        Поиск FFmpeg в системе (локальный -> системный).
        
        Returns:
            Путь к FFmpeg или None если не найден
        """
        import subprocess
        
        # Попробуем локальный FFmpeg (из корня проекта)  
        project_root = Path(__file__).parent.parent.parent.parent.absolute()
        local_ffmpeg = project_root / "bin" / "ffmpeg"
        if local_ffmpeg.exists():
            logger.info(f"Using local FFmpeg: {local_ffmpeg}")
            return str(local_ffmpeg)
        
        # Попробуем системный FFmpeg
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                system_ffmpeg = result.stdout.strip()
                logger.info(f"Using system FFmpeg: {system_ffmpeg}")
                return system_ffmpeg
        except Exception:
            pass
        
        logger.warning("FFmpeg not found")
        return None