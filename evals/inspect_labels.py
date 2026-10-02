import json
from collections import Counter
from pathlib import Path

DATA_PATH = Path("data/evaluation/support_eval.jsonl")

queues = Counter()
priorities = Counter()
ticket_types = Counter()

with DATA_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)

        queues[row["expected_queue"]] += 1
        priorities[row["expected_priority"]] += 1

        if row.get("ticket_type"):
            ticket_types[row["ticket_type"]] += 1


print("\n=== QUEUES ===")
for label, count in queues.most_common():
    print(f"{label:<40} {count}")

print("\n=== PRIORITIES ===")
for label, count in priorities.most_common():
    print(f"{label:<20} {count}")

print("\n=== TICKET TYPES ===")
for label, count in ticket_types.most_common():
    print(f"{label:<20} {count}")

print("\nSUMMARY")
print(f"Unique queues:     {len(queues)}")
print(f"Unique priorities: {len(priorities)}")
print(f"Unique types:      {len(ticket_types)}")