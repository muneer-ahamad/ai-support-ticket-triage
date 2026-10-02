from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "evaluation" / "support_dev.jsonl"
OUTPUT = ROOT / "data" / "evaluation" / "gold_labels.csv"

SAMPLE_SIZE = 50


def main():
    rows = []

    with SOURCE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    rows = rows[:SAMPLE_SIZE]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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
        "gold_route",
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

        for index, row in enumerate(rows, start=1):

            writer.writerow(
                {
                    "id": index,
                    "subject": row["subject"],
                    "body": row["body"],
                    "original_queue": row["expected_queue"],
                    "original_type": row["ticket_type"],
                    "original_priority": row["expected_priority"],
                    "gold_category": "",
                    "gold_queue": "",
                    "gold_type": "",
                    "gold_priority": "",
                    "gold_route": "",
                    "requires_human_review": "",
                    "notes": "",
                }
            )

    print(f"Created {SAMPLE_SIZE}-ticket gold-set template")
    print(f"Location: {OUTPUT}")


if __name__ == "__main__":
    main()