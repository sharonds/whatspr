"""Message preprocessing and TwiML response utilities.

Provides message cleaning, emoji filtering, and TwiML response generation
for WhatsApp message processing with length validation and sanitization.
"""

import re
from typing import Optional
import structlog
from twilio.twiml.messaging_response import MessagingResponse
from fastapi.responses import Response

log = structlog.get_logger("prefilter")

MAX_LEN = 1000
EMOJI_RE = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)


def twiml(text: str) -> Response:
    """Create a TwiML response for WhatsApp messaging.

    Args:
        text: Message text to send back to WhatsApp user.

    Returns:
        Response: FastAPI response with TwiML XML content.
    """
    r = MessagingResponse()
    r.message(text)
    return Response(str(r), media_type="application/xml")


def clean_message(raw: str) -> Optional[str]:
    """Clean and validate incoming message text.

    Args:
        raw: The raw message text

    Returns:
        Cleaned message text or None if invalid (too long, empty, etc.)
    """
    if len(raw) > MAX_LEN:
        return None
    no_emoji = EMOJI_RE.sub("", raw)
    return no_emoji.strip() or None
