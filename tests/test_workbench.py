import csv
import io
import unittest

from workbench import (
    TABLE_DEFINITIONS,
    calculate_batch,
    calculate_composition_ranges,
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

    def test_composition_ranges_apply_constraints_to_estimated_bounds(self) -> None:
        results = calculate_composition_ranges(
            [
                {
                    "Element": "Al",
                    "Average (%)": 1.5,
                    "Standard Deviation (%)": 0.5,
                    "Minimum Constraint (%)": 1.2,
                    "Maximum Constraint (%)": 1.8,
                },
                {
                    "Element": "Ti",
                    "Average (%)": 2,
                    "Standard Deviation (%)": 0.25,
                    "Minimum Constraint (%)": None,
                    "Maximum Constraint (%)": 2.1,
                },
            ],
            1,
        )

        self.assertEqual(results[0]["Calculated Minimum (%)"], 1.0)
        self.assertEqual(results[0]["Calculated Maximum (%)"], 2.0)
        self.assertEqual(results[0]["Adjusted Minimum (%)"], 1.2)
        self.assertEqual(results[0]["Adjusted Maximum (%)"], 1.8)
        self.assertEqual(results[0]["Status"], "Adjusted by constraints")
        self.assertEqual(results[1]["Adjusted Minimum (%)"], 1.75)
        self.assertEqual(results[1]["Adjusted Maximum (%)"], 2.1)

    def test_composition_range_reports_non_overlapping_constraints(self) -> None:
        result = calculate_composition_ranges(
            [
                {
                    "Element": "Ni",
                    "Average (%)": 1.0,
                    "Standard Deviation (%)": 0.1,
                    "Minimum Constraint (%)": 1.5,
                    "Maximum Constraint (%)": None,
                }
            ],
            1,
        )[0]

        self.assertEqual(result["Adjusted Minimum (%)"], 1.5)
        self.assertEqual(result["Adjusted Maximum (%)"], 1.1)
        self.assertEqual(result["Status"], "No overlap")

    def test_composition_ranges_validate_required_inputs_and_constraints(self) -> None:
        with self.assertRaisesRegex(ValueError, "both average and standard deviation"):
            calculate_composition_ranges(
                [{"Element": "Cr", "Average (%)": 1.0}], 1
            )
        with self.assertRaisesRegex(ValueError, "Minimum constraint exceeds"):
            calculate_composition_ranges(
                [
                    {
                        "Element": "Cr",
                        "Average (%)": 1.0,
                        "Standard Deviation (%)": 0.1,
                        "Minimum Constraint (%)": 2.0,
                        "Maximum Constraint (%)": 1.0,
                    }
                ],
                1,
            )

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