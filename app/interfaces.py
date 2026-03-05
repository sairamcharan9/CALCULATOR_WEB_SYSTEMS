from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.calculator_repl import Calculator

class Command(ABC):
    """
    Abstract base class for the Command design pattern.
    All concrete commands should inherit from this class and implement the execute method.
    """
    @abstractmethod
    def execute(self):
        """
        Executes the command.
        """
        pass

class CalculatorCommand(Command):
    """
    Abstract base class for commands that operate on the Calculator instance.
    """
    def __init__(self, calculator: 'Calculator'):
        self.calculator = calculator
