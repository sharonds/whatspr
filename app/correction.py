def is_correction(msg:str)->bool:
    return msg.startswith('*') or msg.lower().startswith('i meant')

def extract_correction(msg:str)->str:
    if msg.startswith('*'):
        return msg[1:].strip()
    if msg.lower().startswith('i meant'):
        return msg.split(' ',2)[-1].strip()
    return msg