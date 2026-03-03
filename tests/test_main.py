
from unittest.mock import patch
import main

def test_main():
    with patch('main.Calculator') as MockCalc:
        main.main()
        MockCalc.return_value.run.assert_called_once()
