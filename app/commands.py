"""Command parsing and handling utilities for WhatsApp interactions.

Provides command recognition and response generation for user commands
like help, reset, and field changes in conversation flow.
"""

from typing import Optional
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse


def _tw(text: str) -> Response:
    """Create a TwiML response with the given message text."""
    r = MessagingResponse()
    r.message(text)
    return Response(str(r), media_type="application/xml")


def handle_help(current_slot: Optional[str] = None):
    """Handle help command, showing available commands and slot-specific examples."""
    extra = f"\n/example – example answer for {current_slot}" if current_slot else ""
    return _tw(
        "Commands:\n/reset – start over\n/change – change category\n/help – this help" + extra
    )


def handle_reset(current_slot: Optional[str] = None):
    """Handle reset command, clearing the current session."""
    return _tw("Session reset. Send any message to start again.")


def handle_change(current_slot: Optional[str] = None):
    """Handle change command, allowing user to pick a different category."""
    return _tw("Sure—let's choose a different category. Reply with 1, 2, or 3.")


# Command aliases mapping - enhanced with more aliases
COMMANDS = {
    "/help": handle_help,
    "/h": handle_help,
    "help": handle_help,
    "/reset": handle_reset,
    "reset": handle_reset,
    "/change": handle_change,
    "change": handle_change,
    "/cancel": handle_reset,
    "stop": handle_reset,
}


def maybe_command(body: str, current_slot: Optional[str] = None):
    """Check if the message is a command and handle it if so.

    Args:
        body: The message text to check
        current_slot: The current slot being asked about (for context-specific help)

    Returns:
        TwiML Response if command was handled, None otherwise
    """
    token = body.lower().split()[0]
    if token in COMMANDS:
        return COMMANDS[token](current_slot)
    return None
