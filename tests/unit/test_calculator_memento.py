"""
Tests for the Calculator Memento Module
=========================================

Tests for CalculatorMemento and MementoCaretaker — undo/redo
functionality over the pandas-backed CalculationHistory.
"""

import pytest
import pandas as pd
from decimal import Decimal

from app.calculation import Calculation
from app.operations import add, subtract
from app.history import CalculationHistory
from app.calculator_memento import CalculatorMemento, MementoCaretaker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def history(tmp_path) -> CalculationHistory:
    return CalculationHistory(history_dir=str(tmp_path), history_file="test.csv")


@pytest.fixture
def caretaker(history: CalculationHistory) -> MementoCaretaker:
    return MementoCaretaker(history)


@pytest.fixture
def sample_calc() -> Calculation:
    return Calculation(Decimal("2"), Decimal("3"), add, "add", precision=2)


@pytest.fixture
def sample_calc2() -> Calculation:
    return Calculation(Decimal("10"), Decimal("4"), subtract, "subtract", precision=2)


# ---------------------------------------------------------------------------
# CalculatorMemento
# ---------------------------------------------------------------------------


class TestCalculatorMemento:
    """Tests for the CalculatorMemento snapshot."""

    def test_memento_stores_copy(self) -> None:
        """Memento stores a copy of the DataFrame, not a reference."""
        original = pd.DataFrame([{"a": 1}])
        memento = CalculatorMemento(original)
        original.drop(index=0, inplace=True)
        assert len(memento.dataframe) == 1

    def test_repr(self) -> None:
        """The repr string includes the dataset size."""
        memento = CalculatorMemento(pd.DataFrame({"A": [1, 2]}))
        assert "rows=2" in repr(memento)


# ---------------------------------------------------------------------------
# MementoCaretaker — undo
# ---------------------------------------------------------------------------


class TestMementoUndo:
    """Tests for undo functionality."""

    def test_undo_empty(self, caretaker: MementoCaretaker) -> None:
        """Undo on empty stack returns False."""
        assert caretaker.undo() is False

    def test_undo_restores_state(
        self,
        history: CalculationHistory,
        caretaker: MementoCaretaker,
        sample_calc: Calculation,
    ) -> None:
        """Undo restores the previous history state."""
        # Save empty state
        caretaker.save()
        history.add(sample_calc)
        assert len(history) == 1

        # Undo should restore to empty
        assert caretaker.undo() is True
        assert len(history) == 0

    def test_can_undo(self, caretaker: MementoCaretaker) -> None:
        """can_undo reflects stack state."""
        assert caretaker.can_undo is False
        caretaker.save()
        assert caretaker.can_undo is True


# ---------------------------------------------------------------------------
# MementoCaretaker — redo
# ---------------------------------------------------------------------------


class TestMementoRedo:
    """Tests for redo functionality."""

    def test_redo_empty(self, caretaker: MementoCaretaker) -> None:
        """Redo on empty stack returns False."""
        assert caretaker.redo() is False

    def test_redo_after_undo(
        self,
        history: CalculationHistory,
        caretaker: MementoCaretaker,
        sample_calc: Calculation,
    ) -> None:
        """Redo restores the state that was undone."""
        caretaker.save()
        history.add(sample_calc)
        assert len(history) == 1

        caretaker.undo()
        assert len(history) == 0

        assert caretaker.redo() is True
        assert len(history) == 1

    def test_can_redo(
        self,
        history: CalculationHistory,
        caretaker: MementoCaretaker,
    ) -> None:
        """can_redo reflects stack state."""
        assert caretaker.can_redo is False
        caretaker.save()
        caretaker.undo()
        assert caretaker.can_redo is True


# ---------------------------------------------------------------------------
# Undo / redo interaction
# ---------------------------------------------------------------------------


