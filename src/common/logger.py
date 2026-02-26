"""Structured JSON logger.

Wraps structlog to provide consistent structured logging across the application.
Compatible with the _shared/services/logger interface contract.
No print() statements — use this module everywhere.
"""

import structlog


def setup_logging(*, json_output: bool = True, log_level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Args:
        json_output: If True, output JSON-formatted logs. False for human-readable dev output.
        log_level: Minimum log level to emit.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named logger instance.

    Args:
        name: Logger name, typically the module name.

    Returns:
        Bound structured logger instance.
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
