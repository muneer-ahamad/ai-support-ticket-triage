from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = ROOT / "data" / "evaluation" / "support_eval.jsonl"
RESULTS_PATH = ROOT / "evals" / "dataset_results.json"


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(DATASET_PATH)

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"{RESULTS_PATH} not found. Run the dataset evaluator first."
        )

    dataset = load_jsonl(DATASET_PATH)

    report = json.loads(
        RESULTS_PATH.read_text(encoding="utf-8")
    )

    results = report["results"]

    print()
    print("=" * 80)
    print("FAILURE ANALYSIS")
    print("=" * 80)

    failures = 0

    for index, result in enumerate(results, start=1):
        if result.get("error"):
            print()
            print(f"[{index}] API / STRUCTURED OUTPUT FAILURE")
            print(result["error"])
            continue

        queue_wrong = not result["queue_correct"]
        type_wrong = not result["type_correct"]
        priority_wrong = not result["priority_correct"]

        if not (queue_wrong or type_wrong or priority_wrong):
            continue

        failures += 1

        # The evaluator uses the first N rows,
        # so this corresponding dataset row is safe here.
        source = dataset[index - 1]

        print()
        print("-" * 80)
        print(f"TICKET {index}")
        print("-" * 80)

        print(f"SUBJECT:")
        print(source["subject"])

        print()
        print("BODY:")
        print(source["body"])

        print()
        print("QUEUE")
        print(f"  Expected : {result['expected_queue']}")
        print(f"  Predicted: {result['predicted_queue']}")

        print()
        print("TYPE")
        print(f"  Expected : {result['expected_type']}")
        print(f"  Predicted: {result['predicted_type']}")

        print()
        print("PRIORITY")
        print(f"  Expected : {result['expected_priority']}")
        print(f"  Predicted: {result['predicted_priority']}")

        print()
        print(f"Internal category: {result['predicted_category']}")
        print(f"Confidence:        {result['confidence']}")

    print()
    print("=" * 80)
    print(f"Tickets with at least one mismatch: {failures}/{len(results)}")
    print("=" * 80)


if __name__ == "__main__":
    main()