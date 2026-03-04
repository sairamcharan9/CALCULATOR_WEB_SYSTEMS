"""
Input Validation (Look Before You Leap)
=======================================

This module provides functions for validating user input before any calculations
are attempted. This approach is known as "Look Before You Leap" (LBYL), where
the code explicitly checks for pre-conditions (like correct format and valid
numbers) before proceeding.

This contrasts with an "Easier to Ask for Forgiveness than Permission" (EAFP)
approach, where one might try the calculation directly and catch any resulting
exceptions. Using LBYL here helps provide clearer, more specific error messages
to the user.
"""

from decimal import Decimal, InvalidOperation
from app.calculation import CalculationFactory


def validate_input_parts(parts: list[str], max_value: float = 1e10) -> str | None:
    """
    Validates that the tokenized user input is in the correct format for a calculation.

    Checks:
        1. The number of parts is correct (e.g., operation, operand, operand).
        2. The operation is one of the supported operations.
        3. The operands are valid numbers and within the configured `max_value` range.

    Args:
        parts (list[str]): The user's input, split into a list of strings.
        max_value (float): The maximum absolute value allowed for the operands.

    Returns:
        str | None: An error message string if validation fails, or `None` if it succeeds.
    """
    if not parts:
        return "Error: No input provided. Please enter a command."

    operation = parts[0]
    valid_operations = CalculationFactory.get_supported_operations()

    # Check if the operation is supported.
    if operation not in valid_operations:
        return (
            f"Error: Unknown operation '{operation}'.\n"
            f"Available operations: {', '.join(valid_operations)}\n"
            "Type 'help' for more information."
        )

    # Check for the correct number of arguments.
    if len(parts) != 3:
        return (
            "Error: Invalid format. Please use: <operation> <number1> <number2>\n"
            "Example: add 5 3\n"
            "Type 'help' for available commands."
        )

    # Validate that the operands are numeric and within the allowed range.
    for i in [1, 2]:
        operand_str = parts[i]
        numeric_value = validate_numeric(operand_str)

        if numeric_value is None:
            return f"Error: '{parts[i]}' is not a valid number."
        
        if abs(numeric_value) > Decimal(str(max_value)):
            return f"Error: Operand '{parts[i]}' exceeds the maximum allowed value of {max_value}."

    return None  # Return None to indicate successful validation.


def validate_numeric(value: str) -> Decimal | None:
    """
    Checks if a string can be converted to a `Decimal`.

    Args:
        value (str): The string to validate.

    Returns:
        A ``Decimal`` if the conversion succeeds, or ``None`` on failure.
    """
    try:
        return Decimal(value)
    except InvalidOperation:
        return None
