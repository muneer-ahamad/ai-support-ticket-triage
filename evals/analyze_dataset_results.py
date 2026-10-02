from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "evals" / "dataset_results.json"


def print_confusions(title: str, counter: Counter):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    for (expected, predicted), count in counter.most_common():
        marker = "✓" if expected == predicted else "✗"

        print(
            f"{count:>3}  "
            f"{str(expected):<35} -> "
            f"{str(predicted):<35} {marker}"
        )


def main():
    report = json.loads(
        RESULTS_PATH.read_text(encoding="utf-8")
    )

    results = report["results"]

    queue_pairs = Counter()
    type_pairs = Counter()
    priority_pairs = Counter()

    successful = 0

    print()
    print("=" * 80)
    print("INDIVIDUAL PREDICTIONS")
    print("=" * 80)

    for index, row in enumerate(results, start=1):

        if row.get("error"):
            print()
            print(f"{index:>2}. {row['subject']}")
            print("    ERROR")
            continue

        successful += 1

        queue_pairs[
            (row["expected_queue"], row["predicted_queue"])
        ] += 1

        type_pairs[
            (row["expected_type"], row["predicted_type"])
        ] += 1

        priority_pairs[
            (
                row["expected_priority"],
                row["predicted_priority"],
            )
        ] += 1

        print()
        print(f"{index:>2}. {row['subject']}")

        print(
            f"    Queue:    "
            f"{row['expected_queue']} -> "
            f"{row['predicted_queue']}"
        )

        print(
            f"    Type:     "
            f"{row['expected_type']} -> "
            f"{row['predicted_type']}"
        )

        print(
            f"    Priority: "
            f"{row['expected_priority']} -> "
            f"{row['predicted_priority']}"
        )

        print(
            f"    Category: {row['predicted_category']}"
        )

        print(
            f"    Confidence: {row['confidence']}"
        )

    print_confusions(
        "QUEUE CONFUSION PAIRS",
        queue_pairs,
    )

    print_confusions(
        "TICKET TYPE CONFUSION PAIRS",
        type_pairs,
    )

    print_confusions(
        "PRIORITY CONFUSION PAIRS",
        priority_pairs,
    )

    # Additional priority metric:
    # The benchmark has no "urgent" class.
    # Treat high -> urgent as an escalation rather than exact agreement.
    strict_priority_correct = 0
    escalation_aware_correct = 0

    for row in results:
        if row.get("error"):
            continue

        expected = row["expected_priority"]
        predicted = row["predicted_priority"]

        if expected == predicted:
            strict_priority_correct += 1
            escalation_aware_correct += 1

        elif expected == "high" and predicted == "urgent":
            escalation_aware_correct += 1

    def percent(value: int) -> float:
        if successful == 0:
            return 0.0

        return round(
            value / successful * 100,
            2,
        )

    print()
    print("=" * 80)
    print("PRIORITY POLICY COMPARISON")
    print("=" * 80)

    print(
        f"Strict priority agreement:      "
        f"{percent(strict_priority_correct)}%"
    )

    print(
        f"Escalation-aware agreement:     "
        f"{percent(escalation_aware_correct)}%"
    )

    print()
    print(
        "Escalation-aware agreement only treats "
        "dataset HIGH -> application URGENT as acceptable."
    )

    print(
        "The strict metric remains the primary benchmark metric."
    )


if __name__ == "__main__":
    main()