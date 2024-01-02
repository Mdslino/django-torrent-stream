bind = "0.0.0.0:8000"
workers = 4
worker_class = "gevent"
accesslog = "-"
errorlog = "-"
loglevel = "info"
preload_app = True

import logging.config
import os

import structlog

timestamper = structlog.processors.TimeStamper(fmt="iso")
pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry is not from structlog.
    structlog.stdlib.add_log_level,
    timestamper,
]

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=False),
            "foreign_pre_chain": pre_chain,
        },
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": pre_chain,
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": True}
    },
})

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


class GunicornLogger(object):
    def __init__(self, cfg):
        self._error_logger = structlog.get_logger("gunicorn.error")
        self._error_logger.setLevel(logging.INFO)
        self._access_logger = structlog.get_logger("gunicorn.access")
        self._access_logger.setLevel(logging.INFO)
        self.cfg = cfg

    def critical(self, msg, *args, **kwargs) -> None:
        self._error_logger.error(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs) -> None:
        self._error_logger.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        self._error_logger.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:
        self._error_logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs) -> None:
        self._error_logger.debug(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs) -> None:
        self._error_logger.exception(msg, *args, **kwargs)

    def log(self, lvl, msg, *args, **kwargs) -> None:
        self._error_logger.log(lvl, msg, *args, **kwargs)

    def access(self, resp, req, environ, request_time) -> None:
        status = resp.status
        if isinstance(status, str):
            status = status.split(None, 1)[0]

        self._access_logger.info(
            "request",
            method=environ["REQUEST_METHOD"],
            request_uri=environ["RAW_URI"],
            status=status,
            response_length=getattr(resp, "sent", None),
            request_time_seconds="%d.%06d"
            % (request_time.seconds, request_time.microseconds),
            pid="<%s>" % os.getpid(),
        )

    def reopen_files(self) -> None:
        pass  # we don't support files

    def close_on_exec(self) -> None:
        pass  # we don't support files


logger_class = GunicornLogger
