from decimal import Decimal
import pytest
from app.input_validators import validate_input_parts, validate_numeric

class TestInputValidators:
    # Test cases for validate_input_parts
    def test_validate_input_parts_empty_input(self):
        result = validate_input_parts([])
        assert result == "Error: No input provided. Please enter a command."

    @pytest.mark.parametrize("parts, expected_error", [
        (["add"], "Error: Invalid format. Please use: <operation> <number1> <number2>\nExample: add 5 3\nType 'help' for available commands."),
        (["add", "5"], "Error: Invalid format. Please use: <operation> <number1> <number2>\nExample: add 5 3\nType 'help' for available commands."),
        (["add", "5", "3", "extra"], "Error: Invalid format. Please use: <operation> <number1> <number2>\nExample: add 5 3\nType 'help' for available commands."),
    ])
    def test_validate_input_parts_incorrect_number_of_parts(self, parts, expected_error):
        result = validate_input_parts(parts)
        assert result == expected_error

    @pytest.mark.parametrize("parts, expected_error", [
        (["add", "abc", "3"], "Error: 'abc' is not a valid number."),
        (["add", "5", "xyz"], "Error: 'xyz' is not a valid number."),
    ])
    def test_validate_input_parts_non_numeric_operands(self, parts, expected_error):
        result = validate_input_parts(parts)
        assert result == expected_error

    @pytest.mark.parametrize("parts, max_value, expected_error", [
        (["add", "1e11", "3"], 1e10, "Error: Operand '1e11' exceeds the maximum allowed value of 10000000000.0."),
        (["add", "5", "1e11"], 1e10, "Error: Operand '1e11' exceeds the maximum allowed value of 10000000000.0."),
        (["add", "-1e11", "3"], 1e10, "Error: Operand '-1e11' exceeds the maximum allowed value of 10000000000.0."),
    ])
    def test_validate_input_parts_operands_exceeding_max_value(self, parts, max_value, expected_error):
        result = validate_input_parts(parts, max_value=max_value)
        assert result == expected_error

    @pytest.mark.parametrize("parts, max_value", [
        (["add", "5", "3"], 1e10),
        (["subtract", "10.5", "2"], 1e10),
    ])
    def test_validate_input_parts_valid_input(self, parts, max_value):
        result = validate_input_parts(parts, max_value=max_value)
        assert result is None

    # Test cases for validate_numeric
    @pytest.mark.parametrize("value, expected", [
        ("123", Decimal('123')),
        ("123.45", Decimal('123.45')),
        ("-10", Decimal('-10')),
        ("0", Decimal('0')),
        (".5", Decimal('0.5')),
        ("1e-5", Decimal('0.00001')),
        ("1e5", Decimal('100000')),
    ])
    def test_validate_numeric_valid_input(self, value, expected):
        result = validate_numeric(value)
        assert result == expected

    def test_validate_numeric_invalid_input(self):
        result = validate_numeric("abc")
        assert result is None
        result = validate_numeric("123a")
        assert result is None
