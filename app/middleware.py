import uuid
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger("middleware")


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = uuid.uuid4().hex[:8]
        start = time.time()
        log.info("start", id=rid, path=request.url.path)
        try:
            resp: Response = await call_next(request)
            resp_text = getattr(resp, "body", b"")[:200]
            log.info("response_sample", id=rid, body=resp_text.decode(errors="ignore"))
            log.info(
                "end", id=rid, status=resp.status_code, latency_ms=int((time.time() - start) * 1000)
            )
            return resp
        except Exception as e:
            log.error("error", id=rid, error=str(e), latency_ms=int((time.time() - start) * 1000))
            raise
