"""Input validation utilities for press release data collection.

Provides validation functions with regex patterns for different data types
like monetary amounts and contact information with helpful user feedback.
"""

import re
from typing import Union

REGEXS = {
    "money": re.compile(r"^\$?\d[\d,\.]*\s?(?:[mk]|million)?$", re.I),
    "email_phone": re.compile(r"^.+@.+\..+.*\+?[0-9][0-9\-\s]{6,}$", re.I),
}


def validate(slot_id: str, value: str, rule: Union[str, dict, None] = None):
    """Validate user input against specified rules with helpful hints.

    Args:
        slot_id: Field identifier (not currently used in validation).
        value: User input value to validate.
        rule: Validation rule - string, dict with type/min_len, or None.

    Returns:
        tuple: (accepted: bool, hint: str) with validation result and feedback.
    """
    if rule is None or rule == "free":
        return True, ""
    if isinstance(rule, dict):
        rtype = rule.get("type", "free")
        min_len = rule.get("min_len", 0)
    else:
        rtype, min_len = rule, 0

    if min_len and len(value) < min_len:
        return False, f"Answer must be at least {min_len} characters."

    if rtype == "free" or rtype == "min_len":
        return True, ""

    rx = REGEXS.get(rtype)
    if rx and rx.match(value.strip()):
        return True, ""
    hints = {
        "money": "Use a currency symbol and magnitude, e.g. $3.5 M.",
        "email_phone": "Format: Name – email – phone (+country).",
    }
    return False, hints.get(rtype, "Please rephrase.")
