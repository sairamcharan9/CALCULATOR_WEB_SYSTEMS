"""
Memento Pattern for Undo/Redo Functionality
===========================================

This module implements the Memento design pattern to provide undo and redo
capabilities for the calculator's history. The pattern allows capturing and
restoring the internal state of an object (the `CalculationHistory`) without
violating its encapsulation.

Classes:
    - CalculatorMemento: Stores a snapshot of the `CalculationHistory` state.
      This is the "Memento" object, representing a particular state in time.
    - MementoCaretaker: Manages the undo and redo stacks of mementos. This is
      the "Caretaker," responsible for orchestrating save and restore operations.
"""

from __future__ import annotations

import pandas as pd

from app.history import CalculationHistory


class CalculatorMemento:
    """
    Represents a snapshot of the calculator's history state (the "Memento").

    This class holds an immutable copy of the history DataFrame at the moment
    the memento is created, ensuring that the stored state is isolated from
    future modifications.

    Attributes:
        dataframe (pd.DataFrame): A deep copy of the history DataFrame.
    """

    def __init__(self, dataframe: pd.DataFrame) -> None:
        """
        Initializes the memento with a copy of the history DataFrame.

        Args:
            dataframe (pd.DataFrame): The DataFrame to be saved in the memento.
        """
        self.dataframe = dataframe.copy()

    def __repr__(self) -> str:
        """Returns a string representation of the memento, including the number of history rows."""
        return f"CalculatorMemento(rows={len(self.dataframe)})"


class MementoCaretaker:
    """
    Manages the undo and redo stacks for `CalculatorMemento` objects (the "Caretaker").

    This class provides the core logic for saving history states and rolling back
    or forward through these states. It directly interacts with the `CalculationHistory`
    object to restore its state from a memento.

    Attributes:
        history (CalculationHistory): The instance of `CalculationHistory` being managed.
    """

    def __init__(self, history: CalculationHistory) -> None:
        """
        Initializes the caretaker with a reference to the calculation history.

        Args:
            history (CalculationHistory): The history object to be managed.
        """
        self.history = history
        self._undo_stack: list[CalculatorMemento] = []
        self._redo_stack: list[CalculatorMemento] = []

    def save(self) -> None:
        """
        Saves the current state of the calculation history to the undo stack.

        When a new state is saved, the redo stack is cleared, as the new action
        creates a new branch of history, making the old redo path invalid.
        """
        snapshot = CalculatorMemento(self.history.get_dataframe())
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()

    def undo(self) -> bool:
        """
        Restores the most recent state from the undo stack.

        The current state is pushed to the redo stack before restoring the previous state,
        allowing the `redo` operation to reverse the `undo`.

        Returns:
            bool: True if the undo was successful, False if the undo stack was empty.
        """
        if not self.can_undo:
            return False

        # Save the current state to the redo stack before reverting
        current_state = CalculatorMemento(self.history.get_dataframe())
        self._redo_stack.append(current_state)

        # Pop from the undo stack and restore the history
        memento = self._undo_stack.pop()
        self.history.set_dataframe(memento.dataframe)
        return True

    def redo(self) -> bool:
        """
        Restores the most recent state from the redo stack.

        The current state is pushed back to the undo stack, allowing for multiple
        undos and redos in sequence.

        Returns:
            bool: True if the redo was successful, False if the redo stack was empty.
        """
        if not self.can_redo:
            return False

        # Save the current state back to the undo stack
        current_state = CalculatorMemento(self.history.get_dataframe())
        self._undo_stack.append(current_state)

        # Pop from the redo stack and restore the history
        memento = self._redo_stack.pop()
        self.history.set_dataframe(memento.dataframe)
        return True

    @property
    def can_undo(self) -> bool:
        """Returns True if there are states in the undo stack, False otherwise."""
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        """Returns True if there are states in the redo stack, False otherwise."""
        return bool(self._redo_stack)

    @property
    def stack_sizes(self) -> tuple[int, int]:
        """Returns the current sizes of the undo and redo stacks as a tuple."""
        return len(self._undo_stack), len(self._redo_stack)
