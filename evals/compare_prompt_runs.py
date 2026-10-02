from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASELINE_PATH = ROOT / "evals" / "gold_results_baseline.json"
CURRENT_PATH = ROOT / "evals" / "gold_results.json"

FIELDS = [
    "category",
    "queue",
    "ticket_type",
    "priority",
]


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found."
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def mark(value: bool) -> str:
    return "✓" if value else "✗"


def main():
    baseline = load(BASELINE_PATH)
    current = load(CURRENT_PATH)

    baseline_results = {
        str(row["id"]): row
        for row in baseline["results"]
        if not row.get("error")
    }

    current_results = {
        str(row["id"]): row
        for row in current["results"]
        if not row.get("error")
    }

    improved = []
    regressed = []
    unchanged_correct = []
    unchanged_wrong = []

    print()
    print("=" * 85)
    print("BASELINE VS TUNED PROMPT")
    print("=" * 85)

    for ticket_id, old in baseline_results.items():

        new = current_results.get(ticket_id)

        if not new:
            continue

        print()
        print("-" * 85)
        print(
            f"TICKET {ticket_id}: "
            f"{old['subject']}"
        )
        print("-" * 85)

        for field in FIELDS:

            old_correct = old["correct"][field]
            new_correct = new["correct"][field]

            expected = old["expected"][field]
            old_pred = old["predicted"][field]
            new_pred = new["predicted"][field]

            if not old_correct and new_correct:
                status = "IMPROVED"
                improved.append(
                    (ticket_id, field)
                )

            elif old_correct and not new_correct:
                status = "REGRESSED"
                regressed.append(
                    (ticket_id, field)
                )

            elif old_correct and new_correct:
                status = "STILL CORRECT"
                unchanged_correct.append(
                    (ticket_id, field)
                )

            else:
                status = "STILL WRONG"
                unchanged_wrong.append(
                    (ticket_id, field)
                )

            if (
                old_pred != new_pred
                or old_correct != new_correct
            ):
                print()
                print(f"{field.upper()}")
                print(f"  Expected : {expected}")
                print(
                    f"  Baseline : {old_pred} "
                    f"{mark(old_correct)}"
                )
                print(
                    f"  Tuned    : {new_pred} "
                    f"{mark(new_correct)}"
                )
                print(f"  Result   : {status}")

    print()
    print("=" * 85)
    print("SUMMARY")
    print("=" * 85)

    print(
        f"Improved field predictions: "
        f"{len(improved)}"
    )

    print(
        f"Regressed field predictions: "
        f"{len(regressed)}"
    )

    print(
        f"Still correct: "
        f"{len(unchanged_correct)}"
    )

    print(
        f"Still wrong: "
        f"{len(unchanged_wrong)}"
    )

    print()

    if improved:
        print("IMPROVEMENTS")
        for ticket_id, field in improved:
            print(
                f"  Ticket {ticket_id}: {field}"
            )

    print()

    if regressed:
        print("REGRESSIONS")
        for ticket_id, field in regressed:
            print(
                f"  Ticket {ticket_id}: {field}"
            )


if __name__ == "__main__":
    main()