from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "evaluation" / "support_eval.jsonl"
DEV = ROOT / "data" / "evaluation" / "support_dev.jsonl"
TEST = ROOT / "data" / "evaluation" / "support_test.jsonl"


def main():
    lines = [
        line
        for line in SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if len(lines) < 500:
        raise ValueError(
            f"Expected 500 tickets, found {len(lines)}"
        )

    dev = lines[:100]
    test = lines[100:500]

    DEV.write_text(
        "\n".join(dev) + "\n",
        encoding="utf-8",
    )

    TEST.write_text(
        "\n".join(test) + "\n",
        encoding="utf-8",
    )

    print(f"Development set: {len(dev)} tickets")
    print(f"Test set:        {len(test)} tickets")
    print()
    print(f"Saved: {DEV}")
    print(f"Saved: {TEST}")


if __name__ == "__main__":
    main()