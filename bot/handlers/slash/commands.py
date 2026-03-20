"""
Command handlers for the LMS bot.

These are pure functions that take input and return text.
They don't depend on Telegram - same logic works from:
- --test mode (CLI)
- Unit tests
- Telegram bot
"""

from services.api_client import LmsApiClient, LmsApiError
from config import load_config


def _get_api_client() -> LmsApiClient:
    """Create an API client from config."""
    config = load_config()
    return LmsApiClient(
        base_url=config["LMS_API_URL"],
        api_key=config["LMS_API_KEY"],
    )


def handle_start() -> str:
    """Handle /start command - welcome message."""
    config = load_config()
    bot_name = config.get("BOT_TOKEN", "").split(":")[0] if config.get("BOT_TOKEN") else "LMS"
    return f"Welcome to the LMS Bot! Use /help to see available commands."


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
    client = _get_api_client()
    try:
        result = client.health_check()
        if result["healthy"]:
            return f"Backend is healthy. {result['item_count']} items available."
        else:
            return "Backend returned an unexpected response."
    except LmsApiError as e:
        return f"Backend error: {e.message}"


def handle_labs() -> str:
    """Handle /labs command - list available labs."""
    client = _get_api_client()
    try:
        items = client.get_items()
        labs = [item for item in items if item.get("type") == "lab"]
        
        if not labs:
            return "No labs available."
        
        lines = ["Available labs:"]
        for lab in labs:
            title = lab.get("title", "Unknown")
            lines.append(f"- {title}")
        
        return "\n".join(lines)
    except LmsApiError as e:
        return f"Backend error: {e.message}"


def handle_scores(lab_name: str = "") -> str:
    """Handle /scores command - view scores for a lab."""
    if not lab_name:
        return "Please specify a lab name, e.g., /scores lab-04"

    client = _get_api_client()
    try:
        pass_rates = client.get_pass_rates(lab_name)

        if not pass_rates:
            return f"No scores found for '{lab_name}'."

        lines = [f"Pass rates for {lab_name}:"]
        for task in pass_rates:
            task_name = task.get("task", "Unknown task")
            avg_score = task.get("avg_score", 0)
            attempts = task.get("attempts", 0)
            lines.append(f"- {task_name}: {avg_score:.1f}% ({attempts} attempts)")

        return "\n".join(lines)
    except LmsApiError as e:
        return f"Backend error: {e.message}"


def handle_start() -> str:
    """Handle /start command - welcome message with keyboard hint."""
    return """Welcome to the LMS Bot! I can help you with:

• Slash commands: /health, /labs, /scores <lab>
• Natural language questions like:
  - "what labs are available?"
  - "show me scores for lab 4"
  - "which lab has the lowest pass rate?"

Use /help for more information."""


def get_start_keyboard():
    """Get inline keyboard buttons for the /start command."""
    return [
        [{"text": "📊 Check Health", "callback_data": "health"}],
        [{"text": "📚 View Labs", "callback_data": "labs"}],
        [{"text": "🏆 Lab 04 Scores", "callback_data": "scores_lab-04"}],
        [{"text": "❓ Help", "callback_data": "help"}],
    ]


def handle_natural_language(message: str) -> str:
    """
    Handle natural language queries using LLM intent routing.

    The LLM decides which tools to call based on the user's message.
    Tool results are fed back to the LLM for final answer generation.
    """
    from handlers.slash.intent_router import IntentRouter

    try:
        router = IntentRouter()
        return router.route(message)
    except Exception as e:
        return f"Error processing query: {type(e).__name__}: {e}"
