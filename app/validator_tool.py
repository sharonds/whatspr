from .validators import validate
from .config import settings

RETRIES = {}

def validate_local(name: str, value: str):
    slot = next(s for s in settings.flow['slots'] if s['id']==name)
    rule = slot.get('validator')
    ok, hint = validate(name, value, rule)
    if ok:
        RETRIES.pop(name, None)
        return {"accepted": True, "hint": ""}
    max_r = slot.get('validator',{}).get('max_retries',1) if isinstance(slot.get('validator'),dict) else 1
    RETRIES[name] = RETRIES.get(name,0)+1
    if RETRIES[name] >= max_r:
        return {"accepted": True, "hint": ""}
    return {"accepted": False, "hint": hint}