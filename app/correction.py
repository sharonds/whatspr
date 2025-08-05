"""Message correction detection and extraction utilities.

Handles user corrections in chat messages using patterns like asterisk
prefixes or 'I meant' phrases for updating previous responses.
"""


def is_correction(msg: str) -> bool:
    """Check if message indicates a correction to previous input.

    Args:
        msg: Message text to check.

    Returns:
        bool: True if message appears to be a correction.
    """
    return msg.startswith("*") or msg.lower().startswith("i meant")


def extract_correction(msg: str) -> str:
    """Extract corrected text from correction message.

    Args:
        msg: Correction message to extract from.

    Returns:
        str: Extracted correction text.
    """
    if msg.startswith("*"):
        return msg[1:].strip()
    if msg.lower().startswith("i meant"):
        return msg.split(" ", 2)[-1].strip()
    return msg
