import structlog, io, logging


class LogCapture:
    def __enter__(self):
        self.buffer = io.StringIO()
        handler = logging.StreamHandler(self.buffer)
        logging.getLogger().addHandler(handler)
        self.handler = handler
        return self

    def __exit__(self, exc_type, exc, tb):
        logging.getLogger().removeHandler(self.handler)

    def text(self):
        return self.buffer.getvalue()
