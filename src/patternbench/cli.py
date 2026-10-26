"""Command-line interface for PatternBench."""

from __future__ import annotations

import argparse
import json
import sys

from patternbench import __version__
from patternbench.bench import run_bench
from patternbench.patterns import describe_patterns, get_pattern
from patternbench.task import generate, is_correct


def _run(args: argparse.Namespace) -> int:
    report = run_bench(count=args.tasks, seed=args.seed, patterns=args.patterns)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.render())
    return 0


def _patterns(args: argparse.Namespace) -> int:
    for item in describe_patterns():
        print(f"{item['name']:<12} {item['description']}")
    return 0


def _tasks(args: argparse.Namespace) -> int:
    tasks = generate(count=args.count, seed=args.seed)
    for task in tasks:
        print(f"{task.id}  {task.kind:<9} {task.prompt}")
    print(f"\n{len(tasks)} task(s), seed {args.seed}")
    return 0


def _check(args: argparse.Namespace) -> int:
    task = next((item for item in generate(count=200) if item.id == args.task), None)
    if task is None:
        print(f"unknown task id: {args.task}", file=sys.stderr)
        return 2
    attempt = get_pattern(args.pattern)(task)
    correct = is_correct(attempt.answer, task)
    print(f"task    : {task.prompt}")
    print(f"expected: {task.answer:g}")
    print(f"pattern : {args.pattern} → {attempt.answer if attempt.answer is not None else 'no answer'}")
    print(f"correct : {correct}")
    for line in attempt.trace:
        print(f"  · {line}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patternbench",
        description="Benchmark agentic patterns on a deterministic task set — no model required.",
    )
    parser.add_argument("--version", action="version", version=f"patternbench {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the leaderboard")
    run.add_argument("--tasks", type=int, default=40)
    run.add_argument("--seed", type=int, default=7)
    run.add_argument("--patterns", nargs="*", help="subset of patterns to run")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=_run)

    patterns = sub.add_parser("patterns", help="list the available patterns")
    patterns.set_defaults(func=_patterns)

    tasks = sub.add_parser("tasks", help="print generated tasks")
    tasks.add_argument("--count", type=int, default=8)
    tasks.add_argument("--seed", type=int, default=7)
    tasks.set_defaults(func=_tasks)

    check = sub.add_parser("check", help="run one pattern on one task and show the trace")
    check.add_argument("task")
    check.add_argument("--pattern", default="router")
    check.set_defaults(func=_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
