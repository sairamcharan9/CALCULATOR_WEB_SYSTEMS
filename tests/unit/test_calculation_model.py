"""
Unit Tests for Calculation Model & Pydantic Schemas
===================================================

Tests the Pydantic schemas (OperationType parsing, division by zero blocking)
and the CalculationModelFactory logic.
"""

import pytest
from pydantic import ValidationError
from app.schemas import CalculationCreate, OperationType
from app.models import CalculationModelFactory, Calculation


class TestCalculationCreateSchema:
    """Tests Pydantic validation for incoming calculation operations."""

    def test_valid_operation(self):
        """CalculationCreate accepts valid operands and type."""
        calc = CalculationCreate(a=10.5, b=2.0, type="ADD")
        assert calc.a == 10.5
        assert calc.b == 2.0
        assert calc.type == OperationType.ADD

    def test_invalid_operation_type_rejected(self):
        """CalculationCreate rejects unknown text for type."""
        with pytest.raises(ValidationError) as exc:
            CalculationCreate(a=1, b=2, type="SQUARE_ROOT")
        assert "Input should be" in str(exc.value)

    def test_division_by_zero_rejected(self):
        """CalculationCreate blocks b=0 when type is DIVIDE."""
        with pytest.raises(ValidationError) as exc:
            CalculationCreate(a=10, b=0, type="DIVIDE")
        assert "Cannot divide by zero" in str(exc.value)

    def test_int_division_by_zero_rejected(self):
        """CalculationCreate blocks b=0 when type is INT_DIVIDE."""
        with pytest.raises(ValidationError) as exc:
            CalculationCreate(a=10, b=0, type="INT_DIVIDE")
        assert "Cannot divide by zero" in str(exc.value)

    def test_addition_with_zero_allowed(self):
        """CalculationCreate allows b=0 for safe operations like ADD."""
        calc = CalculationCreate(a=10, b=0, type="ADD")
        assert calc.b == 0.0


class TestCalculationModelFactory:
    """Tests the factory instantiate logic and math."""

    def test_factory_addition(self):
        """Factory computes ADD correctly."""
        calc = CalculationModelFactory.create_calculation(user_id=1, a=5.0, b=3.0, operation_type="add")
        assert isinstance(calc, Calculation)
        assert calc.result == 8.0
        assert calc.type == "ADD"
        assert calc.user_id == 1

    def test_factory_subtraction(self):
        """Factory computes SUBTRACT correctly."""
        calc = CalculationModelFactory.create_calculation(user_id=1, a=10.0, b=4.0, operation_type="SUBTRACT")
        assert calc.result == 6.0

    def test_factory_multiplication(self):
        """Factory computes MULTIPLY correctly."""
        calc = CalculationModelFactory.create_calculation(user_id=1, a=2.0, b=3.5, operation_type="multiply")
        assert calc.result == 7.0

    def test_factory_division(self):
        """Factory computes DIVIDE correctly."""
        calc = CalculationModelFactory.create_calculation(user_id=1, a=10.0, b=2.0, operation_type="divide")
        assert calc.result == 5.0

    def test_factory_int_division(self):
        """Factory computes INT_DIVIDE correctly."""
        calc = CalculationModelFactory.create_calculation(user_id=1, a=10.0, b=3.0, operation_type="INT_DIVIDE")
        assert calc.result == 3.0

    def test_factory_division_by_zero_shield(self):
        """Factory blocks direct zero division strings."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            CalculationModelFactory.create_calculation(user_id=1, a=10.0, b=0, operation_type="DIVIDE")

    def test_factory_unsupported_operation(self):
        """Factory raises ValueError for unsupported types."""
        with pytest.raises(ValueError, match="Unsupported calculation type: UNKNOWN"):
            CalculationModelFactory.create_calculation(user_id=1, a=1.0, b=1.0, operation_type="UNKNOWN")
