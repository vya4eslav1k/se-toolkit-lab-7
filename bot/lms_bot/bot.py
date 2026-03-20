"""
Telegram bot entry point with --test mode support.

Usage:
    uv run bot.py --test "/start"    # Test mode, prints response to stdout
    uv run bot.py                    # Production mode, connects to Telegram
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "handlers"))

from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)
from lms_bot.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def handle_command(command: str) -> str:
    """
    Route a command string to the appropriate handler.
    
    This is the core routing logic that works in both --test mode
    and production Telegram mode.
    """
    parts = command.strip().split()
    if not parts:
        return "Empty command"
    
    cmd = parts[0].lower()
    
    if cmd == "/start":
        return handle_start()
    elif cmd == "/help":
        return handle_help()
    elif cmd == "/health":
        return handle_health()
    elif cmd == "/labs":
        return handle_labs()
    elif cmd == "/scores":
        lab_name = parts[1] if len(parts) > 1 else ""
        return handle_scores(lab_name)
    else:
        return f"Unknown command: {cmd}. Use /help for available commands."


def run_test_mode(command: str) -> None:
    """
    Run a command in test mode - print response to stdout and exit.
    
    This allows testing handlers without connecting to Telegram.
    """
    response = handle_command(command)
    print(response)


async def run_production_mode() -> None:
    """
    Run the bot in production mode - connect to Telegram using aiogram.
    """
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    
    config = load_config()
    bot_token = config["BOT_TOKEN"]
    
    if not bot_token:
        logger.error("BOT_TOKEN not found. Please set it in .env.bot.secret")
        sys.exit(1)
    
    logger.info(f"Starting bot with token: {bot_token[:10]}...")
    
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Register command handlers
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message) -> None:
        response = handle_start()
        await message.answer(response)
    
    @dp.message(Command("help"))
    async def cmd_help(message: types.Message) -> None:
        response = handle_help()
        await message.answer(response)
    
    @dp.message(Command("health"))
    async def cmd_health(message: types.Message) -> None:
        response = handle_health()
        await message.answer(response)
    
    @dp.message(Command("labs"))
    async def cmd_labs(message: types.Message) -> None:
        response = handle_labs()
        await message.answer(response)
    
    @dp.message(Command("scores"))
    async def cmd_scores(message: types.Message) -> None:
        # Extract lab name from command arguments
        lab_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
        response = handle_scores(lab_name)
        await message.answer(response)
    
    # Start polling
    logger.info("Bot is now polling for messages...")
    await dp.start_polling(bot)


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="LMS Telegram Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run bot.py --test "/start"
    uv run bot.py --test "/help"
    uv run bot.py --test "/health"
    uv run bot.py                    # Production mode
        """
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Run in test mode with the given command (e.g., '/start')"
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_test_mode(args.test)
    else:
        asyncio.run(run_production_mode())


if __name__ == "__main__":
    main()
