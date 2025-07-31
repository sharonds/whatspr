from .validators import validate
from .config import settings

def validate_local(name: str, value: str) -> dict:
    # assume slot spec is in settings.flow
    slot = next(s for s in settings.flow['slots'] if s['id']==name)
    rule = slot.get('validator', {}).get('type', 'free')
    ok, hint = validate(name, value, rule)
    return {"accepted": ok, "hint": hint}