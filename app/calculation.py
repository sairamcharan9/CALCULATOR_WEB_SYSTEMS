"""
Calculation Module (Factory Pattern)
=====================================

- **Calculation**: Represents a single arithmetic calculation with one or two
  operands, an operation, and a computed result.
- **CalculationFactory**: Creates ``Calculation`` instances from string
  operation names using the operations registry (Factory Pattern).
"""

from decimal import Decimal
from typing import Callable, Optional

from app.operations import get_operation, get_supported_operations


class Calculation:
    """Immutable record of a single arithmetic calculation.

    Attributes:
        operand_a: The first operand.
        operand_b: The second operand (optional for single-operand ops).
        operation: The callable that performs the arithmetic.
        operation_name: Human-readable name for the operation.
        result: The computed result.
    """

    # Symbols used in the user-friendly __str__ representation
    _SYMBOLS: dict[str, str] = {
        "add": "+",
        "subtract": "-",
        "multiply": "*",
        "divide": "/",
        "power": "^",
        "root": "√",
        "percentage": "%",
        "sqrt": "√",
        "cube": "^3",
        "cbrt": "³√",
    }

    def __init__(
        self,
        operand_a: Decimal,
        operand_b: Optional[Decimal],
        operation: Callable,
        operation_name: str,
    ) -> None:
        """Initialize and immediately compute the calculation.

        Args:
            operand_a: The first operand.
            operand_b: The second operand (or None for single-operand ops).
            operation: Callable that performs the arithmetic.
            operation_name: Human-readable name (e.g., ``"add"``).

        Raises:
            DivisionByZeroError: If the operation involves division by zero.
            InvalidOperationError: If the operation is mathematically invalid.
        """
        self.operand_a = operand_a
        self.operand_b = operand_b
        self.operation = operation
        self.operation_name = operation_name
        
        if operand_b is not None:
            self.result = operation(operand_a, operand_b)
        else:
            self.result = operation(operand_a)

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        if self.operand_b is not None:
            return (
                f"Calculation({self.operand_a}, {self.operand_b}, "
                f"{self.operation_name}) = {self.result}"
            )
        return (
            f"Calculation({self.operand_a}, {self.operation_name}) = {self.result}"
        )

    def __str__(self) -> str:
        """Return a user-friendly string (e.g. ``5 + 3 = 8``)."""
        symbol = self._SYMBOLS.get(self.operation_name, self.operation_name)
        if self.operand_b is not None:
            return f"{self.operand_a} {symbol} {self.operand_b} = {self.result}"
        
        # Format for single-operand operations
        if self.operation_name in ("cube",):
            return f"{self.operand_a}{symbol} = {self.result}"
        return f"{symbol}({self.operand_a}) = {self.result}"


class CalculationFactory:
    """Factory that creates ``Calculation`` instances from operation names.

    Uses ``operations.get_operation`` to look up the callable, keeping
    the mapping in one place (Strategy + Factory patterns).
    """

    @staticmethod
    def create(
        operand_a: Decimal, operand_b: Optional[Decimal], operation_name: str
    ) -> "Calculation":
        """Create a ``Calculation`` from an operation name string.

        Args:
            operand_a: The first operand.
            operand_b: The second operand (or None).
            operation_name: Name of the operation.

        Returns:
            A ``Calculation`` with the result already computed.

        Raises:
            InvalidOperationError: If the name is not recognized.
            DivisionByZeroError: If dividing / rooting by zero.
        """
        operation = get_operation(operation_name)
        return Calculation(operand_a, operand_b, operation, operation_name)

    @staticmethod
    def get_supported_operations() -> list[str]:
        """Return a list of supported operation names."""
        return get_supported_operations()
