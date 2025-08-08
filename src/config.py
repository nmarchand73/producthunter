"""
Configuration management for ProductHunt CLI tool.

Handles environment variables, API keys, and application settings.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration."""
    # Anthropic API settings
    anthropic_api_key: Optional[str] = None
    ai_analysis_mode: str = "quick"
    max_daily_ai_cost: float = 10.0
    ai_model: str = "claude-3-haiku-20240307"
    
    # Output settings
    output_dir: str = "./data"
    log_level: str = "INFO"
    
    # Scraping settings
    scraping_delay: float = 1.0
    max_retries: int = 3
    user_agent: str = "ProductHunt Daily Recap CLI Tool v1.0"
    
    # Optional webhook for notifications
    webhook_url: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.ai_analysis_mode not in ["quick", "detailed", "market-focus"]:
            raise ValueError(f"Invalid AI analysis mode: {self.ai_analysis_mode}")
        
        if self.max_daily_ai_cost <= 0:
            raise ValueError("Max daily AI cost must be positive")
        
        if self.scraping_delay < 0:
            raise ValueError("Scraping delay must be non-negative")


def load_config() -> Config:
    """Load configuration from environment variables.
    
    Returns:
        Config instance with values from environment
    """
    try:
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        config = Config(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            ai_analysis_mode=os.getenv("AI_ANALYSIS_MODE", "quick"),
            max_daily_ai_cost=float(os.getenv("MAX_DAILY_AI_COST", "10.0")),
            ai_model=os.getenv("AI_MODEL", "claude-3-haiku-20240307"),
            output_dir=os.getenv("OUTPUT_DIR", "./data"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            scraping_delay=float(os.getenv("SCRAPING_DELAY", "1.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            user_agent=os.getenv("USER_AGENT", "ProductHunt Daily Recap CLI Tool v1.0"),
            webhook_url=os.getenv("WEBHOOK_URL")
        )
        
        logger.info("Configuration loaded successfully")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


def load_dotenv():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        logger.debug("Loading environment variables from .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def validate_config(config: Config) -> None:
    """Validate configuration and warn about missing required values.
    
    Args:
        config: Configuration to validate
    """
    warnings = []
    
    if not config.anthropic_api_key:
        warnings.append("ANTHROPIC_API_KEY not set - AI analysis will be disabled")
    
    if not Path(config.output_dir).exists():
        logger.info(f"Creating output directory: {config.output_dir}")
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    for warning in warnings:
        logger.warning(warning)
