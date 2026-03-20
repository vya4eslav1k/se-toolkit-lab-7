"""
Configuration loader for the bot.

Loads environment variables from .env.bot.secret file.
This pattern keeps secrets out of version control.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_config() -> dict[str, str]:
    """
    Load configuration from environment variables.
    
    Returns a dict with keys:
        BOT_TOKEN, LMS_API_URL, LMS_API_KEY, 
        LLM_API_KEY, LLM_API_BASE_URL, LLM_API_MODEL
    """
    # Load from .env.bot.secret in the bot directory
    bot_dir = Path(__file__).parent
    env_file = bot_dir / ".env.bot.secret"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Also try parent directory (for deployment)
        parent_env = bot_dir.parent / ".env.bot.secret"
        if parent_env.exists():
            load_dotenv(parent_env)
    
    return {
        "BOT_TOKEN": os.getenv("BOT_TOKEN", ""),
        "LMS_API_URL": os.getenv("LMS_API_URL", "http://localhost:42002"),
        "LMS_API_KEY": os.getenv("LMS_API_KEY", ""),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
        "LLM_API_BASE_URL": os.getenv("LLM_API_BASE_URL", ""),
        "LLM_API_MODEL": os.getenv("LLM_API_MODEL", ""),
    }
