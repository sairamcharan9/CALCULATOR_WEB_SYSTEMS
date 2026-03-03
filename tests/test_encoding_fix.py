
import pytest
from unittest.mock import patch
from app.history import LoggingObserver
from app.calculation import Calculation

def test_logging_observer_encoding_error():
    observer = LoggingObserver()
    # Mock a calculation
    class MockOp:
        __name__ = "add"
    calc = patch('app.calculation.Calculation').start()
    calc.__str__.return_value = "√9 = 3"
    
    with patch('builtins.print', side_effect=[UnicodeEncodeError('charmap', "", 0, 1, "reason"), None]):
        observer.on_calculation(calc)
    
    # If no exception raised, it means it caught it and called print again.
    assert len(observer.log_messages) == 1
