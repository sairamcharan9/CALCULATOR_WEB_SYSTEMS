"""
Calculator Configuration Module (dotenv)
==========================================

Loads application settings from environment variables (with ``.env`` file
support via ``python-dotenv``).  Validates values and raises
``ConfigurationError`` for invalid settings.

Settings:
    - ``CALCULATOR_LOG_DIR``: Directory for log files (default ``logs``)
    - ``CALCULATOR_LOG_FILE``: Log file name (default ``calculator.log``)
    - ``CALCULATOR_HISTORY_DIR``: Directory for history files (default ``data``)
    - ``CALCULATOR_MAX_HISTORY_SIZE``: Maximum history entries (default ``1000``)
    - ``CALCULATOR_AUTO_SAVE``: ``true``/``false`` toggle (default ``true``)
    - ``CALCULATOR_PRECISION``: Decimal places for calculations (default ``2``)
    - ``CALCULATOR_MAX_INPUT_VALUE``: Maximum allowed input value (default ``1e10``)
    - ``CALCULATOR_DEFAULT_ENCODING``: Default encoding for file operations (default ``utf-8``)
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from app.exceptions import ConfigurationError


class CalculatorConfig:
    """Loads and validates calculator settings from the environment.

    Attributes:
        log_dir: Directory for log files.
        log_file: Log file name.
        history_dir: Directory for history files.
        history_file: History file name.
        max_history_size: Maximum number of history entries.
        auto_save: Whether to auto-save after each calculation.
        precision: Number of decimal places for calculations.
        max_input_value: Maximum allowed input value.
        default_encoding: Default encoding for file operations.
    """

    # Supported encodings for validation
    _VALID_ENCODINGS = ("utf-8", "utf-16", "utf-32", "ascii", "latin-1", "iso-8859-1")
    _MAX_PRECISION = 20

    def __init__(self, env_path: str | None = None) -> None:
        """Load and validate config from environment / ``.env`` file.

        Args:
            env_path: Optional explicit path to a ``.env`` file.

        Raises:
            ConfigurationError: If any setting is invalid.
        """
        load_dotenv(dotenv_path=env_path, override=True)

        self.log_dir: str = os.getenv("CALCULATOR_LOG_DIR", "logs")
        self.log_file: str = os.getenv("CALCULATOR_LOG_FILE", "calculator.log")
        self.history_dir: str = os.getenv("CALCULATOR_HISTORY_DIR", "data")
        self.history_file: str = os.getenv("CALCULATOR_HISTORY_FILE", "history.csv")
        self.max_history_size: int = self._parse_positive_int(
            os.getenv("CALCULATOR_MAX_HISTORY_SIZE", "1000"), "CALCULATOR_MAX_HISTORY_SIZE"
        )
        self.auto_save: bool = self._parse_bool(
            os.getenv("CALCULATOR_AUTO_SAVE", "true"), "CALCULATOR_AUTO_SAVE"
        )
        self.precision: int = self._parse_non_negative_int(
            os.getenv("CALCULATOR_PRECISION", "2"), "CALCULATOR_PRECISION"
        )
        self.max_input_value: float = self._parse_float(
            os.getenv("CALCULATOR_MAX_INPUT_VALUE", "1e10"), "CALCULATOR_MAX_INPUT_VALUE"
        )
        self.default_encoding: str = os.getenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")

        # Validate all settings on startup
        self.validate()

    def validate(self) -> None:
        """Validate all configuration settings.

        Raises:
            ConfigurationError: If any setting fails validation.
        """
        if not self.log_dir.strip():
            raise ConfigurationError("CALCULATOR_LOG_DIR must not be empty.")
        if not self.log_file.strip():
            raise ConfigurationError("CALCULATOR_LOG_FILE must not be empty.")
        if not self.history_dir.strip():
            raise ConfigurationError("CALCULATOR_HISTORY_DIR must not be empty.")
        if not self.history_file.strip():
            raise ConfigurationError("CALCULATOR_HISTORY_FILE must not be empty.")
        if self.precision > self._MAX_PRECISION:
            raise ConfigurationError(
                f"CALCULATOR_PRECISION must be <= {self._MAX_PRECISION}, got {self.precision}."
            )
        if self.max_input_value <= 0:
            raise ConfigurationError(
                f"CALCULATOR_MAX_INPUT_VALUE must be positive, got {self.max_input_value}."
            )
        if self.default_encoding.lower() not in self._VALID_ENCODINGS:
            raise ConfigurationError(
                f"CALCULATOR_DEFAULT_ENCODING '{self.default_encoding}' is not supported. "
                f"Use one of: {', '.join(self._VALID_ENCODINGS)}."
            )

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _parse_bool(value: str, name: str) -> bool:
        """Convert a string to a boolean.

        Raises:
            ConfigurationError: If the value is not ``true`` or ``false``.
        """
        lower = value.strip().lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
        raise ConfigurationError(
            f"Invalid boolean value for {name}: '{value}'. "
            "Use 'true' or 'false'."
        )

    @staticmethod
    def _parse_positive_int(value: str, name: str) -> int:
        """Convert a string to a positive integer.

        Raises:
            ConfigurationError: If the value is not a valid positive integer.
        """
        try:
            result = int(value)
        except ValueError:
            raise ConfigurationError(
                f"Invalid integer value for {name}: '{value}'."
            )
        if result <= 0:
            raise ConfigurationError(
                f"{name} must be a positive integer, got {result}."
            )
        return result

    @staticmethod
    def _parse_non_negative_int(value: str, name: str) -> int:
        """Convert a string to a non-negative integer.

        Raises:
            ConfigurationError: If the value is not a valid non-negative integer.
        """
        try:
            result = int(value)
        except ValueError:
            raise ConfigurationError(
                f"Invalid integer value for {name}: '{value}'."
            )
        if result < 0:
            raise ConfigurationError(
                f"{name} must be a non-negative integer, got {result}."
            )
        return result

    @staticmethod
    def _parse_float(value: str, name: str) -> float:
        """Convert a string to a float.

        Raises:
            ConfigurationError: If the value is not a valid float.
        """
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError(
                f"Invalid float value for {name}: '{value}'."
            )

    def __repr__(self) -> str:
        return (
            f"CalculatorConfig("
            f"log_dir='{self.log_dir}', "
            f"log_file='{self.log_file}', "
            f"history_dir='{self.history_dir}', "
            f"history_file='{self.history_file}', "
            f"max_history_size={self.max_history_size}, "
            f"auto_save={self.auto_save}, "
            f"precision={self.precision}, "
            f"max_input_value={self.max_input_value}, "
            f"default_encoding='{self.default_encoding}')"
        )
