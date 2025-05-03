import logging
from datetime import datetime
from typing import Optional

class F1Logger:
    """Logging utility for F1 Agent with structured context logging."""
    
    def __init__(self, name: str = "F1RacerAI"):
        self.logger = logging.getLogger(name)
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Initialize logger configuration once."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(action)-15s | %(response)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _log(
        self,
        level: int,
        action: str,
        response: str,
        exc_info: Optional[Exception] = None
    ) -> None:
        """Base logging method implementing DRY principle."""
        self.logger.log(
            level,
            extra={
                'action': action,
                'response': response
            },
            exc_info=exc_info
        )

    def info(self, action: str, response: str) -> None:
        """Log informational message."""
        self._log(logging.INFO, action, response)

    def warn(self, action: str, response: str) -> None:
        """Log warning message."""
        self._log(logging.WARNING, action, response)

    def error(self, action: str, response: str, exc: Optional[Exception] = None) -> None:
        """Log error message with optional exception."""
        self._log(logging.ERROR, action, response, exc_info=exc)