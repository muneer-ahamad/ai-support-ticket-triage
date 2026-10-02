from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm import GeminiClient
from app.nodes.classify import classify_node


GOLD_PATH = ROOT / "data" / "evaluation" / "gold_labels.csv"
RESULTS_JSON = ROOT / "evals" / "gold_results.json"
RESULTS_MD = ROOT / "evals" / "gold_results.md"


def percentage(correct: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round((correct / total) * 100, 2)


def load_gold_rows(limit: int) -> list[dict]:
    if not GOLD_PATH.exists():
        raise FileNotFoundError(
            f"{GOLD_PATH} was not found."
        )

    rows = []

    with GOLD_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            # Only evaluate rows that you actually labelled.
            required = [
                "gold_category",
                "gold_queue",
                "gold_type",
                "gold_priority",
            ]

            if not all(
                str(row.get(field, "")).strip()
                for field in required
            ):
                continue

            rows.append(row)

    return rows[:limit]


def run_with_retry(
    llm: GeminiClient,
    state: dict,
    max_attempts: int = 4,
):
    for attempt in range(1, max_attempts + 1):

        try:
            return classify_node(state, llm)

        except Exception as exc:
            message = str(exc)
            upper = message.upper()

            transient = any(
                marker in upper
                for marker in [
                    "429",
                    "503",
                    "UNAVAILABLE",
                    "RESOURCE_EXHAUSTED",
                    "RATE LIMIT",
                    "HIGH DEMAND",
                ]
            )

            if not transient or attempt == max_attempts:
                raise

            if (
                "429" in upper
                or "RESOURCE_EXHAUSTED" in upper
            ):
                wait_seconds = 60
            else:
                wait_seconds = 2 ** attempt

            print(
                f"    Temporary Gemini error. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Gemini against curated ticket labels."
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay between Gemini requests.",
    )

    args = parser.parse_args()

    rows = load_gold_rows(args.samples)

    if not rows:
        raise ValueError(
            "No completed gold labels were found."
        )

    print()
    print("=" * 65)
    print("CURATED POLICY EVALUATION")
    print("=" * 65)
    print(f"Tickets: {len(rows)}")
    print()

    llm = GeminiClient()

    category_correct = 0
    queue_correct = 0
    type_correct = 0
    priority_correct = 0
    all_correct = 0
    successful = 0

    confidences = []
    latencies = []
    results = []

    for index, row in enumerate(rows, start=1):

        print(
            f"[{index}/{len(rows)}] "
            f"{row['subject'][:60]}"
        )

        state = {
            "subject": row["subject"],
            "body": row["body"],
        }

        started = time.perf_counter()

        try:
            prediction = run_with_retry(
                llm,
                state,
            )

            latency = time.perf_counter() - started

            predicted_category = prediction["category"]
            predicted_queue = prediction["queue"]
            predicted_type = prediction["ticket_type"]
            predicted_priority = prediction["priority"]

            confidence = float(
                prediction["classification_confidence"]
            )

            expected_category = row["gold_category"].strip()
            expected_queue = row["gold_queue"].strip()
            expected_type = row["gold_type"].strip()
            expected_priority = row["gold_priority"].strip()

            category_ok = (
                predicted_category == expected_category
            )

            queue_ok = (
                predicted_queue == expected_queue
            )

            type_ok = (
                predicted_type == expected_type
            )

            priority_ok = (
                predicted_priority == expected_priority
            )

            complete_ok = all(
                [
                    category_ok,
                    queue_ok,
                    type_ok,
                    priority_ok,
                ]
            )

            category_correct += int(category_ok)
            queue_correct += int(queue_ok)
            type_correct += int(type_ok)
            priority_correct += int(priority_ok)
            all_correct += int(complete_ok)

            successful += 1

            confidences.append(confidence)
            latencies.append(latency)

            print(
                f"    Category: "
                f"{predicted_category:<18} "
                f"{'✓' if category_ok else '✗'} "
                f"(expected {expected_category})"
            )

            print(
                f"    Queue:    "
                f"{predicted_queue:<30} "
                f"{'✓' if queue_ok else '✗'}"
            )

            if not queue_ok:
                print(
                    f"              expected "
                    f"{expected_queue}"
                )

            print(
                f"    Type:     "
                f"{predicted_type:<18} "
                f"{'✓' if type_ok else '✗'} "
                f"(expected {expected_type})"
            )

            print(
                f"    Priority: "
                f"{predicted_priority:<18} "
                f"{'✓' if priority_ok else '✗'} "
                f"(expected {expected_priority})"
            )

            print(
                f"    Confidence: {confidence:.2f} | "
                f"Latency: {latency:.2f}s"
            )

            results.append(
                {
                    "id": row["id"],
                    "subject": row["subject"],
                    "expected": {
                        "category": expected_category,
                        "queue": expected_queue,
                        "ticket_type": expected_type,
                        "priority": expected_priority,
                    },
                    "predicted": {
                        "category": predicted_category,
                        "queue": predicted_queue,
                        "ticket_type": predicted_type,
                        "priority": predicted_priority,
                    },
                    "correct": {
                        "category": category_ok,
                        "queue": queue_ok,
                        "ticket_type": type_ok,
                        "priority": priority_ok,
                        "all_fields": complete_ok,
                    },
                    "confidence": confidence,
                    "latency_seconds": round(
                        latency,
                        3,
                    ),
                    "error": None,
                }
            )

        except Exception as exc:

            latency = time.perf_counter() - started

            print(f"    ERROR: {exc}")

            results.append(
                {
                    "id": row["id"],
                    "subject": row["subject"],
                    "error": str(exc),
                    "latency_seconds": round(
                        latency,
                        3,
                    ),
                }
            )

        print()

        if index < len(rows):
            time.sleep(args.delay)

    total = len(rows)

    summary = {
        "tickets_requested": total,
        "successful_predictions": successful,
        "failed_predictions": total - successful,
        "structured_output_success_pct": percentage(
            successful,
            total,
        ),
        "category_accuracy_pct": percentage(
            category_correct,
            successful,
        ),
        "queue_accuracy_pct": percentage(
            queue_correct,
            successful,
        ),
        "ticket_type_accuracy_pct": percentage(
            type_correct,
            successful,
        ),
        "priority_accuracy_pct": percentage(
            priority_correct,
            successful,
        ),
        "all_fields_correct_pct": percentage(
            all_correct,
            successful,
        ),
        "average_confidence": (
            round(mean(confidences), 4)
            if confidences
            else None
        ),
        "average_latency_seconds": (
            round(mean(latencies), 3)
            if latencies
            else None
        ),
    }

    RESULTS_JSON.write_text(
        json.dumps(
            {
                "summary": summary,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    markdown = f"""# Curated Policy Evaluation

This evaluation compares the classifier against manually curated
labels following the project's documented routing and severity policy.

## Results

| Metric | Result |
|---|---:|
| Tickets evaluated | {total} |
| Successful predictions | {successful}/{total} |
| Structured-output success | {summary["structured_output_success_pct"]}% |
| Category accuracy | {summary["category_accuracy_pct"]}% |
| Queue accuracy | {summary["queue_accuracy_pct"]}% |
| Ticket-type accuracy | {summary["ticket_type_accuracy_pct"]}% |
| Priority accuracy | {summary["priority_accuracy_pct"]}% |
| All four fields correct | {summary["all_fields_correct_pct"]}% |
| Average confidence | {summary["average_confidence"]} |
| Average latency | {summary["average_latency_seconds"]} s |

## Methodology

These results are from a development policy set and should not be
treated as final held-out benchmark results.
"""

    RESULTS_MD.write_text(
        markdown,
        encoding="utf-8",
    )

    print()
    print("=" * 65)
    print("FINAL RESULTS")
    print("=" * 65)

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print()
    print(f"JSON results: {RESULTS_JSON}")
    print(f"Markdown:     {RESULTS_MD}")


if __name__ == "__main__":
    main()