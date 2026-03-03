"""
Input Validators Module (LBYL)
===============================

Provides Look-Before-You-Leap validation helpers that check user input
*before* attempting to create a calculation.  This contrasts with the
EAFP style used in the operations module.
"""

from decimal import Decimal, InvalidOperation

from app.operations import get_supported_operations


def validate_input_parts(parts: list[str]) -> str | None:
    """Validate that *parts* has the correct format for a calculation.

    Checks:
        1. Correct number of tokens for the given operation.
        2. The first token is a recognized operation name.

    Args:
        parts: The tokenized user input.

    Returns:
        An error message string if invalid, or ``None`` if valid.
    """
    if not parts:
        return (
            "Error: Invalid format. Please enter a command.\n"
            "Type 'help' for available commands."
        )

    operation = parts[0]
    valid_operations = get_supported_operations()

    if operation not in valid_operations:
        return (
            f"Error: Unknown operation '{operation}'.\n"
            f"Available operations: {', '.join(valid_operations)}\n"
            "Type 'help' for more information."
        )

    # Operations requiring one operand
    if operation in ("sqrt", "cube", "cbrt"):
        if len(parts) != 2:
            return (
                f"Error: Invalid format for '{operation}'. Please use: {operation} <number>\n"
                f"Example: {operation} 9"
            )
    # Operations requiring two operands
    else:
        if len(parts) != 3:
            return (
                "Error: Invalid format. Please use: <operation> <number1> <number2>\n"
                "Example: add 5 3\n"
                "Type 'help' for available commands."
            )

    return None


def validate_numeric(value: str) -> Decimal | None:
    """Try to convert *value* to a ``Decimal`` (LBYL-style).

    Args:
        value: A string that may represent a number.

    Returns:
        A ``Decimal`` if the conversion succeeds, or ``None`` on failure.
    """
    try:
        return Decimal(value)
    except InvalidOperation:
        return None
