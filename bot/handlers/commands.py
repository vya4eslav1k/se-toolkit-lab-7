"""
Command handlers for the LMS bot.

These are pure functions that take input and return text.
They don't depend on Telegram - same logic works from:
- --test mode (CLI)
- Unit tests
- Telegram bot
"""


def handle_start() -> str:
    """Handle /start command - welcome message."""
    return "Welcome to the LMS Bot! Use /help to see available commands."


def handle_help() -> str:
    """Handle /help command - list available commands."""
    return """Available commands:
/start - Welcome message
/help - Show this help message
/health - Check backend status
/labs - List available labs
/scores <lab> - View scores for a lab"""


def handle_health() -> str:
    """Handle /health command - check backend status."""
    # Placeholder - will be implemented in Task 2
    return "Backend status: Not implemented yet"


def handle_labs() -> str:
    """Handle /labs command - list available labs."""
    # Placeholder - will be implemented in Task 2
    return "Available labs: Not implemented yet"


def handle_scores(lab_name: str = "") -> str:
    """Handle /scores command - view scores for a lab."""
    # Placeholder - will be implemented in Task 2
    if lab_name:
        return f"Scores for {lab_name}: Not implemented yet"
    return "Please specify a lab name, e.g., /scores lab-04"
