"""Handler modules for the LMS bot."""

from .slash.commands import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_natural_language,
    get_start_keyboard,
)

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_natural_language",
    "get_start_keyboard",
]
