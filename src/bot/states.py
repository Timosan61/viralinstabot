"""FSM states for the updated bot."""

from aiogram.fsm.state import State, StatesGroup


class AnalysisStatesV2(StatesGroup):
    """States for Instagram analysis flow."""
    
    # Main menu - waiting for analysis type selection
    main_menu = State()
    
    # Waiting for user input based on analysis type
    waiting_for_account = State()
    waiting_for_hashtag = State()
    waiting_for_location = State()
    waiting_for_reel_url = State()
    
    # Period selection
    selecting_period = State()
    
    # Sample size selection
    selecting_sample_size = State()
    
    # Confirmation
    confirming_analysis = State()
    
    # Processing
    processing = State()

    # Vision Analysis and Context-Aware Scenario Generation
    vision_analysis_start = State()
    collecting_user_context = State()
    confirm_user_context = State()
    generating_vision_scenario = State()
    
    # New states for URL Vision Analysis workflow
    selecting_generation_mode = State()
    processing_vision_analysis = State()


class UserContextStates(StatesGroup):
    """States for collecting user context for content generation."""
    niche = State()
    audience = State()
    unique_value = State()
    content_style = State()
    resources = State()
    goals = State()
    confirmation = State()


class ContextManagementStates(StatesGroup):
    """States for managing user contexts."""
    
    # Создание контекста
    creating_name = State()
    creating_description = State() 
    creating_data = State()
    confirming_creation = State()
    
    # Редактирование контекста
    editing_name = State()
    editing_description = State()
    editing_data = State()
    
    # Просмотр и выбор контекстов
    viewing_contexts = State()
    selecting_context = State()



class UserData:
    """Container for user analysis data."""
    
    def __init__(self):
        self.analysis_type = None  # @account, #hashtag, location, url
        self.input_value = None    # username, hashtag, location name, or URL
        self.period_days = None    # 3, 7, or 14
        self.sample_size = None    # 50, 100, or 200
        self.price_rub = None      # Calculated price
        
        # Vision Analysis fields
        self.generation_mode = None    # "no_context", "context_1", "context_2", etc.
        self.selected_context_id = None  # ID of selected user context
        self.video_url = None         # Direct video URL from Apify
        
    def reset(self):
        """Reset all data."""
        self.analysis_type = None
        self.input_value = None
        self.period_days = None
        self.sample_size = None
        self.price_rub = None
        self.generation_mode = None
        self.selected_context_id = None
        self.video_url = None
        
    def is_complete(self) -> bool:
        """Check if all required data is collected."""
        if self.analysis_type == "url":
            # URL analysis doesn't need period/sample size
            return self.input_value is not None
        else:
            return all([
                self.analysis_type,
                self.input_value,
                self.period_days is not None,
                self.sample_size is not None
            ])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "analysis_type": self.analysis_type,
            "input_value": self.input_value,
            "period_days": self.period_days,
            "sample_size": self.sample_size,
            "price_rub": self.price_rub,
            "generation_mode": self.generation_mode,
            "selected_context_id": self.selected_context_id,
            "video_url": self.video_url
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserData':
        """Create from dictionary."""
        user_data = cls()
        user_data.analysis_type = data.get("analysis_type")
        user_data.input_value = data.get("input_value")
        user_data.period_days = data.get("period_days")
        user_data.sample_size = data.get("sample_size")
        user_data.price_rub = data.get("price_rub")
        user_data.generation_mode = data.get("generation_mode")
        user_data.selected_context_id = data.get("selected_context_id")
        user_data.video_url = data.get("video_url")
        return user_data