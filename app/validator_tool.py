from .validators import validate
from .config import settings


def validate_local(name: str, value: str) -> dict:
    # Try to find slot spec in settings.flow, default to appropriate rule for generic validation
    try:
        if settings.flow and 'slots' in settings.flow:
            slot = next(s for s in settings.flow['slots'] if s['id'] == name)
            rule = slot.get('validator', {}).get('type', 'free')
        else:
            raise StopIteration
    except (StopIteration, KeyError, TypeError):
        # Default rule based on field name or use appropriate validation
        if 'email' in name.lower():
            rule = 'email'
        elif 'money' in name.lower() or 'amount' in name.lower():
            rule = 'money'
        else:
            rule = 'free'

    ok, hint = validate(name, value, rule)
    return {"accepted": ok, "hint": hint}
