"""
Custom Application Exceptions
=============================

This module defines a custom exception hierarchy for the calculator application
to provide more specific and meaningful error handling than using generic
built-in exceptions.

All custom exceptions inherit from a common base class, `CalculationError`,
allowing for centralized error catching.
"""


class CalculationError(Exception):
    """Base exception for all errors raised by the calculator application."""


class InvalidOperationError(CalculationError):
    """
    Raised when the user requests an operation that is not supported or does not exist.
    
    Example:
        - User inputs: `log 10 2`
    """


class InvalidInputError(CalculationError):
    """
    Raised when the user input is malformed, such as providing non-numeric operands.
    
    Example:
        - User inputs: `add ten five`
    """


class DivisionByZeroError(CalculationError):
    """
    Raised specifically when a division or root operation involves zero in a prohibited way.
    
    This exception wraps Python's built-in `ZeroDivisionError` to fit into the
    application's custom exception hierarchy.
    """


class ConfigurationError(CalculationError):
    """
    Raised when there is an issue with the application's configuration,
    such as an invalid value in the `.env` file or a missing required setting.
    """


class OperationError(CalculationError):
    """Raised for general errors that occur during the execution of an arithmetic operation."""


class ValidationError(CalculationError):
    """Raised when user input fails validation checks, such as providing too few arguments."""
