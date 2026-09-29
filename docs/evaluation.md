# Evaluation

Run the built-in benchmark:

```bash
curl http://localhost:8000/api/evaluation/run
```

This runs `backend/app/evaluation/benchmark.py`'s 5-question labeled set
through the full pipeline and reports:

- `intent_accuracy` — predicted intent type == expected intent type
- `sql_execution_accuracy` — query ran without a database error
- `visualization_match_rate` — predicted chart type == expected chart type
- `avg_latency_ms`

These are all **structurally checkable** — no judgment call needed about
whether the answer is actually *correct*, just whether the pipeline produced
the expected shape of output.

## Metrics that need a judge (not implemented)

The design doc also calls for:

- **Semantic correctness** — does the SQL actually answer the question
  correctly, beyond "it ran and has the right shape"? This needs either a
  human rater or an LLM-as-judge comparing the result against a known-correct
  answer for each benchmark question.
- **Clarification accuracy / unnecessary clarification rate** — needs a
  labeled set of genuinely-ambiguous vs. answerable questions, evaluated
  against Stage 3's `intent/clarification.py` once it's wired into the
  pipeline (see `docs/architecture.md`).
- **Abstention accuracy** — same: needs labeled "should abstain" examples.
- **Schema retrieval recall** — needs a labeled mapping of question → the
  set of tables/columns a correct answer *should* retrieve, then checking
  `RetrievedContext.documents` against it.

## How to add an LLM-judge metric

1. Extend `BENCHMARK_QUESTIONS` in `evaluation/benchmark.py` with an
   `expected_answer_description` field (plain-language description of what a
   correct result looks like, not the exact rows — those will drift as the
   demo data changes).
2. After execution, prompt a judge model with the question, the SQL, and a
   sample of the result rows, asking it to rate 1–5 whether the result
   plausibly answers the question.
3. Report the mean judge score alongside the structural metrics — keep them
   in separate columns so a reader can tell which numbers are
   judge-dependent and which aren't.

## Extending the benchmark set

Add cases to `BENCHMARK_QUESTIONS` with `answerable: False` for the
intentionally ambiguous/unanswerable examples in the design doc (section 23)
once Stage 3's clarification/abstention logic is wired into the pipeline —
right now those questions just run through the rule-based/LLM path like any
other and won't exercise ASK/ABSTAIN behavior.
