"""Score the rule-based parser against a hand-labelled set of shopper queries.

Every field of ParsedQuery except `text` and `keywords` is checked. A field the
label leaves out must come back empty (None or []), so stray extra readings
count as errors too. Measurements may differ by up to 0.5 cm.

    python -m tests.eval.run_parser_eval          # summary
    python -m tests.eval.run_parser_eval -v       # list every failing query
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from app.search.rules import parse_query

FIELDS = ["category", "gender", "colors", "materials", "min_price", "max_price",
          "measurements", "size_label", "fit_preference", "tags"]
EMPTY = {"colors": [], "materials": [], "measurements": {}, "tags": []}
QUERIES = Path(__file__).with_name("queries.jsonl")


def _same(field, want, got):
    if field == "measurements":
        return set(want) == set(got) and all(abs(want[k] - got[k]) <= 0.5 for k in want)
    if field in ("colors", "materials", "tags"):
        return sorted(want) == sorted(got)
    return want == got


def evaluate(path: Path = QUERIES):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    field_errors, failures = Counter(), []
    for row in rows:
        got = parse_query(row["q"]).model_dump()
        wrong = []
        for f in FIELDS:
            want = row.get(f, EMPTY.get(f))
            if not _same(f, want, got[f]):
                field_errors[f] += 1
                wrong.append((f, want, got[f]))
        if wrong:
            failures.append((row["q"], wrong))
    return rows, field_errors, failures


def main():
    rows, field_errors, failures = evaluate()
    n = len(rows)
    print(f"Fully correct: {n - len(failures)}/{n} ({(n - len(failures)) / n:.0%})")
    print("Field accuracy:")
    for f in FIELDS:
        print(f"  {f:15s} {(n - field_errors[f]) / n:6.1%}")
    if "-v" in sys.argv:
        for q, wrong in failures:
            print(f"\n{q!r}")
            for f, want, got in wrong:
                print(f"    {f}: want {want!r}, got {got!r}")


if __name__ == "__main__":
    main()
