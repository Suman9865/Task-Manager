
import logging
import logging.config

from app.request_context import get_request_id


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True


def setup_logging():
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "filters": {
            "request_id": {
                "()": RequestIDFilter
            }
        },

        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "[Request ID: %(request_id)s] - %(message)s"
                )
            }
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "filters": ["request_id"],
                "level": "DEBUG"
            }
        },

        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False
            }
        }
    })
