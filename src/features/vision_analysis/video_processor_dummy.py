"""
Заглушка для VideoProcessor без зависимости от cv2
"""

class VideoProcessor:
    """Заглушка для video processor"""
    
    def __init__(self):
        pass
    
    async def extract_frames(self, video_path: str):
        """Заглушка для извлечения кадров"""
        return []