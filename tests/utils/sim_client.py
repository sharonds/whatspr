from fastapi.testclient import TestClient
from app.main import app
import itertools
from tests.utils.rate_limiter import get_rate_limiter

_sid_counter = itertools.count(1000)


class WhatsSim:
    """Lightweight WhatsApp simulator for pytest with rate limiting."""

    def __init__(self, phone: str = "+15551234567", rate_limited: bool = True):
        self.client = TestClient(app)
        self.phone = phone
        self.rate_limited = rate_limited
        if rate_limited:
            # Get a rate limiter for this client instance
            self.rate_limiter = get_rate_limiter(
                f"sim_client_{phone}",
                calls_per_second=0.3,  # Conservative rate for API calls
                burst_size=2,
            )

    def send(self, body: str, num_media: int = 0) -> str:
        sid = f"SM{next(_sid_counter)}"

        # Apply rate limiting if enabled
        if self.rate_limited:
            self.rate_limiter.acquire()

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
