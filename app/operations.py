"""
Operations Module (Strategy Pattern)
=====================================

Provides arithmetic operations as standalone functions and a registry
dictionary that maps operation names to their callables (Strategy Pattern).

Supported operations:
    add, subtract, multiply, divide, power, root, percentage, cube, cbrt

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


def percentage(a: Decimal, b: Decimal) -> Decimal:
    """Return *b* percent of *a*.

    Computes ``a * (b / 100)``.

    Examples:
        >>> percentage(Decimal('200'), Decimal('10'))
        Decimal('20')
    """
    return a * (b / Decimal("100"))


def sqrt(a: Decimal) -> Decimal:
    """Return the square root of *a*.

    Raises:
        InvalidOperationError: If *a* is negative.

    Examples:
        >>> sqrt(Decimal('9'))
        Decimal('3')
    """
    if a < 0:
        raise InvalidOperationError("Square root of a negative number is not allowed.")
    return a.sqrt()


def cube(a: Decimal) -> Decimal:
    """Return the cube of *a*.

    Examples:
        >>> cube(Decimal('3'))
        Decimal('27')
    """
    return a ** 3


def cbrt(a: Decimal) -> Decimal:
    """Return the cube root of *a*.

    Uses ``a ** (1 / 3)``.

    Examples:
        >>> cbrt(Decimal('27'))
        Decimal('3')
    """
    if a < 0:
        # For Decimal, negative ** (1/3) might be tricky,
        # but we can do -(abs(a) ** (1/3))
        return -(abs(a) ** (Decimal("1") / Decimal("3")))
    return a ** (Decimal("1") / Decimal("3"))


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------


OPERATIONS: dict[str, callable] = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "power": nth_power,  # Alias
    "root": nth_root,    # Alias
    "nth_power": nth_power,
    "nth_root": nth_root,
    "percentage": percentage,
    "sqrt": sqrt,
    "cube": cube,
    "cbrt": cbrt,
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
