import csv
import io
import math
from typing import Any

from calculator import calculate


TABLE_DEFINITIONS: dict[str, list[dict[str, str]]] = {
    "FormulaNumber": [
        {"name": "FormulaID", "type": "number"},
        {"name": "ProjectNum", "type": "text"},
        {"name": "BaseNum", "type": "number"},
        {"name": "IterationNum", "type": "number"},
        {"name": "FormulaNum", "type": "number"},
    ],
    "ProjectData": [
        {"name": "ProjectID", "type": "number"},
        {"name": "Formulator", "type": "text"},
        {"name": "ProjectNum", "type": "number"},
        {"name": "ProjNumEngCod", "type": "text"},
        {"name": "Name", "type": "text"},
        {"name": "Description", "type": "text"},
        {"name": "Folio", "type": "text"},
    ],
    "VoyagerInfo_Component": [
        {"name": "ComponentID", "type": "number"},
        {"name": "HobartCode", "type": "text"},
        {"name": "Name", "type": "text"},
        {"name": "Description", "type": "text"},
        {"name": "RD", "type": "number"},
        {"name": "Active", "type": "checkbox"},
    ],
    "VoyagerInfo_ElementSymbols": [
        {"name": "ElementID", "type": "number"},
        {"name": "Symbol", "type": "text"},
        {"name": "Name", "type": "text"},
        {"name": "Notes", "type": "text"},
        {"name": "Metallic?", "type": "text"},
    ],
}


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def calculate_experiment_summary(
    measurements: list[dict[str, Any]],
) -> dict[str, float | int]:
    values = []
    for row in measurements:
        value = row.get("Value")
        if _is_blank(value):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Measurement values must be numeric") from error
        if not math.isfinite(number):
            raise ValueError("Measurement values must be finite numbers")
        values.append(number)

    if not values:
        raise ValueError("Enter at least one measurement value")
    return {
        "Count": len(values),
        "Mean": sum(values) / len(values),
        "Minimum": min(values),
        "Maximum": max(values),
    }


def calculate_formula(
    batch_size: float, components: list[dict[str, Any]]
) -> tuple[float, list[dict[str, Any]]]:
    if not math.isfinite(batch_size) or batch_size <= 0:
        raise ValueError("Batch size must be a positive finite number")

    total_percent = 0.0
    results = []
    for row in components:
        name = row.get("Component")
        percent = row.get("Percent")
        if _is_blank(name) and _is_blank(percent):
            continue
        if _is_blank(name):
            raise ValueError("Each percentage requires a component name")
        if _is_blank(percent):
            raise ValueError(f"Enter a percentage for {name}")
        try:
            percent_value = float(percent)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Percentage for {name} must be numeric") from error
        if not math.isfinite(percent_value) or percent_value < 0:
            raise ValueError(f"Percentage for {name} must be a finite non-negative number")
        total_percent += percent_value
        results.append(
            {
                "Component": str(name),
                "Percent": percent_value,
                "Batch Amount": batch_size * percent_value / 100,
            }
        )

    if not results:
        raise ValueError("Enter at least one formula component")
    return total_percent, results


def calculate_batch(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for row_number, row in enumerate(rows, start=1):
        left = row.get("Left")
        operator = row.get("Operation")
        right = row.get("Right")
        if _is_blank(left) and _is_blank(right):
            continue

        result_row = {
            "Row": row_number,
            "Left": left,
            "Operation": operator,
            "Right": right,
        }
        try:
            if _is_blank(left) or _is_blank(right):
                raise ValueError("Enter both operands")
            result_row["Result"] = calculate(float(left), str(operator), float(right))
            result_row["Status"] = "OK"
        except (TypeError, ValueError) as error:
            result_row["Result"] = None
            result_row["Status"] = str(error)
        results.append(result_row)
    return results


def records_to_csv(
    records: list[dict[str, Any]], fieldnames: list[str] | None = None
) -> bytes:
    if fieldnames is None:
        fieldnames = list(dict.fromkeys(key for row in records for key in row))
    if not fieldnames:
        return b""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8")