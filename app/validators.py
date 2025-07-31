import re
from typing import Optional, Tuple

REGEXS = {
    "money": re.compile(r'^\$?\d[\d,\.]*[mk]?$' , re.I),
    "email": re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$'),
}

def validate(slot_id: str, value: str, rule: Optional[str] = None) -> Tuple[bool, str]:
    if not rule or rule == "free":
        return True, ""
    if rule == "choice":
        return True, ""
    rx = REGEXS.get(rule)
    if rx and rx.match(value.strip()):
        return True, ""
    hint = {
        "money": "Please include a currency symbol and magnitude, e.g. $3.5M.",
        "email": "Need a full email like name@example.com.",
    }.get(rule, "Please rephrase.")
    return False, hint