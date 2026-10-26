from __future__ import annotations

import json

from patternbench.bench import run_bench
from patternbench.cli import main
from patternbench.patterns import PATTERNS, chain, describe_patterns, ensemble, get_pattern, naive, router, self_check
from patternbench.task import generate, is_correct


def tasks() -> list:
    return generate(count=40, seed=7)


def accuracy(pattern, task_list) -> float:
    hits = sum(int(is_correct(pattern(task).answer, task)) for task in task_list)
    return hits / len(task_list)


def test_naive_is_weak_on_compound_tasks() -> None:
    compound = [task for task in tasks() if task.kind == "compound"]
    assert accuracy(naive, compound) == 0.0


def test_router_solves_everything() -> None:
    assert accuracy(router, tasks()) == 1.0


def test_chain_solves_everything_with_more_steps() -> None:
    sample = tasks()
    assert accuracy(chain, sample) == 1.0
    assert chain(sample[0]).steps > router(sample[0]).steps


def test_self_check_corrects_the_naive_path() -> None:
    sample = tasks()
    assert accuracy(self_check, sample) > accuracy(naive, sample)


def test_ensemble_votes_to_the_right_answer() -> None:
    compound = next(task for task in tasks() if task.kind == "compound")
    assert is_correct(ensemble(compound).answer, compound) is True


def test_unknown_pattern_raises() -> None:
    try:
        get_pattern("telepathy")
    except KeyError as exc:
        assert "telepathy" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")


def test_bench_report_leaderboard() -> None:
    report = run_bench(count=40, seed=7)
    board = report.leaderboard()
    assert len(board) == len(PATTERNS)
    assert board[0].accuracy >= board[-1].accuracy
    assert report.best() is board[0]
    names = [score.name for score in board]
    assert names[0] in {"router", "chain", "self_check", "ensemble"}
    assert names[-1] == "naive"


def test_bench_report_render_and_json() -> None:
    report = run_bench(count=20, seed=3)
    text = report.render()
    assert "PATTERN" in text
    assert "ranked by accuracy" in text
    payload = json.loads(json.dumps(report.as_dict()))
    assert payload["tasks"] == 20
    assert payload["leaderboard"]


def test_pattern_subset() -> None:
    report = run_bench(count=12, seed=1, patterns=["naive", "router"])
    assert [score.name for score in report.scores] == ["naive", "router"]


def test_describe_patterns() -> None:
    described = describe_patterns()
    assert {item["name"] for item in described} == set(PATTERNS)
    assert all(item["description"] for item in described)


def test_cli_run(capsys) -> None:
    assert main(["run", "--tasks", "16"]) == 0
    out = capsys.readouterr().out
    assert "PATTERN" in out
    assert "router" in out


def test_cli_run_json(capsys) -> None:
    assert main(["run", "--tasks", "8", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["leaderboard"][0]["accuracy"] >= payload["leaderboard"][-1]["accuracy"]


def test_cli_patterns(capsys) -> None:
    assert main(["patterns"]) == 0
    out = capsys.readouterr().out
    assert "self_check" in out
    assert "ensemble" in out


def test_cli_tasks(capsys) -> None:
    assert main(["tasks", "--count", "4"]) == 0
    assert "4 task(s)" in capsys.readouterr().out


def test_cli_check_shows_trace(capsys) -> None:
    assert main(["check", "T001", "--pattern", "chain"]) == 0
    out = capsys.readouterr().out
    assert "expected:" in out
    assert "decompose" in out


def test_cli_unknown_pattern_exits_two(capsys) -> None:
    assert main(["run", "--patterns", "telepathy"]) == 2
    assert "error" in capsys.readouterr().err
