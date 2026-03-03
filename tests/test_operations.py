"""
Tests for the Operations Module
================================

Parameterized tests covering all six arithmetic operations:
add, subtract, multiply, divide, power, root, percentage, cube, cbrt — including edge cases
(zero, negative numbers, decimals, large numbers, division by zero,
root by zero).

Also tests the strategy registry helpers ``get_operation`` and
``get_supported_operations``.
"""

import pytest
from decimal import Decimal

from app.exceptions import DivisionByZeroError, InvalidOperationError
from app.operations import (
    add,
    subtract,
    multiply,
    divide,
    nth_power,
    nth_root,
    percentage,
    sqrt,
    cube,
    cbrt,
    get_operation,
    get_supported_operations,
    OPERATIONS,
)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("2"), Decimal("3"), Decimal("5")),
        (Decimal("0"), Decimal("0"), Decimal("0")),
        (Decimal("-1"), Decimal("1"), Decimal("0")),
        (Decimal("-5"), Decimal("-3"), Decimal("-8")),
        (Decimal("1.5"), Decimal("2.5"), Decimal("4.0")),
        (Decimal("999999999"), Decimal("1"), Decimal("1000000000")),
        (Decimal("0.1"), Decimal("0.2"), Decimal("0.3")),
    ],
    ids=[
        "pos+pos",
        "zero+zero",
        "neg+pos",
        "neg+neg",
        "dec+dec",
        "large_boundary",
        "small_dec",
    ],
)
def test_add(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test addition with various inputs."""
    assert add(a, b) == expected


# ---------------------------------------------------------------------------
# subtract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("5"), Decimal("3"), Decimal("2")),
        (Decimal("0"), Decimal("0"), Decimal("0")),
        (Decimal("-1"), Decimal("-1"), Decimal("0")),
        (Decimal("3"), Decimal("5"), Decimal("-2")),
        (Decimal("10.5"), Decimal("0.5"), Decimal("10.0")),
    ],
    ids=["pos-pos", "zero-zero", "neg-neg", "result_neg", "dec_sub"],
)
def test_subtract(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test subtraction with various inputs."""
    assert subtract(a, b) == expected


# ---------------------------------------------------------------------------
# multiply
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("4"), Decimal("3"), Decimal("12")),
        (Decimal("0"), Decimal("100"), Decimal("0")),
        (Decimal("-2"), Decimal("3"), Decimal("-6")),
        (Decimal("-3"), Decimal("-4"), Decimal("12")),
        (Decimal("1.5"), Decimal("2"), Decimal("3.0")),
    ],
    ids=["pos*pos", "zero_factor", "neg*pos", "neg*neg", "dec*int"],
)
def test_multiply(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test multiplication with various inputs."""
    assert multiply(a, b) == expected


# ---------------------------------------------------------------------------
# divide
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("10"), Decimal("2"), Decimal("5")),
        (Decimal("7"), Decimal("2"), Decimal("3.5")),
        (Decimal("0"), Decimal("5"), Decimal("0")),
        (Decimal("-10"), Decimal("2"), Decimal("-5")),
        (Decimal("-10"), Decimal("-2"), Decimal("5")),
    ],
    ids=["even", "decimal_result", "zero_dividend", "neg_dividend", "both_neg"],
)
def test_divide(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test division with various inputs."""
    assert divide(a, b) == expected


def test_divide_by_zero() -> None:
    """Test that dividing by zero raises DivisionByZeroError."""
    with pytest.raises(DivisionByZeroError):
        divide(Decimal("10"), Decimal("0"))


# ---------------------------------------------------------------------------
# nth_power
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("2"), Decimal("8"), Decimal("256")),
        (Decimal("5"), Decimal("0"), Decimal("1")),
        (Decimal("10"), Decimal("1"), Decimal("10")),
        (Decimal("3"), Decimal("3"), Decimal("27")),
    ],
    ids=["2^8", "n^0", "n^1", "3^3"],
)
def test_nth_power(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test power with various inputs."""
    assert nth_power(a, b) == expected


# ---------------------------------------------------------------------------
# nth_root
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("9"), Decimal("2"), Decimal("3")),
        (Decimal("27"), Decimal("3"), Decimal("3")),
        (Decimal("1"), Decimal("5"), Decimal("1")),
    ],
    ids=["sqrt_9", "cbrt_27", "root_1"],
)
def test_nth_root(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test root with various inputs."""
    assert nth_root(a, b) == expected


def test_root_by_zero() -> None:
    """Test that root with degree zero raises DivisionByZeroError."""
    with pytest.raises(DivisionByZeroError):
        nth_root(Decimal("9"), Decimal("0"))


# ---------------------------------------------------------------------------
# percentage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("100"), Decimal("10"), Decimal("10")),
        (Decimal("200"), Decimal("25"), Decimal("50")),
        (Decimal("50"), Decimal("50"), Decimal("25")),
        (Decimal("1000"), Decimal("0"), Decimal("0")),
        (Decimal("100"), Decimal("100"), Decimal("100")),
        (Decimal("100"), Decimal("150"), Decimal("150")),
        (Decimal("0"), Decimal("10"), Decimal("0")),
        (Decimal("100"), Decimal("0.5"), Decimal("0.5")),  # 0.5% of 100
        (Decimal("200"), Decimal("-10"), Decimal("-20")), # -10% of 200
    ],
    ids=[
        "10%_of_100",
        "25%_of_200",
        "50%_of_50",
        "0%_of_1000",
        "100%_of_100",
        "150%_of_100",
        "10%_of_0",
        "0.5%_of_100",
        "-10%_of_200",
    ],
)
def test_percentage(a: Decimal, b: Decimal, expected: Decimal) -> None:
    """Test percentage calculation with various inputs."""
    assert percentage(a, b) == expected


