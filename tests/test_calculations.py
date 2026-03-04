"""
Tests for the Calculation Module
=================================

Parameterized tests for ``Calculation`` and ``CalculationFactory``,
covering creation, string representations, and error paths.
"""

import pytest
from decimal import Decimal

from app import load_plugins
# Import the operation functions directly for testing Calculation results
from app.operations import add, subtract, multiply, divide, nth_power, nth_root, modulus, int_divide, percent, abs_diff 
from app.calculation import Calculation, CalculationFactory
from app.exceptions import DivisionByZeroError, InvalidOperationError

load_plugins()


# ===========================================================================
# Calculation class
# ===========================================================================


class TestCalculation:
    """Tests for the Calculation data model."""

    @pytest.mark.parametrize(
        "a, b, operation, op_name, expected",
        [
            (Decimal("5"), Decimal("3"), add, "add", Decimal("8.00")),
            (Decimal("10"), Decimal("4"), subtract, "subtract", Decimal("6.00")),
            (Decimal("6"), Decimal("7"), multiply, "multiply", Decimal("42.00")),
            (Decimal("20"), Decimal("4"), divide, "divide", Decimal("5.00")),
            (Decimal("2"), Decimal("8"), nth_power, "power", Decimal("256.00")),
            (Decimal("9"), Decimal("2"), nth_root, "root", Decimal("3.00")),
            (Decimal("10"), Decimal("3"), modulus, "modulus", Decimal("1.00")),
            (Decimal("10"), Decimal("3"), int_divide, "int_divide", Decimal("3.00")),
            (Decimal("5"), Decimal("100"), percent, "percent", Decimal("5.00")),
            (Decimal("5"), Decimal("10"), abs_diff, "abs_diff", Decimal("5.00")),
        ],
    )
    def test_calculation_result(
        self, a, b, operation, op_name, expected
    ) -> None:
        """Test that Calculation computes the correct result."""
        calc = Calculation(a, b, operation, op_name, precision=2)
        assert calc.result == expected
        assert calc.operand_a == a
        assert calc.operand_b == b
        assert calc.operation_name == op_name

    def test_repr(self) -> None:
        """Test __repr__ output."""
        calc = Calculation(Decimal("2"), Decimal("3"), add, "add")
        assert "Calculation" in repr(calc)
        assert "add" in repr(calc)
        assert "5.00" in repr(calc)

    @pytest.mark.parametrize(
        "a, b, operation, op_name, expected_substring",
        [
            (Decimal("5"), Decimal("3"), add, "add", "5 + 3 = 8.00"),
            (Decimal("10"), Decimal("3"), modulus, "modulus", "10 % 3 = 1.00"),
        ],
    )
    def test_str_formatting(
        self, a, b, operation, op_name, expected_substring
    ) -> None:
        """Test that __str__ uses the correct format and symbol."""
        result_str = str(Calculation(a, b, operation, op_name))
        assert expected_substring in result_str
        assert "=" in result_str

    def test_division_by_zero(self) -> None:
        """Creating a divide-by-zero Calculation raises DivisionByZeroError."""
        with pytest.raises(DivisionByZeroError):
            Calculation(Decimal("10"), Decimal("0"), divide, "divide")


# ===========================================================================
# CalculationFactory
# ===========================================================================


class TestCalculationFactory:
    """Tests for the CalculationFactory."""

    @pytest.mark.parametrize(
        "op_name, a, b, expected",
        [
            ("add", Decimal("2"), Decimal("3"), Decimal("5.00")),
            ("subtract", Decimal("10"), Decimal("3"), Decimal("7.00")),
            ("multiply", Decimal("4"), Decimal("5"), Decimal("20.00")),
            ("divide", Decimal("10"), Decimal("2"), Decimal("5.00")),
            ("power", Decimal("2"), Decimal("3"), Decimal("8.00")),
            ("root", Decimal("27"), Decimal("3"), Decimal("3.00")),
            ("modulus", Decimal("10"), Decimal("3"), Decimal("1.00")),
            ("int_divide", Decimal("10"), Decimal("3"), Decimal("3.00")),
            ("percent", Decimal("5"), Decimal("100"), Decimal("5.00")),
            ("abs_diff", Decimal("5"), Decimal("10"), Decimal("5.00")),
        ],
    )
    def test_create_valid(self, op_name, a, b, expected) -> None:
        """Factory creates correct Calculation instances."""
        calc = CalculationFactory.create(a, b, op_name, precision=2)
        assert calc.result == expected
        assert calc.operation_name == op_name

    def test_create_unknown_operation(self) -> None:
        """Unknown operation raises InvalidOperationError."""
        with pytest.raises(InvalidOperationError):
            CalculationFactory.create(Decimal("1"), Decimal("2"), "unknown")

    def test_create_non_arithmetic_command(self):
        """Trying to create a calculation with a non-arithmetic command raises an error."""
        # The 'greet' command exists but is not an arithmetic operation
        with pytest.raises(InvalidOperationError):
            CalculationFactory.create(Decimal("1"), Decimal("2"), "greet")

    def test_get_supported_operations(self) -> None:
        """Verify that all and only arithmetic operations are returned."""
        ops = CalculationFactory.get_supported_operations()
        expected_ops = {"add", "subtract", "multiply", "divide", "power", "root", "modulus", "int_divide", "percent", "abs_diff"}
        assert set(ops) == expected_ops
        
        # Check that a non-arithmetic command like 'greet' is not included
        assert "greet" not in ops
