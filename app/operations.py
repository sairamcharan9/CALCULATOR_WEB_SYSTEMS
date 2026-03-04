"""
Arithmetic Operations (Strategy Pattern)
========================================

This module implements the Strategy design pattern for handling arithmetic
operations. Each operation is a separate function (a "strategy") that takes
two `Decimal` numbers and returns a `Decimal` result.

A central dictionary, `OPERATIONS`, acts as a registry that maps operation
names (like "add", "subtract") to their corresponding functions. This allows
for easy extension—adding a new operation only requires defining a new function
and adding it to the `OPERATIONS` dictionary.

Error handling follows an "Easier to Ask for Forgiveness than Permission"
(EAFP) approach. For example, the `divide` function does not
check for a zero divisor beforehand; instead, it relies on the caller to
handle the `ZeroDivisionError` that `Decimal` would raise.
"""

from decimal import Decimal, InvalidOperation as DecimalInvalidOperation
from app.exceptions import DivisionByZeroError, InvalidOperationError

# --- Arithmetic Functions (Strategies) ---

def add(a: Decimal, b: Decimal) -> Decimal:
    """Returns the sum of two Decimal numbers."""
    return a + b

def subtract(a: Decimal, b: Decimal) -> Decimal:
    """Returns the difference between two Decimal numbers."""
    return a - b

def multiply(a: Decimal, b: Decimal) -> Decimal:
    """Returns the product of two Decimal numbers."""
    return a * b

def divide(a: Decimal, b: Decimal) -> Decimal:
    """
    Returns the quotient of two Decimal numbers.
    Raises `DivisionByZeroError` if the divisor is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot divide by zero.")
    try:
        return a / b
    except DecimalInvalidOperation as e:
        # Catch other potential decimal errors, e.g., invalid contexts
        raise InvalidOperationError(f"Invalid division operation: {e}")

def nth_power(a: Decimal, b: Decimal) -> Decimal:
    """Returns the base `a` raised to the power of `b`."""
    return a ** b

def nth_root(a: Decimal, b: Decimal) -> Decimal:
    """
    Calculates the `b`-th root of `a`.
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("The root degree cannot be zero.")
    if a < 0 and b % 2 == 0:
        raise InvalidOperationError("Cannot calculate an even root of a negative number.")
    return a ** (Decimal(1) / b)

def modulus(a: Decimal, b: Decimal) -> Decimal:
    """
    Returns the remainder of the division of `a` by `b`.
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform modulus operation with zero.")
    return a % b

def int_divide(a: Decimal, b: Decimal) -> Decimal:
    """
    Returns the integer part of the quotient of `a` divided by `b`.
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform integer division by zero.")
    return a // b

def percent(a: Decimal, b: Decimal) -> Decimal:
    """
    Calculates what percentage `a` is of `b`.
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot calculate a percentage of zero.")
    return (a / b) * Decimal(100)

def abs_diff(a: Decimal, b: Decimal) -> Decimal:
    """Returns the absolute difference between `a` and `b`."""
    return abs(a - b)

# --- Strategy Registry and Dispatchers ---

# The OPERATIONS dictionary acts as a registry for all arithmetic functions (strategies).
# This is the core of the Strategy pattern, allowing for dynamic dispatch of operations.
OPERATIONS: dict[str, callable] = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "power": nth_power,
    "root": nth_root,
    "modulus": modulus,
    "int_divide": int_divide,
    "percent": percent,
    "abs_diff": abs_diff,
}

def get_operation(operation_name: str) -> callable:
    """
    Retrieves an arithmetic function from the `OPERATIONS` registry.

    Args:
        operation_name (str): The name of the operation to retrieve.

    Returns:
        callable: The function corresponding to the operation name.

    Raises:
        InvalidOperationError: If the `operation_name` is not found in the registry.
    """
    operation_func = OPERATIONS.get(operation_name)
    if not operation_func:
        raise InvalidOperationError(
            f"Unknown operation: '{operation_name}'. Supported operations are: "
            f"{', '.join(get_supported_operations())}"
        )
    return operation_func

def get_supported_operations() -> list[str]:
    """Returns a sorted list of the names of all supported operations."""
    return sorted(OPERATIONS.keys())
