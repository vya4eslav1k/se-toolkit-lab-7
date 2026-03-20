#!/usr/bin/env python3
"""
Wrapper script to run the LMS Telegram bot.

Usage:
    uv run bot.py --test "/start"    # Test mode
    uv run bot.py                    # Production mode
"""

import sys
from pathlib import Path

# Add the bot directory to path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from lms_bot.bot import main

if __name__ == "__main__":
    main()
