"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class BotConfig(BaseModel):
    """Bot configuration."""
    name: str
    username: str


class APIConfig(BaseModel):
    """API tokens configuration."""
    telegram_token: str
    openai_api_key: str
    apify_token: str


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000


class ApifyConfig(BaseModel):
    """Apify configuration."""
    actor_id: str
    default_params: Dict[str, Any]


class LimitsConfig(BaseModel):
    """Limits and timeouts configuration."""
    max_requests_per_user: int = 10
    max_clarification_iterations: int = 3
    agent_timeout_seconds: int = 30
    pdf_max_size_mb: int = 5
    reels_per_analysis: int = 5


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str
    report_retention_days: int = 30


class PricingConfig(BaseModel):
    """Pricing configuration."""
    usd_to_rub: float = 90.0
    markup_multiplier: int = 2


class TimeoutsConfig(BaseModel):
    """Timeouts configuration."""
    default: int = 30
    apify_run: int = 120
    pdf_generation: int = 60


class MCPServerConfig(BaseModel):
    """MCP Server configuration."""
    command: str
    args: list[str]
    env: Dict[str, str]


class MCPConfig(BaseModel):
    """MCP configuration."""
    servers: Dict[str, MCPServerConfig]


class Config(BaseSettings):
    """Main configuration."""
    bot: BotConfig
    api: APIConfig
    openai: OpenAIConfig
    apify: ApifyConfig
    limits: LimitsConfig
    database: DatabaseConfig
    pricing: PricingConfig
    timeouts: TimeoutsConfig
    mcp: MCPConfig
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


def load_config() -> Config:
    """Load configuration from YAML file and environment."""
    config_path = Path("config/bot.yml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        yaml_config = yaml.safe_load(f)
    
    # Replace environment variables in config
    def replace_env_vars(obj: Any) -> Any:
        if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            if ":" in env_var:
                var_name, default = env_var.split(":", 1)
                return os.getenv(var_name, default)
            return os.getenv(env_var, obj)
        elif isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        return obj
    
    yaml_config = replace_env_vars(yaml_config)
    
    # Override with environment variables
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        yaml_config["api"]["telegram_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("OPENAI_API_KEY"):
        yaml_config["api"]["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("APIFY_API_TOKEN"):
        yaml_config["api"]["apify_token"] = os.getenv("APIFY_API_TOKEN")
    
    return Config(**yaml_config)


# Global config instance
config = load_config()