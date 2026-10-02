# Public Dataset Evaluation

Generated with:

```bash
python evals/run_dataset_eval.py --samples 25
```

## Results

| Metric | Result |
|---|---:|
| Tickets evaluated | 25 |
| Successful structured outputs | 24/25 |
| Structured-output success | 96.0% |
| Queue accuracy | 25.0% |
| Ticket-type accuracy | 62.5% |
| Priority accuracy | 25.0% |
| Average confidence | 0.9221 |
| Average latency | 1.55 s |

## Notes

- The public dataset supplies queue, ticket type, and priority labels.
- Internal issue category is predicted by the application but is not scored because the dataset does not provide the same category taxonomy.
- Failed API/structured-output requests are counted in structured-output success rate.
- Accuracy metrics are calculated only over successful predictions.
