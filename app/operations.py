"""
Operations Module (Strategy Pattern)
=====================================

Provides arithmetic operations as standalone functions and a registry
dictionary that maps operation names to their callables (Strategy Pattern).

Supported operations:
    add, subtract, multiply, divide, power, root, modulus, int_divide,
    percent, abs_diff

The ``get_operation`` helper retrieves a callable by name.

Error handling follows EAFP — for example, ``divide`` does not pre-check
for a zero divisor; callers handle the ``ZeroDivisionError``.
"""

from decimal import Decimal

from app.exceptions import DivisionByZeroError, InvalidOperationError


# ---------------------------------------------------------------------------
# Arithmetic functions
# ---------------------------------------------------------------------------


def add(a: Decimal, b: Decimal) -> Decimal:
    """Return the sum of *a* and *b*.

    Examples:
        >>> add(Decimal('2'), Decimal('3'))
        Decimal('5')
    """
    return a + b


def subtract(a: Decimal, b: Decimal) -> Decimal:
    """Return the difference *a* − *b*.

    Examples:
        >>> subtract(Decimal('5'), Decimal('3'))
        Decimal('2')
    """
    return a - b


def multiply(a: Decimal, b: Decimal) -> Decimal:
    """Return the product *a* × *b*.

    Examples:
        >>> multiply(Decimal('4'), Decimal('3'))
        Decimal('12')
    """
    return a * b


def divide(a: Decimal, b: Decimal) -> Decimal:
    """Return the quotient *a* ÷ *b*.

    Uses EAFP: does **not** pre-check for a zero divisor.

    Raises:
        DivisionByZeroError: If *b* is zero.

    Examples:
        >>> divide(Decimal('10'), Decimal('2'))
        Decimal('5')
    """
    try:
        return a / b
    except Exception:
        raise DivisionByZeroError("Division by zero is not allowed.")


def nth_power(a: Decimal, b: Decimal) -> Decimal:
    """Return *a* raised to the power *b*.

    Examples:
        >>> nth_power(Decimal('2'), Decimal('8'))
        Decimal('256')
    """
    return a ** b


def nth_root(a: Decimal, b: Decimal) -> Decimal:
    """Return the *b*-th root of *a*.

    Computes ``a ** (1 / b)``.

    Raises:
        DivisionByZeroError: If `b` is zero.

    Examples:
        >>> nth_root(Decimal('9'), Decimal('2'))
        Decimal('3')
    """
    if b == 0:
        raise DivisionByZeroError("Root degree cannot be zero.")
    return a ** (Decimal("1") / b)


def modulus(a: Decimal, b: Decimal) -> Decimal:
    """Return the remainder of *a* / *b*.

    Raises:
        DivisionByZeroError: If *b* is zero.
    """
    if b == 0:
        raise DivisionByZeroError("Modulus by zero is not allowed.")
    return a % b


def int_divide(a: Decimal, b: Decimal) -> Decimal:
    """Return the integer quotient of *a* / *b*.

    Raises:
        DivisionByZeroError: If *b* is zero.
    """
    if b == 0:
        raise DivisionByZeroError("Integer division by zero is not allowed.")
    return a // b


def percent(a: Decimal, b: Decimal) -> Decimal:
    """Return the percentage of *a* with respect to *b*.

    Computes ``(a / b) * 100``.

    Raises:
        DivisionByZeroError: If *b* is zero.
    """
    if b == 0:
        raise DivisionByZeroError("Percentage calculation with respect to zero is not allowed.")
    return (a / b) * Decimal("100")


def abs_diff(a: Decimal, b: Decimal) -> Decimal:
    """Return the absolute difference between *a* and *b*."""
    return abs(a - b)


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------


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


def get_operation(name: str) -> callable:
    """Look up an operation callable by *name*.

    Args:
        name: The operation name (case-sensitive, lower-case expected).

    Returns:
        The corresponding arithmetic function.

    Raises:
        InvalidOperationError: If *name* is not in the registry.
    """
    operation = OPERATIONS.get(name)
    if operation is None:
        supported = ", ".join(OPERATIONS.keys())
        raise InvalidOperationError(
            f"Unknown operation '{name}'. Supported: {supported}"
        )
    return operation


def get_supported_operations() -> list[str]:
    """Return a sorted list of supported operation names."""
    return list(OPERATIONS.keys())
