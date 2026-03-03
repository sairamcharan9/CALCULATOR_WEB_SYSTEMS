"""
Input Validators Module (LBYL)
===============================

Provides Look-Before-You-Leap validation helpers that check user input
*before* attempting to create a calculation.  This contrasts with the
EAFP style used in the operations module.
"""

from decimal import Decimal, InvalidOperation

from app.operations import get_supported_operations


def validate_input_parts(parts: list[str], max_value: float = 1e10) -> str | None:
    """Validate that *parts* has the correct format for a calculation.

    Checks:
        1. Correct number of tokens for the given operation.
        2. The first token is a recognized operation name.
        3. Operands are within the allowed range.

    Args:
        parts: The tokenized user input.
        max_value: Maximum allowed numeric value for operands.

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

    if len(parts) != 3:
        return (
            "Error: Invalid format. Please use: <operation> <number1> <number2>\n"
            "Example: add 5 3\n"
            "Type 'help' for available commands."
        )

    # Range validation
    for i in [1, 2]:
        val = validate_numeric(parts[i])
        if val is None:
            return f"Error: '{parts[i]}' is not a valid number."
        if abs(val) > Decimal(str(max_value)):
            return f"Error: Operand '{parts[i]}' exceeds the maximum allowed value of {max_value}."

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