# ---------------------------------------------------------------------------
# sqrt
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, expected",
    [
        (Decimal("9"), Decimal("3")),
        (Decimal("0"), Decimal("0")),
        (Decimal("1"), Decimal("1")),
        (Decimal("4"), Decimal("2")),
        (Decimal("0.25"), Decimal("0.5")),
    ],
    ids=["sqrt_9", "sqrt_0", "sqrt_1", "sqrt_4", "sqrt_0.25"],
)
def test_sqrt(a: Decimal, expected: Decimal) -> None:
    """Test sqrt with various inputs."""
    assert sqrt(a) == expected


def test_sqrt_negative() -> None:
    """Test that sqrt of a negative number raises InvalidOperationError."""
    with pytest.raises(InvalidOperationError):
        sqrt(Decimal("-9"))


# ---------------------------------------------------------------------------
# cube
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, expected",
    [
        (Decimal("3"), Decimal("27")),
        (Decimal("0"), Decimal("0")),
        (Decimal("-2"), Decimal("-8")),
        (Decimal("1.5"), Decimal("3.375")),
    ],
    ids=["cube_3", "cube_0", "cube_neg", "cube_decimal"],
)
def test_cube(a: Decimal, expected: Decimal) -> None:
    """Test cube with various inputs."""
    assert cube(a) == expected


# ---------------------------------------------------------------------------
# cbrt
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, expected",
    [
        (Decimal("27"), Decimal("3")),
        (Decimal("0"), Decimal("0")),
        (Decimal("-8"), Decimal("-2")),
        (Decimal("1"), Decimal("1")),
    ],
    ids=["cbrt_27", "cbrt_0", "cbrt_neg", "cbrt_1"],
)
def test_cbrt(a: Decimal, expected: Decimal) -> None:
    """Test cbrt with various inputs."""
    # Decimal root might have precision issues, let's check with some tolerance if needed
    # but for these integers it should be exact if implemented correctly
    assert cbrt(a) == expected


# ---------------------------------------------------------------------------
# Strategy registry helpers
# ---------------------------------------------------------------------------


class TestStrategyRegistry:
    """Tests for the operation lookup and listing helpers."""

    @pytest.mark.parametrize(
        "name",
        ["add", "subtract", "multiply", "divide", "power", "root", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"],
        ids=["add", "subtract", "multiply", "divide", "power", "root", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"],
    )
    def test_get_operation_valid(self, name: str) -> None:
        """Known names return a callable."""
        func = get_operation(name)
        assert callable(func)

    def test_get_operation_invalid(self) -> None:
        """Unknown names raise InvalidOperationError."""
        with pytest.raises(InvalidOperationError, match="Unknown operation"):
            get_operation("modulo")

    def test_get_supported_operations(self) -> None:
        """All operations are returned."""
        ops = get_supported_operations()
        expected_ops = {"add", "subtract", "multiply", "divide", "power", "root", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"}
        assert set(ops) == expected_ops

    def test_operations_dict(self) -> None:
        """OPERATIONS dict contains all expected keys."""
        assert len(OPERATIONS) == 12
