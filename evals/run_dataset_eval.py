from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm import GeminiClient
from app.nodes.classify import classify_node


DATASET_PATHS = {
    "dev": ROOT / "data" / "evaluation" / "support_dev.jsonl",
    "test": ROOT / "data" / "evaluation" / "support_test.jsonl",
}
RESULTS_JSON = ROOT / "evals" / "dataset_results.json"
RESULTS_MD = ROOT / "evals" / "dataset_results.md"


def pct(correct: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((correct / total) * 100, 2)


def load_dataset(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist.\n"
            "Run: python evals/prepare_dataset.py"
        )

    rows = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))

    return rows[: min(limit, len(rows))]


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

            transient = any(
                marker in message.upper()
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

            if "429" in message or "RESOURCE_EXHAUSTED" in message.upper():
    		wait_seconds = 60
	    else:
   	        wait_seconds = 2 ** attempt

            print(
                f"  Temporary Gemini error. "
                f"Retrying in {wait_seconds}s "
                f"({attempt}/{max_attempts})..."
            )

            time.sleep(wait_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate ticket classifier on public support dataset."
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=25,
        help="Number of tickets to evaluate.",
    )

    parser.add_argument(
        "--split",
        choices=["dev", "test"],
        default="dev",
        help="Evaluation split to use.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait between API requests.",
    )

    args = parser.parse_args()

    dataset_path = DATASET_PATHS[args.split]
    rows = load_dataset(dataset_path, args.samples)

    print()
    print("=" * 60)
    print("AI SUPPORT TICKET DATASET EVALUATION")
    print("=" * 60)
    print(f"Tickets: {len(rows)}")
    print(f"Split:   {args.split}")
    print()

    llm = GeminiClient()

    queue_correct = 0
    type_correct = 0
    priority_correct = 0
    successful = 0

    confidences: list[float] = []
    latencies: list[float] = []

    queue_confusion = Counter()
    type_confusion = Counter()
    priority_confusion = Counter()

    results = []

    for index, row in enumerate(rows, start=1):
        subject = row["subject"]
        body = row["body"]

        expected_queue = row["expected_queue"]
        expected_priority = row["expected_priority"]
        expected_type = row.get("ticket_type")

        print(
            f"[{index}/{len(rows)}] "
            f"{subject[:55]}"
        )

        state = {
            "subject": subject,
            "body": body,
        }

        started = time.perf_counter()

        try:
            prediction = run_with_retry(llm, state)

            latency = time.perf_counter() - started
            latencies.append(latency)

            predicted_queue = prediction["queue"]
            predicted_type = prediction["ticket_type"]
            predicted_priority = prediction["priority"]
            predicted_category = prediction["category"]
            confidence = prediction["classification_confidence"]

            successful += 1
            confidences.append(confidence)

            queue_ok = predicted_queue == expected_queue
            type_ok = predicted_type == expected_type
            priority_ok = predicted_priority == expected_priority

            queue_correct += int(queue_ok)
            type_correct += int(type_ok)
            priority_correct += int(priority_ok)

            queue_confusion[
                (expected_queue, predicted_queue)
            ] += 1

            type_confusion[
                (expected_type, predicted_type)
            ] += 1

            priority_confusion[
                (expected_priority, predicted_priority)
            ] += 1

            print(
                f"    Queue:    {predicted_queue} "
                f"{'✓' if queue_ok else '✗'}"
            )

            print(
                f"    Type:     {predicted_type} "
                f"{'✓' if type_ok else '✗'}"
            )

            print(
                f"    Priority: {predicted_priority} "
                f"{'✓' if priority_ok else '✗'}"
            )

            print(
                f"    Category: {predicted_category}"
            )

            print(
                f"    Confidence: {confidence:.2f} | "
                f"Latency: {latency:.2f}s"
            )

            results.append(
                {
                    "subject": subject,
                    "expected_queue": expected_queue,
                    "predicted_queue": predicted_queue,
                    "queue_correct": queue_ok,
                    "expected_type": expected_type,
                    "predicted_type": predicted_type,
                    "type_correct": type_ok,
                    "expected_priority": expected_priority,
                    "predicted_priority": predicted_priority,
                    "priority_correct": priority_ok,
                    "predicted_category": predicted_category,
                    "confidence": confidence,
                    "latency_seconds": round(latency, 3),
                    "error": None,
                }
            )

        except Exception as exc:
            latency = time.perf_counter() - started

            print(f"    ERROR: {exc}")

            results.append(
                {
                    "subject": subject,
                    "expected_queue": expected_queue,
                    "expected_type": expected_type,
                    "expected_priority": expected_priority,
                    "error": str(exc),
                    "latency_seconds": round(latency, 3),
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
        "structured_output_success_pct": pct(successful, total),
        "queue_accuracy_pct": pct(queue_correct, successful),
        "ticket_type_accuracy_pct": pct(type_correct, successful),
        "priority_accuracy_pct": pct(priority_correct, successful),
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

    markdown = [
        "# Public Dataset Evaluation",
        "",
        "Generated with:",
        "",
        "```bash",
        f"python evals/run_dataset_eval.py --samples {total}",
        "```",
        "",
        "## Results",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Tickets evaluated | {total} |",
        f"| Successful structured outputs | {successful}/{total} |",
        (
            f"| Structured-output success | "
            f"{summary['structured_output_success_pct']}% |"
        ),
        f"| Queue accuracy | {summary['queue_accuracy_pct']}% |",
        (
            f"| Ticket-type accuracy | "
            f"{summary['ticket_type_accuracy_pct']}% |"
        ),
        (
            f"| Priority accuracy | "
            f"{summary['priority_accuracy_pct']}% |"
        ),
        (
            f"| Average confidence | "
            f"{summary['average_confidence']} |"
        ),
        (
            f"| Average latency | "
            f"{summary['average_latency_seconds']} s |"
        ),
        "",
        "## Notes",
        "",
        (
            "- The public dataset supplies queue, ticket type, "
            "and priority labels."
        ),
        (
            "- Internal issue category is predicted by the application "
            "but is not scored because the dataset does not provide "
            "the same category taxonomy."
        ),
        (
            "- Failed API/structured-output requests are counted in "
            "structured-output success rate."
        ),
        (
            "- Accuracy metrics are calculated only over successful "
            "predictions."
        ),
    ]

    RESULTS_MD.write_text(
        "\n".join(markdown) + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print()
    print(f"Detailed results: {RESULTS_JSON}")
    print(f"Markdown report:  {RESULTS_MD}")


if __name__ == "__main__":
    main()