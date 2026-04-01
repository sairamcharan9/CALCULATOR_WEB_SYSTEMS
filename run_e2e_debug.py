import traceback
from tests.fastapi.e2e.test_e2e import test_addition_e2e, test_subtraction_e2e, test_divide_by_zero_e2e, test_history_e2e

tests = [
    test_addition_e2e,
    test_subtraction_e2e,
    test_divide_by_zero_e2e,
    test_history_e2e
]

for t in tests:
    print(f"Running {t.__name__}...")
    try:
        t()
        print(f"Passed: {t.__name__}\n")
    except Exception as e:
        print(f"FAILED: {t.__name__}\n")
        with open("e2e_debug_out.txt", "w") as f:
            traceback.print_exc(file=f)
            f.write(f"\nError string: {str(e)}")
        print("Wrote traceback to e2e_debug_out.txt")
        break
