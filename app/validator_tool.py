from .validators import validate
from .config import settings

RETRIES = {}


def validate_local(name: str, value: str):
    try:
        if settings.flow and 'slots' in settings.flow:
            slot = next(s for s in settings.flow['slots'] if s['id'] == name)
            rule = slot.get('validator')
        else:
            # Default rule based on field name
            if 'email' in name.lower():
                rule = 'email_phone'
            elif 'money' in name.lower() or 'amount' in name.lower():
                rule = 'money'
            else:
                rule = 'free'
    except (StopIteration, KeyError, TypeError):
        # Default rule based on field name or use appropriate validation
        if 'email' in name.lower():
            rule = 'email_phone'
        elif 'money' in name.lower() or 'amount' in name.lower():
            rule = 'money'
        else:
            rule = 'free'

    ok, hint = validate(name, value, rule)
    if ok:
        RETRIES.pop(name, None)
        return {"accepted": True, "hint": ""}
    
    # Only apply retry logic if we have slot config
    try:
        if settings.flow and 'slots' in settings.flow:
            slot = next(s for s in settings.flow['slots'] if s['id'] == name)
            max_r = (
                slot.get('validator', {}).get('max_retries', 1)
                if isinstance(slot.get('validator'), dict)
                else 1
            )
        else:
            max_r = 1
    except (StopIteration, KeyError, TypeError):
        max_r = 1
        
    RETRIES[name] = RETRIES.get(name, 0) + 1
    if RETRIES[name] >= max_r:
        return {"accepted": True, "hint": ""}
    return {"accepted": False, "hint": hint}
