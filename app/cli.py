from __future__ import annotations

import argparse
import json

from app.schemas import TicketInput
from app.service import get_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one support ticket through the AI triage graph.")
    parser.add_argument("subject")
    parser.add_argument("body")
    parser.add_argument("--email", default=None)
    args = parser.parse_args()

    result = get_service().triage(
        TicketInput(subject=args.subject, body=args.body, customer_email=args.email)
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
