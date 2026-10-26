"""A deterministic task set.

Each task is a small quantitative question with an exact answer, generated from a
seed. No model and no network: the benchmark measures *patterns*, not model quality.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SIMPLE = "simple"
COMPOUND = "compound"
PERCENT = "percent"
UNIT = "unit"
KINDS = (SIMPLE, COMPOUND, PERCENT, UNIT)

UNITS = {
    "km": ("m", 1000.0),
    "m": ("cm", 100.0),
    "kg": ("g", 1000.0),
    "hour": ("min", 60.0),
    "GB": ("MB", 1024.0),
}


@dataclass(frozen=True)
class Task:
    id: str
    kind: str
    prompt: str
    answer: float
    numbers: tuple[float, ...]
    unit_from: str = ""
    unit_to: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "prompt": self.prompt,
            "answer": self.answer,
            "numbers": list(self.numbers),
        }


def generate(count: int = 40, seed: int = 7) -> list[Task]:
    rng = random.Random(seed)
    tasks: list[Task] = []
    for index in range(count):
        kind = KINDS[index % len(KINDS)]
        tasks.append(_build(kind, index, rng))
    return tasks


def _build(kind: str, index: int, rng: random.Random) -> Task:
    if kind == SIMPLE:
        a, b = rng.randint(11, 89), rng.randint(11, 89)
        return Task(
            id=f"T{index:03d}",
            kind=kind,
            prompt=f"What is {a} + {b}?",
            answer=float(a + b),
            numbers=(float(a), float(b)),
        )
    if kind == COMPOUND:
        start, delta, factor = rng.randint(5, 20), rng.randint(2, 12), rng.randint(2, 6)
        return Task(
            id=f"T{index:03d}",
            kind=kind,
            prompt=f"Start with {start}, add {delta}, then multiply the result by {factor}. What is the final number?",
            answer=float((start + delta) * factor),
            numbers=(float(start), float(delta), float(factor)),
        )
    if kind == PERCENT:
        whole, pct = rng.randint(80, 400), rng.choice((5, 10, 15, 20, 25))
        return Task(
            id=f"T{index:03d}",
            kind=kind,
            prompt=f"What is {pct}% of {whole}?",
            answer=round(pct / 100 * whole, 4),
            numbers=(float(pct), float(whole)),
        )
    unit = rng.choice(sorted(UNITS))
    target, factor = UNITS[unit]
    amount = round(rng.uniform(1.5, 9.5), 1)
    return Task(
        id=f"T{index:03d}",
        kind=kind,
        prompt=f"Convert {amount} {unit} to {target}. Answer in {target}.",
        answer=round(amount * factor, 4),
        numbers=(amount,),
        unit_from=unit,
        unit_to=target,
    )


def parse_prediction(value: str | float) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def is_correct(prediction: float | None, task: Task, tolerance: float = 0.01) -> bool:
    if prediction is None:
        return False
    return abs(prediction - task.answer) <= max(tolerance, abs(task.answer) * 1e-6)
