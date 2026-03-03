"""
Tests for the Calculation Module
=================================

Parameterized tests for ``Calculation`` and ``CalculationFactory``,
covering creation, string representations, and error paths.
"""

import pytest
from decimal import Decimal

from app.operations import add, subtract, multiply, divide, nth_power, nth_root, percentage, sqrt, cube, cbrt
from app.calculation import Calculation, CalculationFactory
from app.exceptions import DivisionByZeroError, InvalidOperationError


# ===========================================================================
# Calculation class
# ===========================================================================


class TestCalculation:
    """Tests for the Calculation data model."""

    @pytest.mark.parametrize(
        "a, b, operation, op_name, expected",
        [
            (Decimal("5"), Decimal("3"), add, "add", Decimal("8")),
            (Decimal("10"), Decimal("4"), subtract, "subtract", Decimal("6")),
            (Decimal("6"), Decimal("7"), multiply, "multiply", Decimal("42")),
            (Decimal("20"), Decimal("4"), divide, "divide", Decimal("5")),
            (Decimal("2"), Decimal("8"), nth_power, "nth_power", Decimal("256")),
            (Decimal("9"), Decimal("2"), nth_root, "nth_root", Decimal("3")),
            (Decimal("100"), Decimal("10"), percentage, "percentage", Decimal("10")),
            (Decimal("9"), None, sqrt, "sqrt", Decimal("3")),
            (Decimal("3"), None, cube, "cube", Decimal("27")),
            (Decimal("27"), None, cbrt, "cbrt", Decimal("3")),
        ],
        ids=["add", "subtract", "multiply", "divide", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"],
    )
    def test_calculation_result(
        self, a, b, operation, op_name, expected
    ) -> None:
        """Test that Calculation computes the correct result."""
        calc = Calculation(a, b, operation, op_name)
        assert calc.result == expected
        assert calc.operand_a == a
        assert calc.operand_b == b
        assert calc.operation_name == op_name

    def test_repr(self) -> None:
        """Test __repr__ output."""
        calc = Calculation(Decimal("2"), Decimal("3"), add, "add")
        assert "Calculation" in repr(calc)
        assert "add" in repr(calc)
        assert "5" in repr(calc)
        
        calc_single = Calculation(Decimal("9"), None, sqrt, "sqrt")
        assert "Calculation(9, sqrt) = 3" in repr(calc_single)

    @pytest.mark.parametrize(
        "a, b, operation, op_name, expected_substring",
        [
            (Decimal("5"), Decimal("3"), add, "add", "5 + 3 = 8"),
            (Decimal("9"), None, sqrt, "sqrt", "√(9) = 3"),
            (Decimal("3"), None, cube, "cube", "3^3 = 27"),
            (Decimal("27"), None, cbrt, "cbrt", "³√(27) = 3"),
        ],
        ids=["add_sym", "sqrt_sym", "cube_sym", "cbrt_sym"],
    )
    def test_str_formatting(
        self, a, b, operation, op_name, expected_substring
    ) -> None:
        """Test that __str__ uses the correct format and symbol."""
        result_str = str(Calculation(a, b, operation, op_name))
        assert expected_substring in result_str
        assert "=" in result_str

    def test_str_unknown_operation(self) -> None:
        """Test __str__ falls back to operation_name when no symbol mapped."""
        calc = Calculation(Decimal("2"), Decimal("3"), add, "custom_op")
        assert "custom_op" in str(calc)

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
            ("add", Decimal("2"), Decimal("3"), Decimal("5")),
            ("subtract", Decimal("10"), Decimal("3"), Decimal("7")),
            ("multiply", Decimal("4"), Decimal("5"), Decimal("20")),
            ("divide", Decimal("10"), Decimal("2"), Decimal("5")),
            ("power", Decimal("2"), Decimal("3"), Decimal("8")),
            ("root", Decimal("27"), Decimal("3"), Decimal("3")),
            ("nth_power", Decimal("2"), Decimal("3"), Decimal("8")),
            ("nth_root", Decimal("27"), Decimal("3"), Decimal("3")),
            ("percentage", Decimal("100"), Decimal("10"), Decimal("10")),
            ("sqrt", Decimal("9"), None, Decimal("3")),
            ("cube", Decimal("3"), None, Decimal("27")),
            ("cbrt", Decimal("27"), None, Decimal("3")),
        ],
        ids=["add", "subtract", "multiply", "divide", "power_alias", "root_alias", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"],
    )
    def test_create_valid(self, op_name, a, b, expected) -> None:
        """Factory creates correct Calculation instances."""
        calc = CalculationFactory.create(a, b, op_name)
        assert calc.result == expected
        assert calc.operation_name == op_name

    def test_create_unknown_operation(self) -> None:
        """Unknown operation raises InvalidOperationError."""
        with pytest.raises(InvalidOperationError, match="Unknown operation"):
            CalculationFactory.create(Decimal("1"), Decimal("2"), "modulo")

    def test_create_division_by_zero(self) -> None:
        """Factory propagates DivisionByZeroError."""
        with pytest.raises(DivisionByZeroError):
            CalculationFactory.create(Decimal("10"), Decimal("0"), "divide")

    def test_get_supported_operations(self) -> None:
        """All operations are returned."""
        ops = CalculationFactory.get_supported_operations()
        expected_ops = {"add", "subtract", "multiply", "divide", "power", "root", "nth_power", "nth_root", "percentage", "sqrt", "cube", "cbrt"}
        assert set(ops) == expected_ops
