import logging


class SafeExtraFormatter(logging.Formatter):
    def format(self, record):
        defaults = {
            "provider": "-",
            "model": "-",
            "duration_ms": "-",
            "input_tokens": "-",
            "output_tokens": "-",
            "attempt": "-",
            "next_attempt": "-",
            "error_type": "-",
        }

        for field, default in defaults.items():
            if not hasattr(record, field):
                setattr(record, field, default)

        return super().format(record)