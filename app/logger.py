"""
Centralized Logging Configuration
=================================

Provides a centralized logger factory for the calculator application.

The primary goal of this module is to ensure that the entire application shares
a single, consistent logging setup. All modules should obtain their logger via
the `get_logger(name)` function. This creates a parent-child relationship
with the root "calculator" logger, ensuring that all log messages are processed
by the same handlers and formatters.

Logger Hierarchy Example:
  - `calculator` (root application logger)
    - `calculator.repl` (for the REPL interface)
    - `calculator.history` (for history events)
    - ... and so on for other modules.
"""

from __future__ import annotations
import logging
import os

# This flag ensures that the logging configuration is applied only once per application run.
_is_configured = False

# Default logging settings, used if not overridden by configuration.
_DEFAULT_LOG_DIR = "logs"
_DEFAULT_LOG_FILE = "calculator.log"
_DEFAULT_ENCODING = "utf-8"
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    log_dir: str = _DEFAULT_LOG_DIR,
    log_file: str = _DEFAULT_LOG_FILE,
    encoding: str = _DEFAULT_ENCODING,
    level: int = logging.INFO,
) -> None:
    """
    Configures the root 'calculator' logger with file and stream handlers.

    This function is safe to call multiple times; it will only configure the
    logger on the first call. It sets up a `FileHandler` to log all messages
    (from the specified level) to a file and a `StreamHandler` to output messages
    of WARNING level and higher to the console.

    Args:
        log_dir (str): The directory where the log file will be created.
        log_file (str): The name of the log file.
        encoding (str): The file encoding for the log file.
        level (int): The minimum log level to be captured by the file handler.
    """
    global _is_configured
    if _is_configured:
        return

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Get the root logger for the application namespace.
    root_logger = logging.getLogger("calculator")
    root_logger.setLevel(level)

    # Create a consistent formatter for all handlers.
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # File handler: Captures all logs from the specified level.
    file_handler = logging.FileHandler(log_path, encoding=encoding)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    _is_configured = True


def reconfigure_logging(**kwargs) -> None:
    """
    Force-reconfigures the root 'calculator' logger.

    This function is useful when settings (like the log file path) change after
    the initial configuration, for instance, after loading a `.env` file. It
    resets the configuration and applies new settings.

    Args:
        **kwargs: Keyword arguments matching the parameters of `configure_logging`.
    """
    global _is_configured
    root_logger = logging.getLogger("calculator")

    # Safely close and remove all existing handlers associated with the root logger.
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Reset the configuration flag and re-run the configuration.
    _is_configured = False
    configure_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """
    Factory function to get a logger instance within the 'calculator' namespace.

    Args:
        name (str): The specific name for the child logger (e.g., 'repl', 'history').

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(f"calculator.{name}")
