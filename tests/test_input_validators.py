"""
Tests for the Input Validators Module
=======================================

Parameterized tests for LBYL validation helpers.
"""

import pytest
from decimal import Decimal

from app.input_validators import validate_input_parts, validate_numeric


# ---------------------------------------------------------------------------
# validate_input_parts
# ---------------------------------------------------------------------------


class TestValidateInputParts:
    """Tests for validate_input_parts."""

    @pytest.mark.parametrize(
        "parts",
        [
            ["add", "5", "3"],
            ["subtract", "10", "4"],
            ["modulus", "10", "3"],
            ["percent", "5", "100"],
        ],
    )
    def test_valid_input(self, parts: list[str]) -> None:
        """Valid three-token input with known operation returns None."""
        assert validate_input_parts(parts) is None

    def test_wrong_token_count(self) -> None:
        """Incorrect number of tokens returns an error."""
        assert validate_input_parts(["add", "5"]) is not None
        assert validate_input_parts([]) is not None

    def test_unknown_operation(self) -> None:
        """Unknown operation name returns an error."""
        assert validate_input_parts(["unknown", "1", "2"]) is not None

    def test_range_validation(self) -> None:
        """Operands exceeding max_value return an error."""
        assert validate_input_parts(["add", "1e11", "1"], max_value=1e10) is not None
        assert validate_input_parts(["add", "1", "1e11"], max_value=1e10) is not None
        assert validate_input_parts(["add", "1e10", "1e10"], max_value=1e10) is None

    def test_invalid_numeric_operands(self) -> None:
        """Non-numeric operands return an error."""
        assert validate_input_parts(["add", "abc", "1"]) is not None
        assert validate_input_parts(["add", "1", "def"]) is not None


# ---------------------------------------------------------------------------
# validate_numeric
# ---------------------------------------------------------------------------


class TestValidateNumeric:
    """Tests for validate_numeric."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("5", Decimal("5")),
            ("-3.14", Decimal("-3.14")),
            ("0", Decimal("0")),
        ],
    )
    def test_valid_numbers(self, value: str, expected: Decimal) -> None:
        """Valid numeric strings convert to Decimal."""
        assert validate_numeric(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["abc", "", "12.34.56"],
    )
    def test_invalid_numbers(self, value: str) -> None:
        """Invalid numeric strings return None."""
        assert validate_numeric(value) is None
