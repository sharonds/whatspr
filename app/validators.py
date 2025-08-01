import re
from typing import Union, Optional

REGEXS = {
    "money": re.compile(r'^\$?\d[\d,\.]*\s?(?:[mk]|million)?$', re.I),
    "email_phone": re.compile(r'^.+@.+\..+.*\+?[0-9][0-9\-\s]{6,}$', re.I),
}


def validate(slot_id: str, value: str, rule: Union[str, dict, None] = None):
    """Return (accepted: bool, hint: str)"""
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
