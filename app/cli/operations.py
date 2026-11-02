"""
Arithmetic Operations (Strategy Pattern)
========================================

Implements the Strategy design pattern for handling arithmetic operations.
Each operation is a separate function registered with the @command decorator.
"""

from decimal import Decimal, InvalidOperation as DecimalInvalidOperation
import math

from app.cli.commands import command
from app.core.logger import get_logger
from app.core.exceptions import DivisionByZeroError, InvalidOperationError


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
    """Returns the quotient; raises DivisionByZeroError if b is zero."""
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot divide by zero.")
    try:
        return a / b
    except DecimalInvalidOperation as e:
        raise InvalidOperationError(f"Invalid division operation: {e}")


@command("power", "Returns the base `a` raised to the power of `b`.", "power <base> <exp>")
def nth_power(a: Decimal, b: Decimal) -> Decimal:
    return a ** b


@command("root", "Calculates the `b`-th root of `a`.", "root <num> <n>")
def nth_root(a: Decimal, b: Decimal) -> Decimal:
    if b == Decimal(0):
        raise DivisionByZeroError("The root degree cannot be zero.")
    if a < 0 and b % 2 == 0:
        raise InvalidOperationError("Cannot calculate an even root of a negative number.")
    return a ** (Decimal(1) / b)


@command("modulus", "Returns the remainder of the division of `a` by `b`.", "modulus <n1> <n2>")
def modulus(a: Decimal, b: Decimal) -> Decimal:
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform modulus operation with zero.")
    return a % b


@command("int_divide", "Returns the integer part of the quotient of `a` divided by `b`.", "int_divide <n1> <n2>")
def int_divide(a: Decimal, b: Decimal) -> Decimal:
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot perform integer division by zero.")
    return a // b


@command("percent", "Calculates what percentage `a` is of `b`.", "percent <n1> <n2>")
def percent(a: Decimal, b: Decimal) -> Decimal:
    if b == Decimal(0):
        raise DivisionByZeroError("Cannot calculate a percentage of zero.")
    return (a / b) * Decimal(100)


@command("abs_diff", "Returns the absolute difference between `a` and `b`.", "abs_diff <n1> <n2>")
def abs_diff(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b)


@command("sin", "Returns the sine of `a` in radians.", "sin <number>")
def sin(a: Decimal) -> Decimal:
    return Decimal(math.sin(a))


@command("cos", "Returns the cosine of `a` in radians.", "cos <number>")
def cos(a: Decimal) -> Decimal:
    return Decimal(math.cos(a))


@command("tan", "Returns the tangent of `a` in radians.", "tan <number>")
def tan(a: Decimal) -> Decimal:
    return Decimal(math.tan(a))


@command("log", "Returns the base-10 logarithm of `a`.", "log <number>")
def log(a: Decimal) -> Decimal:
    return Decimal(math.log10(a))


@command("ln", "Returns the natural logarithm of `a`.", "ln <number>")
def ln(a: Decimal) -> Decimal:
    return Decimal(math.log(a))


@command("distance", "Returns the Euclidean distance between two points (x1, y1) and (x2, y2).", "distance <x1> <y1> <x2> <y2>")
def distance(x1: Decimal, y1: Decimal, x2: Decimal, y2: Decimal) -> Decimal:
    """Returns the Euclidean distance between two points (x1, y1) and (x2, y2)."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2).sqrt()


@command("cube", "Returns the cube (x^3) of a Decimal number.", "cube <num>")
def cube(a: Decimal) -> Decimal:
    """Returns the cube (x^3) of a Decimal number."""
    return a ** 3
