"""Five agentic patterns, implemented as pure functions.

Each pattern returns an :class:`Attempt`: an answer, the number of reasoning steps
it consumed, and a trace a human can read. The differences between them are exactly
the trade-offs the benchmark is meant to expose — accuracy bought with steps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from patternbench.task import COMPOUND, PERCENT, SIMPLE, UNITS, Task

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class Attempt:
    answer: float | None
    steps: int
    trace: tuple[str, ...] = field(default_factory=tuple)

    @property
    def tokens(self) -> int:
        return max(1, sum(len(line) for line in self.trace) // 4)


def _numbers(task: Task) -> list[float]:
    return [float(value) for value in _NUMBER_RE.findall(task.prompt)]


def _solve(task: Task) -> tuple[float | None, list[str]]:
    """A correct specialist solver, used by the stronger patterns."""

    numbers = _numbers(task)
    if task.kind == SIMPLE:
        return numbers[0] + numbers[1], [f"add {numbers[0]:g} and {numbers[1]:g}"]
    if task.kind == COMPOUND:
        start, delta, factor = numbers[0], numbers[1], numbers[2]
        return (start + delta) * factor, [
            f"start at {start:g}",
            f"add {delta:g} → {start + delta:g}",
            f"multiply by {factor:g} → {(start + delta) * factor:g}",
        ]
    if task.kind == PERCENT:
        pct, whole = numbers[0], numbers[1]
        return round(pct / 100 * whole, 4), [f"{pct:g}% of {whole:g}"]
    target, factor = UNITS[task.unit_from]
    return round(numbers[0] * factor, 4), [f"1 {task.unit_from} = {factor:g} {target}", "scale the amount"]


def naive(task: Task) -> Attempt:
    """First two numbers, first operator seen. Fails on anything multi-step."""

    numbers = _numbers(task)
    if len(numbers) < 2:
        return Attempt(None, 1, ("no two numbers found",))
    if task.kind == SIMPLE:
        return Attempt(numbers[0] + numbers[1], 1, ("added the first two numbers",))
    if task.kind == COMPOUND:
        return Attempt(numbers[0] + numbers[1], 1, ("added the first two numbers only",))
    if task.kind == PERCENT:
        return Attempt(
            numbers[0] * numbers[1] / 100 if numbers[0] < 1 else numbers[0] + numbers[1],
            1,
            ("guessed at the percentage",),
        )
    return Attempt(None, 1, ("unit conversion not attempted",))


def router(task: Task) -> Attempt:
    """Pick the right specialist, then solve once."""

    answer, trace = _solve(task)
    return Attempt(answer, 1, ("route to specialist", *trace))


def chain(task: Task) -> Attempt:
    """Solve, but record every intermediate value as its own step."""

    answer, trace = _solve(task)
    steps = 1 + len(trace)
    return Attempt(answer, steps, ("decompose", *trace))


def self_check(task: Task) -> Attempt:
    """Answer, verify, and fall back to a different method on disagreement."""

    first = naive(task)
    verification, trace = _solve(task)
    trace_lines = ["attempt with the fast path", *trace, "verify the result independently"]
    if first.answer is not None and abs(first.answer - verification) <= 0.01:
        return Attempt(first.answer, 3, (*trace_lines, "verification agrees"))
    return Attempt(verification, 3 + 1, (*trace_lines, "verification disagrees → trust the check"))


def ensemble(task: Task) -> Attempt:
    """Three independent attempts, majority vote."""

    votes = [naive(task).answer, router(task).answer, chain(task).answer]
    counts: dict[float, int] = {}
    for vote in votes:
        if vote is None:
            continue
        counts[round(vote, 4)] = counts.get(round(vote, 4), 0) + 1
    if not counts:
        return Attempt(None, 3, ("no votes",))
    winner = max(counts, key=lambda value: counts[value])
    return Attempt(winner, 6, (*(f"vote: {vote}" for vote in votes), "majority wins"))


PATTERNS = {
    "naive": (naive, "one pass, first two numbers, first operator"),
    "router": (router, "classify the task, then call one specialist"),
    "chain": (chain, "explicit intermediate steps"),
    "self_check": (self_check, "answer, verify independently, correct on mismatch"),
    "ensemble": (ensemble, "three attempts, majority vote"),
}


def get_pattern(name: str):
    if name not in PATTERNS:
        raise KeyError(f"unknown pattern: {name}")
    return PATTERNS[name][0]


def describe_patterns() -> list[dict]:
    return [{"name": name, "description": description} for name, (_, description) in PATTERNS.items()]
