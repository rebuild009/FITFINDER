"""Guard the parser's accuracy on the hand-labelled query sets in tests/eval/."""

from pathlib import Path

from tests.eval.run_parser_eval import evaluate

EVAL = Path(__file__).parent / "eval"


def _accuracy(name):
    rows, _, failures = evaluate(EVAL / name)
    return (len(rows) - len(failures)) / len(rows), failures


def test_tuning_set_fully_correct():
    acc, failures = _accuracy("queries.jsonl")
    assert acc == 1.0, failures


def test_holdout_set_stays_above_95_percent():
    acc, failures = _accuracy("holdout.jsonl")
    assert acc >= 0.95, failures
