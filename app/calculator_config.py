"""
Calculator Configuration Management
=================================

This module handles the loading and validation of the application's configuration
settings from environment variables. It uses the `python-dotenv` library to
support loading settings from a `.env` file, which is useful for development.

The `CalculatorConfig` class is responsible for parsing these settings,
providing default values, and performing validation to ensure that the
application runs with a valid configuration. If any setting is invalid,
it raises a `ConfigurationError`.

Key managed settings include paths for logging and history, history size limits,
auto-save behavior, calculation precision, and input value constraints.
"""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv

from app.exceptions import ConfigurationError


class CalculatorConfig:
    """
    Loads, validates, and provides access to calculator settings from the environment.

    This class reads configuration variables from the environment, provides sensible
    defaults, and validates them to ensure the application starts in a consistent
    and error-free state.

    Attributes:
        log_dir (str): Directory for log files.
        log_file (str): Name of the log file.
        history_dir (str): Directory for storing history files.
        history_file (str): Name of the history CSV file.
        max_history_size (int): Maximum number of entries to keep in the history.
        auto_save (bool): If True, automatically saves history after each operation.
        precision (int): The number of decimal places for calculation results.
        max_input_value (float): The maximum numerical value allowed for inputs.
        default_encoding (str): The default file encoding (e.g., 'utf-8').
    """

    # A tuple of supported file encodings for validation purposes.
    _VALID_ENCODINGS: Final[tuple[str, ...]] = (
        "utf-8", "utf-16", "utf-32", "ascii", "latin-1", "iso-8859-1"
    )
    # The maximum allowed precision for calculations to prevent performance issues.
    _MAX_PRECISION: Final[int] = 20

    def __init__(self, env_path: str | None = None) -> None:
        """
        Loads and validates configuration from environment variables or a `.env` file.

        Args:
            env_path (str | None): An optional, explicit path to a `.env` file.

        Raises:
            ConfigurationError: If any environment variable has an invalid value.
        """
        # Load environment variables from a .env file if present, overriding existing ones.
        load_dotenv(dotenv_path=env_path, override=True)

        # Load general settings with default values if not provided.
        self.log_dir: str = os.getenv("CALCULATOR_LOG_DIR", "logs")
        self.log_file: str = os.getenv("CALCULATOR_LOG_FILE", "calculator.log")
        self.history_dir: str = os.getenv("CALCULATOR_HISTORY_DIR", "data")
        self.history_file: str = os.getenv("CALCULATOR_HISTORY_FILE", "history.csv")

        # Parse and validate settings that require specific data types or constraints.
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

        # After loading all values, run a comprehensive validation.
        self.validate()

    def validate(self) -> None:
        """
        Performs validation checks on the loaded configuration settings.

        Raises:
            ConfigurationError: If a configuration value is invalid.
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
                f"Unsupported encoding: '{self.default_encoding}'. Must be one of: "
                f"{', '.join(self._VALID_ENCODINGS)}."
            )

    @staticmethod
    def _parse_bool(value: str, name: str) -> bool:
        """
        Parses a string value to a boolean. Accepts 'true', '1', 'yes' or 'false', '0', 'no'.

        Args:
            value (str): The string to parse.
            name (str): The name of the environment variable for informative error messages.

        Returns:
            bool: The parsed boolean value.

        Raises:
            ConfigurationError: If the value is not a recognized boolean representation.
        """
        normalized_value = value.strip().lower()
        if normalized_value in ("true", "1", "yes"):
            return True
        if normalized_value in ("false", "0", "no"):
            return False
        raise ConfigurationError(f"Invalid boolean value for {name}: '{value}'. Use 'true' or 'false'.")

    @staticmethod
    def _parse_positive_int(value: str, name: str) -> int:
        """
        Parses a string to a positive integer (must be greater than 0).

        Args:
            value (str): The string to parse.
            name (str): The name of the environment variable for error messages.

        Returns:
            int: The parsed positive integer.

        Raises:
            ConfigurationError: If the value is not a valid integer or is not positive.
        """
        try:
            num = int(value)
            if num <= 0:
                raise ConfigurationError(f"{name} must be a positive integer, got {num}.")
            return num
        except ValueError:
            raise ConfigurationError(f"Invalid integer value for {name}: '{value}'.")

    @staticmethod
    def _parse_non_negative_int(value: str, name: str) -> int:
        """
        Parses a string to a non-negative integer (must be 0 or greater).

        Args:
            value (str): The string to parse.
            name (str): The name of the environment variable for error messages.

        Returns:
            int: The parsed non-negative integer.

        Raises:
            ConfigurationError: If the value is not a valid integer or is negative.
        """
        try:
            num = int(value)
            if num < 0:
                raise ConfigurationError(f"{name} must be a non-negative integer, got {num}.")
            return num
        except ValueError:
            raise ConfigurationError(f"Invalid integer value for {name}: '{value}'.")

    @staticmethod
    def _parse_float(value: str, name: str) -> float:
        """
        Parses a string to a float.

        Args:
            value (str): The string to parse.
            name (str): The name of the environment variable for error messages.

        Returns:
            float: The parsed float value.

        Raises:
            ConfigurationError: If the value cannot be converted to a float.
        """
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError(f"Invalid float value for {name}: '{value}'.")

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the configuration object.
        """
        return (
            "CalculatorConfig("
            f"log_dir='{self.log_dir}', "
            f"log_file='{self.log_file}', "
            f"history_dir='{self.history_dir}', "
            f"history_file='{self.history_file}', "
            f"max_history_size={self.max_history_size}, "
            f"auto_save={self.auto_save}, "
            f"precision={self.precision}, "
            f"max_input_value={self.max_input_value}, "
            f"default_encoding='{self.default_encoding}'"
            ")"
        )
