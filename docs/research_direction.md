# Research Direction

Per the "don't fake novelty" requirement, here's an honest breakdown of every
claimed component:

| Component | Classification |
|---|---|
| RAG over schema/relationships/semantics/analytics | Existing technique (standard retrieval-augmented generation), applied to a database-analytics-specific document taxonomy |
| Text-to-SQL generation | Existing technique |
| SQL syntax/schema/safety validation | Existing technique (established in prior text-to-SQL systems) |
| SQL execution error-feedback retry loop | Existing technique (self-correction / reflexion pattern) |
| Structured analytical intent as conversational state | Combination of existing techniques (slot-filling dialogue state + text-to-SQL) |
| Uncertainty scores per pipeline stage | Engineering contribution — simple heuristics, explicitly **not** calibrated probabilities (see `verification/uncertainty.py`) |
| ANSWER/INVESTIGATE/ASK/ABSTAIN policy | Combination of existing techniques (dialogue-act classification + retrieval-augmented clarification), scaffolded but not fully evaluated here |
| Database probing for evidence gathering | Engineering contribution (bounded, safety-constrained exploratory querying) |
| Visualization planning as a rule-based mapping | Existing technique — deliberately *not* "ask an LLM to pick a chart" |
| **Visualization as verification** (comparing expected vs. actual result structure against the planned chart) | **Potential research contribution** — using the visualization layer's structural expectations as a second, independent check on SQL/result correctness, integrated into the same loop as syntax/schema/semantic validation |
| Provenance view (question → intent → tables → SQL → result → viz) | Engineering contribution (UX pattern), not novel in isolation |

## The strongest intended contribution

> A database-grounded, uncertainty-aware conversational analytics loop in
> which the system can answer, investigate, clarify, or abstain; generated
> SQL and result structures are checked against inferred analytical intent;
> and visualization/provenance are integrated into the verification loop
> rather than being a downstream, disconnected rendering step.

This is a **combination and integration** contribution, not a claim of a
novel algorithm. The individual pieces (RAG, text-to-SQL, uncertainty
estimation, clarification dialogue, chart-type selection) all exist in prior
work; what's less common is running them as one closed loop where the
visualization layer feeds back into correctness checking.

## Suggested paper title

*"Ask, Investigate, or Abstain: A Database-Grounded Conversational Analytics
Loop with Visualization-as-Verification"*

## Suggested experiments

1. **Ablation on the verification loop.** Compare end-to-end task success
   (does the final chart answer the question correctly, per human rating)
   with vs. without the visualization-structure-mismatch check enabled.
2. **Clarification precision/recall.** Once Stage 3 is wired in, measure how
   often ASK correctly identifies genuine ambiguity vs. how often it
   unnecessarily interrupts an answerable question (`unnecessary_clarification_rate`
   in the design doc).
3. **Confidence-score calibration.** Bucket the heuristic confidence scores
   from `verification/uncertainty.py` and check whether higher buckets
   actually correlate with higher measured accuracy — if not, that's a
   concrete way to motivate replacing heuristics with a learned/calibrated
   model.
4. **Probing vs. asking.** Compare task success and turn count when
   ambiguity is resolved via database probing (Stage 3) vs. always asking
   the user.

## Known limitations

- The rule-based intent/SQL fallback (`LLM_PROVIDER=rulebased`) is a
  template engine for zero-config demoing, not a general NL-to-SQL model —
  it will miss things like named entities ("Delhi", "Mumbai") that aren't in
  its small keyword tables. Point `LLM_PROVIDER` at a real model for general
  question coverage.
- Confidence scores are heuristic, not calibrated (see table above).
- Stage 3 (clarification/probing) and Power BI dynamic visuals are
  scaffolded but not exercised by real users yet — see `docs/architecture.md`.
- Evaluation metrics requiring semantic judgment are not implemented — see
  `docs/evaluation.md`.

## Suggested future work

- Calibrate confidence scores against a labeled dataset of query outcomes.
- Replace the keyword-based ambiguity taxonomy with one derived from
  clustering historical queries against the schema.
- Extend the evaluation harness with an LLM-as-judge for semantic SQL
  correctness and clarification quality.
- Multi-database support: the `DatabaseProvider`/`VectorStore` interfaces
  are already designed for this — the missing piece is per-database RAG
  index management (currently one process = one schema).
