# PatternBench

**Five agentic patterns, one deterministic task set, one honest leaderboard — and no model in the loop.**

"Use reflection", "use an ensemble", "use a router" are recommendations without
numbers. PatternBench makes the trade-off measurable: every pattern solves the same
seeded tasks, and the leaderboard ranks accuracy first, then the number of reasoning
steps it cost. Because the solvers are plain Python, the result is reproducible and
runs in milliseconds.

[![CI](https://github.com/abubakarsiddique360/PatternBench/actions/workflows/ci.yml/badge.svg)](https://github.com/abubakarsiddique360/PatternBench/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.12-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](pyproject.toml)

## Quick start

```bash
git clone https://github.com/abubakarsiddique360/PatternBench.git
cd PatternBench
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

patternbench run --tasks 40
patternbench check T001 --pattern chain
patternbench patterns
```

```
PATTERN     ACCURACY       STEPS  TOKENS  MS
--------------------------------------------
router      1.000 (40/40)  1.00   10      0
chain       1.000 (40/40)  2.75   8       0
self_check  1.000 (40/40)  3.75   28      0
ensemble    1.000 (40/40)  6.00   11      0
naive       0.250 (10/40)  1.00   6       0

40 task(s), seed 7 · ranked by accuracy, then by fewest steps
```

## The patterns

| Pattern | Idea | What it costs |
| --- | --- | --- |
| `naive` | one pass: take the first two numbers and the first operator | cheapest, fails anything multi-step (10/40) |
| `router` | classify the task, then call exactly one specialist | best accuracy per step |
| `chain` | same solver, but every intermediate value is an explicit step | same accuracy, more steps, more trace |
| `self_check` | answer with the fast path, verify independently, correct on mismatch | recovers naive's errors, ~4× the steps |
| `ensemble` | three attempts, majority vote | robust, most expensive |

The ranking is the point: `router` wins on cost-adjusted accuracy here, while
`self_check` and `ensemble` buy the same accuracy with more work. On tasks where the
router is unsure, that ordering would flip — which is exactly the experiment this
harness exists to run.

## The task set

Four kinds, generated from a seed so two runs are comparable:

| Kind | Example | Answer |
| --- | --- | --- |
| `simple` | What is 37 + 58? | 95 |
| `compound` | Start with 12, add 7, then multiply by 3 | 57 |
| `percent` | What is 15% of 240? | 36 |
| `unit` | Convert 3.5 km to m | 3500 |

`patternbench tasks --count 12 --seed 3` prints them; the generator is a pure
function of `(count, seed)`.

## Design rules

- **Deterministic.** No model, no network, no clock-dependent scoring. Same seed,
  same leaderboard.
- **Cost-aware.** Accuracy alone rewards brute force, so steps are the tie-breaker
  and token-proxy (characters ÷ 4) is reported for every pattern.
- **Explainable.** Every attempt carries a trace; `patternbench check T001 --pattern
  self_check` shows exactly why the correction happened.
- **Honest limits.** These solvers are hand-written, so the benchmark measures the
  *patterns*, not any particular LLM.

## CLI

| Command | Purpose |
| --- | --- |
| `run [--tasks N] [--seed S] [--patterns ...] [--json]` | Leaderboard |
| `check TASK_ID [--pattern NAME]` | One task, one pattern, full trace |
| `tasks [--count N] [--seed S]` | Print the generated tasks |
| `patterns` | List the patterns |

## Project layout

```text
src/patternbench/
├── task.py      seeded task generator + scoring tolerance
├── patterns.py  five pattern implementations with traces
├── bench.py     accuracy, steps, tokens, leaderboard
└── cli.py       run · check · tasks · patterns
tests/           23 pytest cases
```

## Limitations

- The task set is arithmetic and unit conversion. It is a harness demo, not a
  benchmark of general reasoning.
- Patterns are implemented as plain functions; the "steps" metric is the number of
  recorded reasoning steps, not real token usage.
- A router needs a task taxonomy. Here the prompts are unambiguous; real traffic is
  not, and misrouting is the failure mode this benchmark cannot show.

## License

[MIT](LICENSE) © 2026 **ABU BAKAR SIDDIQUE**
