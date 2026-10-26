from __future__ import annotations

import pytest

from patternbench.task import KINDS, UNITS, generate, is_correct, parse_prediction


def test_generation_is_deterministic() -> None:
    assert [task.prompt for task in generate(12, seed=3)] == [task.prompt for task in generate(12, seed=3)]


def test_different_seeds_differ() -> None:
    assert [task.prompt for task in generate(8, seed=1)] != [task.prompt for task in generate(8, seed=2)]


def test_all_kinds_are_used() -> None:
    tasks = generate(12, seed=5)
    assert {task.kind for task in tasks} == set(KINDS)


def test_answers_are_correct_for_known_examples() -> None:
    tasks = {task.kind: task for task in generate(8, seed=11)}
    simple = tasks["simple"]
    assert simple.answer == simple.numbers[0] + simple.numbers[1]
    compound = tasks["compound"]
    assert compound.answer == (compound.numbers[0] + compound.numbers[1]) * compound.numbers[2]
    percent = tasks["percent"]
    assert percent.answer == pytest.approx(percent.numbers[0] / 100 * percent.numbers[1])
    unit = tasks["unit"]
    assert unit.answer == pytest.approx(unit.numbers[0] * UNITS[unit.unit_from][1])


def test_parse_prediction_formats() -> None:
    assert parse_prediction("1,234.5") == 1234.5
    assert parse_prediction(7) == 7.0
    assert parse_prediction("not a number") is None


def test_is_correct_tolerance() -> None:
    task = generate(1, seed=1)[0]
    assert is_correct(task.answer, task) is True
    assert is_correct(task.answer + 1, task) is False
    assert is_correct(None, task) is False


def test_task_ids_are_unique() -> None:
    tasks = generate(20)
    assert len({task.id for task in tasks}) == 20
