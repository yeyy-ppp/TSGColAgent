from __future__ import annotations


def classify_score(score: int) -> str:
    if score < 0:
        raise ValueError("score cannot be negative")
    if score >= 90:
        return "excellent"
    if score >= 60:
        return "pass"
    return "fail"


def sum_positive(values: list[int]) -> int:
    total = 0
    for value in values:
        if value > 0:
            total += value
    return total


def countdown(n: int) -> list[int]:
    result = []
    while n > 0:
        result.append(n)
        n -= 1
    return result


def describe(value: object) -> str:
    match value:
        case None:
            return "none"
        case int() if value > 0:
            return "positive int"
        case str():
            return "text"
        case _:
            return "other"


async def async_double(x: int) -> int:
    return x * 2


def generate_first(n: int):
    for item in range(n):
        yield item
