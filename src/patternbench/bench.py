"""Run every pattern over the task set and build a leaderboard."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from patternbench.patterns import PATTERNS, get_pattern
from patternbench.task import Task, generate, is_correct


@dataclass(frozen=True)
class PatternScore:
    name: str
    correct: int
    total: int
    avg_steps: float
    avg_tokens: float
    duration_ms: int

    @property
    def accuracy(self) -> float:
        return round(self.correct / self.total, 3) if self.total else 0.0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "correct": self.correct,
            "total": self.total,
            "accuracy": self.accuracy,
            "avg_steps": round(self.avg_steps, 2),
            "avg_tokens": round(self.avg_tokens, 1),
            "duration_ms": self.duration_ms,
        }


@dataclass
class BenchReport:
    task_count: int
    seed: int
    scores: list[PatternScore] = field(default_factory=list)

    def leaderboard(self) -> list[PatternScore]:
        return sorted(self.scores, key=lambda score: (-score.accuracy, score.avg_steps))

    def best(self) -> PatternScore | None:
        board = self.leaderboard()
        return board[0] if board else None

    def as_dict(self) -> dict:
        return {
            "tasks": self.task_count,
            "seed": self.seed,
            "leaderboard": [score.as_dict() for score in self.leaderboard()],
        }

    def render(self) -> str:
        rows = [("PATTERN", "ACCURACY", "STEPS", "TOKENS", "MS")]
        for score in self.leaderboard():
            rows.append(
                (
                    score.name,
                    f"{score.accuracy:.3f} ({score.correct}/{score.total})",
                    f"{score.avg_steps:.2f}",
                    f"{score.avg_tokens:.0f}",
                    str(score.duration_ms),
                )
            )
        widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
        lines = ["  ".join(cell.ljust(widths[index]) for index, cell in enumerate(rows[0]))]
        lines.append("-" * (sum(widths) + 8))
        for row in rows[1:]:
            lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
        lines.append("")
        lines.append(f"{self.task_count} task(s), seed {self.seed} · ranked by accuracy, then by fewest steps")
        return "\n".join(lines)


def run_bench(
    tasks: list[Task] | None = None,
    patterns: list[str] | None = None,
    count: int = 40,
    seed: int = 7,
) -> BenchReport:
    tasks = tasks if tasks is not None else generate(count=count, seed=seed)
    names = patterns or list(PATTERNS)
    report = BenchReport(task_count=len(tasks), seed=seed)
    for name in names:
        pattern = get_pattern(name)
        started = time.perf_counter()
        correct = 0
        steps = 0
        tokens = 0
        for task in tasks:
            attempt = pattern(task)
            correct += int(is_correct(attempt.answer, task))
            steps += attempt.steps
            tokens += attempt.tokens
        duration = int((time.perf_counter() - started) * 1000)
        report.scores.append(
            PatternScore(
                name=name,
                correct=correct,
                total=len(tasks),
                avg_steps=steps / len(tasks) if tasks else 0.0,
                avg_tokens=tokens / len(tasks) if tasks else 0.0,
                duration_ms=duration,
            )
        )
    return report
