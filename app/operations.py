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

from app.commands import command
from app.logger import get_logger
from app.exceptions import DivisionByZeroError, InvalidOperationError

# --- Arithmetic Functions (Strategies) ---
import math

@command("add", "Returns the sum of two Decimal numbers.", "add <n1> <n2>")
def add(a: Decimal, b: Decimal) -> Decimal:
    return a + b

@command("subtract", "Returns the difference between two Decimal numbers.", "subtract <n1> <n2>")
def subtract(a: Decimal, b: Decimal) -> Decimal:
    return a - b

@command("multiply", "Returns the product of two Decimal numbers.", "multiply <n1> <n2>")
def multiply(a: Decimal, b: Decimal) -> Decimal:
    return a * b

@command("divide", "Returns the quotient of two Decimal numbers.", "divide <n1> <n2>")
def divide(a: Decimal, b: Decimal) -> Decimal:
    """
    Returns `None` if the divisor is zero, and logs a warning.
    Otherwise, returns the quotient of two Decimal numbers.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot divide by zero.")
    try:
        return a / b
    except DecimalInvalidOperation as e:
        # Catch other potential decimal errors, e.g., invalid contexts
        raise InvalidOperationError(f"Invalid division operation: {e}")

@command("power", "Returns the base `a` raised to the power of `b`.", "power <base> <exp>")
def nth_power(a: Decimal, b: Decimal) -> Decimal:
    return a ** b

@command("root", "Calculates the `b`-th root of `a`.", "root <num> <n>")
def nth_root(a: Decimal, b: Decimal) -> Decimal:
    """
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("The root degree cannot be zero.")
    if a < 0 and b % 2 == 0:
        raise InvalidOperationError("Cannot calculate an even root of a negative number.")
    return a ** (Decimal(1) / b)

@command("modulus", "Returns the remainder of the division of `a` by `b`.", "modulus <n1> <n2>")
def modulus(a: Decimal, b: Decimal) -> Decimal:
    """
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform modulus operation with zero.")
    return a % b

@command("int_divide", "Returns the integer part of the quotient of `a` divided by `b`.", "int_divide <n1> <n2>")
def int_divide(a: Decimal, b: Decimal) -> Decimal:
    """
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform integer division by zero.")
    return a // b

@command("percent", "Calculates what percentage `a` is of `b`.", "percent <n1> <n2>")
def percent(a: Decimal, b: Decimal) -> Decimal:
    """
    Raises `DivisionByZeroError` if `b` is zero.
    """
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot calculate a percentage of zero.")
    return (a / b) * Decimal(100)

@command("abs_diff", "Returns the absolute difference between `a` and `b`.", "abs_diff <n1> <n2>")
def abs_diff(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b)
