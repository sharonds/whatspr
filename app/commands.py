from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse


def _tw(text: str) -> Response:
    r = MessagingResponse()
    r.message(text)
    return Response(str(r), media_type="application/xml")


def handle_help(current_slot: str | None = None):
    extra = f"\n/example – example answer for {current_slot}" if current_slot else ""
    return _tw(
        "Commands:\n/reset – start over\n/help – this message\n/change – change category" + extra
    )


def handle_reset():
    return _tw("Session reset. Type any message to begin again.")


def handle_change():
    return _tw("Sure—let’s choose a different category. Type 1 Funding · 2 Product · 3 Partnership")


COMMANDS = {
    "/help": handle_help,
    "/reset": handle_reset,
    "/change": handle_change,
}


def maybe_command(body: str, current_slot: str | None = None):
    token = body.lower().split()[0]
    if token in COMMANDS:
        return COMMANDS[token](current_slot)
    return None
