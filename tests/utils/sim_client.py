from fastapi.testclient import TestClient
from app.main import app
import itertools

_sid_counter = itertools.count(1000)


class WhatsSim:
    """Lightweight WhatsApp simulator for pytest"""

    def __init__(self, phone: str = "+15551234567"):
        self.client = TestClient(app)
        self.phone = phone

    def send(self, body: str, num_media: int = 0) -> str:
        sid = f"SM{next(_sid_counter)}"
        resp = self.client.post(
            "/agent",  # primary endpoint
            data={
                "From": self.phone,
                "Body": body,
                "MessageSid": sid,
                "NumMedia": str(num_media),
            },
        )
        return resp.text  # TwiML XML
