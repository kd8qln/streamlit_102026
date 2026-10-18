import tempfile
import unittest
from pathlib import Path

from calculator import calculate
from database import clear_history, get_history, save_calculation


class CalculatorTests(unittest.TestCase):
    def test_basic_operations(self) -> None:
        self.assertEqual(calculate(7, "+", 3), 10)
        self.assertEqual(calculate(7, "-", 3), 4)
        self.assertEqual(calculate(7, "×", 3), 21)
        self.assertEqual(calculate(7, "÷", 2), 3.5)

    def test_division_by_zero_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "divide by zero"):
            calculate(7, "÷", 0)

    def test_unknown_operation_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported operation"):
            calculate(7, "%", 3)


class DatabaseTests(unittest.TestCase):
    def test_history_can_be_saved_read_and_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "history.sqlite3"
            save_calculation(7, "+", 3, 10, database_path)

            history = get_history(db_path=database_path)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["Left"], 7)
            self.assertEqual(history[0]["Operation"], "+")
            self.assertEqual(history[0]["Result"], 10)

            clear_history(database_path)
            self.assertEqual(get_history(db_path=database_path), [])


if __name__ == "__main__":
    unittest.main()