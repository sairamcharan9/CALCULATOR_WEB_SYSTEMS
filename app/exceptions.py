"""
Exceptions Module
=================

Custom exception hierarchy for the calculator application.

- CalculationError: base exception for all calculator-related errors.
- InvalidOperationError: raised when an unknown operation name is used.
- InvalidInputError: raised for malformed input or non-numeric values.
- DivisionByZeroError: wraps Python's built-in ZeroDivisionError.
- ConfigurationError: raised for invalid or missing configuration.
- OperationError: raised for errors during operation execution.
- ValidationError: raised for input validation errors.
"""


class CalculationError(Exception):
    """Base exception for calculator errors."""


class InvalidOperationError(CalculationError):
    """Raised when an unknown operation name is requested."""


class InvalidInputError(CalculationError):
    """Raised when user input is malformed or contains non-numeric values."""


class DivisionByZeroError(CalculationError):
    """Raised when a division by zero is attempted."""


class ConfigurationError(CalculationError):
    """Raised when application configuration is invalid or missing."""


class OperationError(CalculationError):
    """Raised when an error occurs during an arithmetic operation."""


class ValidationError(CalculationError):
    """Raised when input fails validation checks."""