class TestUndoRedoInteraction:
    """Tests for combined undo/redo workflows."""

    def test_save_clears_redo_stack(
        self,
        history: CalculationHistory,
        caretaker: MementoCaretaker,
        sample_calc: Calculation,
    ) -> None:
        """A new save() clears the redo stack."""
        caretaker.save()
        history.add(sample_calc)

        caretaker.undo()
        assert caretaker.can_redo is True

        caretaker.save()
        assert caretaker.can_redo is False

    def test_multiple_undos(
        self,
        history: CalculationHistory,
        caretaker: MementoCaretaker,
        sample_calc: Calculation,
        sample_calc2: Calculation,
    ) -> None:
        """Multiple undos walk back through the history."""
        caretaker.save()  # state 0 (empty)
        history.add(sample_calc)

        caretaker.save()  # state 1 (1 row)
        history.add(sample_calc2)
        assert len(history) == 2

        caretaker.undo()  # back to 1 row
        assert len(history) == 1

        caretaker.undo()  # back to 0 rows
        assert len(history) == 0


# ---------------------------------------------------------------------------
# MementoCaretaker — stack_sizes
# ---------------------------------------------------------------------------


class TestStackSizes:
    """Tests for the stack_sizes property."""

    def test_initial_stack_sizes(self, caretaker: MementoCaretaker) -> None:
        """Both stacks start empty."""
        assert caretaker.stack_sizes == (0, 0)

    def test_undo_stack_grows_on_save(
        self,
        caretaker: MementoCaretaker,
        history: CalculationHistory,
        sample_calc: Calculation,
    ) -> None:
        """Undo stack grows with each save; redo stack starts empty."""
        caretaker.save()
        history.add(sample_calc)
        assert caretaker.stack_sizes == (1, 0)

        caretaker.save()
        assert caretaker.stack_sizes == (2, 0)

    def test_redo_stack_grows_on_undo(
        self,
        caretaker: MementoCaretaker,
        history: CalculationHistory,
        sample_calc: Calculation,
    ) -> None:
        """Redo stack grows with each undo."""
        caretaker.save()
        history.add(sample_calc)
        caretaker.undo()
        assert caretaker.stack_sizes == (0, 1)

    def test_stack_sizes_after_full_cycle(
        self,
        caretaker: MementoCaretaker,
        history: CalculationHistory,
        sample_calc: Calculation,
        sample_calc2: Calculation,
    ) -> None:
        """After full undo/redo cycle stacks balance correctly."""
        caretaker.save()          # snap 0 (empty)
        history.add(sample_calc)
        caretaker.save()          # snap 1 (1 row)
        history.add(sample_calc2)

        # undo twice
        caretaker.undo()
        caretaker.undo()
        undo_sz, redo_sz = caretaker.stack_sizes
        assert undo_sz == 0
        assert redo_sz == 2

        # redo once
        caretaker.redo()
        undo_sz, redo_sz = caretaker.stack_sizes
        assert undo_sz == 1
        assert redo_sz == 1


# ---------------------------------------------------------------------------
# Undo → Redo multi-step chain
# ---------------------------------------------------------------------------


class TestUndoRedoChain:
    """Walk multiple states backward and forward."""

    def test_undo_then_redo_chain(
        self,
        caretaker: MementoCaretaker,
        history: CalculationHistory,
        sample_calc: Calculation,
        sample_calc2: Calculation,
    ) -> None:
        """Can undo two steps then redo them both in order."""
        caretaker.save()          # state 0: empty
        history.add(sample_calc)
        caretaker.save()          # state 1: 1 row
        history.add(sample_calc2)
        assert len(history) == 2

        # Undo back to 1 row
        assert caretaker.undo() is True
        assert len(history) == 1

        # Undo back to empty
        assert caretaker.undo() is True
        assert len(history) == 0

        # Redo forward to 1 row
        assert caretaker.redo() is True
        assert len(history) == 1

        # Redo forward to 2 rows
        assert caretaker.redo() is True
        assert len(history) == 2

        # Nothing left to redo
        assert caretaker.redo() is False

    def test_new_action_after_undo_clears_redo(
        self,
        caretaker: MementoCaretaker,
        history: CalculationHistory,
        sample_calc: Calculation,
        sample_calc2: Calculation,
    ) -> None:
        """Performing a new save after an undo clears the redo stack."""
        caretaker.save()
        history.add(sample_calc)
        caretaker.undo()
        assert caretaker.can_redo is True

        # New action: save again (simulating a new calculation)
        caretaker.save()
        history.add(sample_calc2)
        assert caretaker.can_redo is False
