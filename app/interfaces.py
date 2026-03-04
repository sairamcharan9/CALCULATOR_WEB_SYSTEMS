from abc import ABC, abstractmethod

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
