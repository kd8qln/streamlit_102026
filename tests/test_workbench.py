import csv
import io
import unittest

from workbench import (
    TABLE_DEFINITIONS,
    calculate_batch,
    calculate_experiment_summary,
    calculate_formula,
    records_to_csv,
)


class WorkbenchTests(unittest.TestCase):
    def test_experiment_summary_ignores_blank_rows(self) -> None:
        summary = calculate_experiment_summary(
            [{"Value": 2}, {"Value": "4"}, {"Value": None}]
        )
        self.assertEqual(summary, {"Count": 2, "Mean": 3, "Minimum": 2, "Maximum": 4})

    def test_formula_calculates_batch_amounts(self) -> None:
        total, results = calculate_formula(
            200,
            [
                {"Component": "A", "Percent": 25},
                {"Component": "B", "Percent": 75},
            ],
        )
        self.assertEqual(total, 100)
        self.assertEqual([row["Batch Amount"] for row in results], [50, 150])

    def test_batch_calculator_retains_row_errors(self) -> None:
        results = calculate_batch(
            [
                {"Left": 3, "Operation": "+", "Right": 4},
                {"Left": 5, "Operation": "÷", "Right": 0},
                {"Left": None, "Operation": "+", "Right": None},
            ]
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["Result"], 7)
        self.assertEqual(results[0]["Status"], "OK")
        self.assertIn("divide by zero", results[1]["Status"])

    def test_table_definitions_are_in_memory_and_export_as_csv(self) -> None:
        self.assertEqual(
            set(TABLE_DEFINITIONS),
            {
                "FormulaNumber",
                "ProjectData",
                "VoyagerInfo_Component",
                "VoyagerInfo_ElementSymbols",
            },
        )
        csv_text = records_to_csv(
            [{"Experiment": "Mix A", "Value": 1.5}], ["Experiment", "Value"]
        ).decode("utf-8")
        self.assertEqual(
            list(csv.DictReader(io.StringIO(csv_text))),
            [{"Experiment": "Mix A", "Value": "1.5"}],
        )


if __name__ == "__main__":
    unittest.main()