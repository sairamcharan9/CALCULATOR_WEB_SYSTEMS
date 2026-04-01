from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Optional
from datetime import datetime

from app.interfaces import Command  # Import Command
from app.command_loader import command_manager
from app.exceptions import InvalidOperationError, DivisionByZeroError


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

    # A dictionary mapping operation names to their corresponding mathematical symbols
    # for a user-friendly string representation.
    _SYMBOLS: dict[str, str] = {
        "add": "+",
        "subtract": "-",
        "multiply": "*",
        "divide": "/",
        "power": "^",
        "root": "√",
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
        """
        Initializes a new Calculation instance. The result is computed when execute() is called.

        Args:
            operand_a (Decimal): The first operand.
            operand_b (Decimal): The second operand.
            operation (Callable): The function to execute for the calculation.
            operation_name (str): The name of the operation.
            precision (int): The number of decimal places for rounding the result.
        """
        self.operand_a = operand_a
        self.operand_b = operand_b
        self.operation = operation
        self.operation_name = operation_name
        self.precision = precision
        self.timestamp = datetime.now()
        self.result: Optional[Decimal] = None  # Result will be set by execute

    def execute(self) -> Decimal:
        """
        Executes the encapsulated arithmetic operation and returns the result.
        """
        try:
            raw_result = self.operation(self.operand_a, self.operand_b)
            if self.precision >= 0:
                rounding_format = f"0.{'0' * self.precision}" if self.precision > 0 else "0"
                self.result = raw_result.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
            else:  # pragma: no cover
                self.result = raw_result
        except DivisionByZeroError:
            self.result = Decimal('NaN')
            raise # Re-raise the exception to be caught by the test
        return self.result

    def __repr__(self) -> str:
        """
        Provides an unambiguous string representation of the Calculation instance,
        useful for debugging.
        """
        return (
            f"Calculation({self.operand_a}, {self.operand_b}, "
            f"'{self.operation_name}') = {self.result}"
        )

    def __str__(self) -> str:
        """
        Provides a user-friendly string representation of the calculation,
        formatted like a mathematical equation.
        """
        symbol = self._SYMBOLS.get(self.operation_name, f"({self.operation_name})")
        return f"{self.operand_a} {symbol} {self.operand_b} = {self.result}"


class CalculationFactory:
    """
    A factory class for creating `Calculation` objects.

    This class decouples the `Calculator` from the `Calculation` instantiation process,
    following the Factory Method design pattern. It uses a registry of operations
    to create `Calculation` instances based on a given operation name.
    """

    @staticmethod
    def create(
        operand_a: Decimal,
        operand_b: Decimal,
        operation_name: str,
        precision: int = 2
    ) -> "Calculation":
        """
        Creates a `Calculation` instance for the specified operation.

        Args:
            operand_a (Decimal): The first operand.
            operand_b (Decimal): The second operand.
            operation_name (str): The name of the operation (e.g., 'add').
            precision (int): The precision to use for the calculation result.

        Returns:
            Calculation: A new instance of the `Calculation` class.

        Raises:
            InvalidOperationError: If the requested operation name is not supported.
        """
        command = command_manager.get_command(operation_name)
        if not command or not ("<" in command.usage and "[" not in command.usage):  # Check for an arithmetic command
            raise InvalidOperationError(f"Unknown or non-arithmetic operation: '{operation_name}'")
        
        return Calculation(operand_a, operand_b, command.handler, operation_name, precision)

    @staticmethod
    def get_supported_operations() -> list[str]:
        """
        Retrieves a list of all supported operation names.

        Returns:
            list[str]: A list of strings, where each string is a supported operation name.
        """
        # Filter for commands that look like arithmetic operations
        return [cmd.name for cmd in command_manager.get_all_commands() if "<" in cmd.usage and "[" not in cmd.usage]