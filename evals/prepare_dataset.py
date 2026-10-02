from pathlib import Path
import json

from datasets import load_dataset


DATASET_NAME = "Tobi-Bueck/customer-support-tickets"
SAMPLE_SIZE = 500
SEED = 42

OUTPUT_PATH = Path("data/evaluation/support_eval.jsonl")


def main():
    print("Downloading customer-support dataset...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
    )

    print(f"Total rows: {len(dataset):,}")
    print(f"Columns: {dataset.column_names}")

    # Keep English tickets only.
    def is_english(row):
        language = str(row.get("language", "")).strip().lower()
        return language in {"en", "english"}

    english = dataset.filter(is_english)

    print(f"English rows: {len(english):,}")

    # Remove records that don't contain the fields needed for evaluation.
    def valid_ticket(row):
        return all(
            [
                row.get("subject"),
                row.get("body"),
                row.get("queue"),
                row.get("priority"),
            ]
        )

    english = english.filter(valid_ticket)

    # Deterministic sample so every evaluation run uses the same tickets.
    sample_size = min(SAMPLE_SIZE, len(english))

    sample = (
        english
        .shuffle(seed=SEED)
        .select(range(sample_size))
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for row in sample:
            record = {
                "subject": row["subject"],
                "body": row["body"],
                "expected_queue": row["queue"],
                "expected_priority": row["priority"],
                "ticket_type": row.get("type"),
            }

            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print()
    print(f"Saved {len(sample)} evaluation tickets")
    print(f"Location: {OUTPUT_PATH}")
    print()

    print("Example:")
    print(json.dumps(sample[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()