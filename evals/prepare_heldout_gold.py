from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = (
    ROOT
    / "data"
    / "evaluation"
    / "support_test.jsonl"
)

OUTPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "heldout_gold.csv"
)

SAMPLE_SIZE = 20


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"{SOURCE} not found."
        )

    rows = []

    with SOURCE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            if line.strip():
                rows.append(
                    json.loads(line)
                )

    rows = rows[:SAMPLE_SIZE]

    fieldnames = [
        "id",
        "subject",
        "body",
        "original_queue",
        "original_type",
        "original_priority",
        "gold_category",
        "gold_queue",
        "gold_type",
        "gold_priority",
        "requires_human_review",
        "notes",
    ]

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for index, row in enumerate(
            rows,
            start=1,
        ):
            writer.writerow(
                {
                    "id": index,
                    "subject": row["subject"],
                    "body": row["body"],
                    "original_queue": row[
                        "expected_queue"
                    ],
                    "original_type": row[
                        "ticket_type"
                    ],
                    "original_priority": row[
                        "expected_priority"
                    ],
                    "gold_category": "",
                    "gold_queue": "",
                    "gold_type": "",
                    "gold_priority": "",
                    "requires_human_review": "",
                    "notes": "",
                }
            )

    print(
        f"Created held-out set "
        f"with {len(rows)} tickets"
    )

    print(
        f"Location: {OUTPUT}"
    )


if __name__ == "__main__":
    main()