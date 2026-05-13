from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Optional
from datetime import datetime

from app.cli.interfaces import Command  # Import Command
from app.cli.command_loader import command_manager
from app.core.exceptions import InvalidOperationError, DivisionByZeroError


class Calculation(Command):  # Inherit from Command
    """
    Represents a single, immutable arithmetic calculation.

    Attributes:
        operand_a (Decimal): The first operand of the calculation.
        operand_b (Decimal): The second operand of the calculation.
        operation (Callable): The function that performs the arithmetic operation.
        operation_name (str): The human-readable name of the operation (e.g., "add").
        result (Decimal): The result of the calculation, rounded to a specified precision.
        timestamp (datetime): The timestamp of when the calculation was created.
    """

    # A dictionary mapping operation names to their corresponding mathematical symbols.
    _SYMBOLS: dict[str, str] = {
        "add": "+",
        "subtract": "-",
        "multiply": "*",
        "divide": "/",
        "power": "^",
        "root": "root",
        "modulus": "%",
        "int_divide": "//",
        "percent": "%%",
        "abs_diff": "|-|",
    }

    def __init__(
        self,
        operand_a: Decimal,
        operand_b: Decimal,
        operation: Callable,
        operation_name: str,
        precision: int = 2
    ) -> None:
        self.operand_a = operand_a
        self.operand_b = operand_b
        self.operation = operation
        self.operation_name = operation_name
        self.precision = precision
        self.timestamp = datetime.now()
        self.result: Optional[Decimal] = None

    def execute(self) -> Decimal:
        """Executes the encapsulated arithmetic operation and returns the result."""
        try:
            raw_result = self.operation(self.operand_a, self.operand_b)
            if self.precision >= 0:
                rounding_format = f"0.{'0' * self.precision}" if self.precision > 0 else "0"
                self.result = raw_result.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
            else:  # pragma: no cover
                self.result = raw_result
        except DivisionByZeroError:
            self.result = Decimal('NaN')
            raise
        return self.result

    def __repr__(self) -> str:
        return (
            f"Calculation({self.operand_a}, {self.operand_b}, "
            f"'{self.operation_name}') = {self.result}"
        )

    def __str__(self) -> str:
        symbol = self._SYMBOLS.get(self.operation_name, f"({self.operation_name})")
        return f"{self.operand_a} {symbol} {self.operand_b} = {self.result}"


class CalculationFactory:
    """
    A factory class for creating `Calculation` objects.

    Decouples the Calculator from the Calculation instantiation process,
    following the Factory Method design pattern.
    """

    @staticmethod
    def create(
        operand_a: Decimal,
        operand_b: Decimal,
        operation_name: str,
        precision: int = 2
    ) -> "Calculation":
        """Creates a `Calculation` instance for the specified operation."""
        command = command_manager.get_command(operation_name)
        if not command or not ("<" in command.usage and "[" not in command.usage):
            raise InvalidOperationError(f"Unknown or non-arithmetic operation: '{operation_name}'")

        return Calculation(operand_a, operand_b, command.handler, operation_name, precision)

    @staticmethod
    def get_supported_operations() -> list[str]:
        """Retrieves a list of all supported operation names."""
        return [cmd.name for cmd in command_manager.get_all_commands() if "<" in cmd.usage and "[" not in cmd.usage]
