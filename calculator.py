from collections.abc import Callable


def _divide(left: float, right: float) -> float:
    if right == 0:
        raise ValueError("Cannot divide by zero.")
    return left / right


OPERATIONS: dict[str, Callable[[float, float], float]] = {
    "+": lambda left, right: left + right,
    "-": lambda left, right: left - right,
    "×": lambda left, right: left * right,
    "÷": _divide,
}


def calculate(left: float, operator: str, right: float) -> float:
    """Apply a registered arithmetic operation to two numbers."""
    try:
        operation = OPERATIONS[operator]
    except KeyError as error:
        raise ValueError(f"Unsupported operation: {operator}") from error
    return operation(left, right)