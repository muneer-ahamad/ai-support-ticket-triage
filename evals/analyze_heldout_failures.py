from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = ROOT / "evals" / "heldout_results_v1.json"


def main():
    report = json.loads(
        RESULTS_PATH.read_text(encoding="utf-8")
    )

    results = report["results"]

    queue_pairs = Counter()
    category_pairs = Counter()
    type_pairs = Counter()
    priority_pairs = Counter()

    print()
    print("=" * 90)
    print("V1 HELD-OUT FAILURE ANALYSIS")
    print("=" * 90)

    for row in results:
        if row.get("error"):
            continue

        expected = row["expected"]
        predicted = row["predicted"]
        correct = row["correct"]

        category_pairs[
            (expected["category"], predicted["category"])
        ] += 1

        queue_pairs[
            (expected["queue"], predicted["queue"])
        ] += 1

        type_pairs[
            (expected["ticket_type"], predicted["ticket_type"])
        ] += 1

        priority_pairs[
            (expected["priority"], predicted["priority"])
        ] += 1

        wrong_fields = [
            field
            for field in [
                "category",
                "queue",
                "ticket_type",
                "priority",
            ]
            if not correct[field]
        ]

        review_wrong = not correct["review"]

        if not wrong_fields and not review_wrong:
            continue

        print()
        print("-" * 90)
        print(f"TICKET {row['id']}: {row['subject']}")
        print("-" * 90)

        for field in wrong_fields:
            print(
                f"{field.upper():<12}"
                f" expected: {expected[field]}"
            )

            print(
                f"{'':<12}"
                f" predicted: {predicted[field]}"
            )

        if review_wrong:
            print(
                f"REVIEW       expected: "
                f"{expected['requires_review']}"
            )

            print(
                f"{'':<12}"
                f" predicted: "
                f"{predicted['requires_review']}"
            )

        print(
            f"Confidence: {row['confidence']}"
        )

    def print_pairs(title, pairs):
        print()
        print("=" * 90)
        print(title)
        print("=" * 90)

        for (expected, predicted), count in pairs.most_common():
            marker = "✓" if expected == predicted else "✗"

            print(
                f"{count:>3}  "
                f"{expected:<35} -> "
                f"{predicted:<35} {marker}"
            )

    print_pairs(
        "QUEUE CONFUSION",
        queue_pairs,
    )

    print_pairs(
        "CATEGORY CONFUSION",
        category_pairs,
    )

    print_pairs(
        "TYPE CONFUSION",
        type_pairs,
    )

    print_pairs(
        "PRIORITY CONFUSION",
        priority_pairs,
    )


if __name__ == "__main__":
    main()