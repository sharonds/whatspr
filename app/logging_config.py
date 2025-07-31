import logging, structlog, sys

def scrub_pii(logger, _, event):
    for k in ("phone", "email"):
        if k in event:
            event[k] = "***"
    return event

def configure_logging(level=logging.INFO):
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=level)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            scrub_pii,
            structlog.processors.JSONRenderer(),
        ],
    )