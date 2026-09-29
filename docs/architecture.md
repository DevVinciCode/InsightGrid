# Architecture

## What's actually built (Stage 1 + 2) vs. scaffolded (Stage 3–6)

This codebase follows the staged build strategy on purpose: a fully working
core loop first, with the advanced research modules built as real,
independently testable code but not force-fit into the main pipeline until
they're worth the added complexity.

```
Question
   |
   v
RAG retrieval (rag/retriever.py)         <- WIRED IN
   |
   v
Intent extraction (intent/extractor.py)  <- WIRED IN
   |
   v
SQL generation (sql/generator.py)        <- WIRED IN
   |
   v
Multi-level validation (sql/validator.py)<- WIRED IN
   |
   v
Safe execution + retry loop              <- WIRED IN
(database/executor.py, services/pipeline.py)
   |
   v
Result verification                      <- WIRED IN
(verification/result_verification.py)
   |
   v
Visualization planning                   <- WIRED IN
(visualization/planner.py)
   |
   v
Conversational state update              <- WIRED IN
(conversation/state.py)
```

Everything above is exercised by `tests/integration/test_pipeline.py` and by
running the FastAPI app directly (see README).

## Stage 3: Uncertainty-gated clarification (scaffolded, not wired in)

`intent/clarification.py` implements the ANSWER / INVESTIGATE / ASK / ABSTAIN
decision policy described in the design doc, and `verification/probing.py`
implements safe, read-only exploratory queries. Both are real, tested code —
just not called from `services/pipeline.py` yet.

**Why not wired in yet:** the decision policy needs a real ambiguity
taxonomy grounded in the schema (right now it's a small hand-authored keyword
table — `AMBIGUOUS_TERMS` — which is enough to demonstrate the mechanism but
not enough to claim general ambiguity detection). Wiring plan:

1. In `Pipeline.run_turn`, after intent extraction, call
   `clarification.decide(question, intent, tables)`.
2. On `ASK`, short-circuit and return `question_to_user` instead of
   proceeding to SQL generation.
3. On `INVESTIGATE`, run a bounded probe from `probing.py`, feed the result
   back into a second `decide()` call.
4. On `ABSTAIN`, return a message explaining the limitation.

## Stage 5: Power BI (scaffolded, honestly bounded)

`powerbi/service.py` implements real Azure AD token acquisition and embed
token generation against the Power BI REST API — this part actually works if
you provide real credentials (see `docs/powerbi_setup.md`).

What it deliberately does **not** claim to do: dynamically create or modify
a Power BI report's visuals. The Power BI REST API has no supported
endpoint for that — report design happens in Power BI Desktop or the
service UI. So "Power BI mode" means embedding a report you built once, with
basic filter parameters passed through; "MVP mode" (native React/Recharts,
driven by `visualization/planner.py`) is the fully dynamic path.

## Stage 6: Evaluation (scaffolded, partial)

`evaluation/benchmark.py` measures what's structurally checkable without a
judge model: intent accuracy, SQL execution success, visualization-type
match, latency. Semantic-correctness, clarification-quality, and
abstention-quality metrics are listed in `docs/evaluation.md` along with why
they need either an LLM-as-judge or a human rater, and how to wire one in.

## Swapping components

Every "provider" in this system is a small interface with one default,
dependency-light implementation:

| Interface | Default | Swap in by |
|---|---|---|
| `DatabaseProvider` (`database/connection.py`) | SQLite | set `DB_TYPE=postgresql` in `.env` |
| `LLMProvider` (`services/llm_provider.py`) | `RuleBasedProvider` (templates, no key) | set `LLM_PROVIDER=openai\|groq\|gemini` + `LLM_API_KEY` |
| `VectorStore` (`rag/vector_store.py`) | TF-IDF (scikit-learn) | implement `FaissVectorStore`/`ChromaVectorStore` against the same interface |

No other code needs to change when you swap any of these — that's the point
of the interface boundary.
