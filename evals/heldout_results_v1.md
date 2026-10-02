# Held-Out Policy Evaluation

The classifier was frozen before this evaluation.

## Results

| Metric | Result |
|---|---:|
| Tickets evaluated | 20 |
| Successful predictions | 20/20 |
| Structured-output success | 100.0% |
| Category accuracy | 90.0% |
| Queue accuracy | 40.0% |
| Ticket-type accuracy | 80.0% |
| Priority accuracy | 75.0% |
| Review-trigger accuracy | 95.0% |
| All four classification fields correct | 30.0% |
| Average confidence | 0.9175 |
| Average latency | 1.462 s |

## Methodology

The classifier and classification prompt were frozen before
evaluation on this separately curated 20-ticket held-out set.

The review-trigger metric measures the classification-side
conditions only: security category, urgent priority, or
classification confidence below the configured threshold.

The complete LangGraph workflow may additionally request human
review when answer-generation confidence is below threshold.
