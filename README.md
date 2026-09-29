# InsightGrid
Natural Language → SQL → Data Analysis & Visualization

Developed by Dev Dogra
GitHub: [DevVinciCode](https://github.com/DevVinciCode)

**Status: Stage 1 + 2 of the design doc are fully implemented and tested.**
Stage 3–6 (uncertainty-gated clarification, database probing, Power BI,
evaluation) are real, independently-testable code, scaffolded but not yet
wired into the main pipeline — see `docs/architecture.md` for exactly what's
live vs. what's a documented next step. This is deliberate, not a shortcut:
see section 27/29 of the original design doc on staged development.

## Quickstart (runs with zero configuration — no API key required)

```bash
# 1. Backend
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
# -> http://localhost:8000/docs for interactive API docs
```

The demo SQLite database (`data/demo_database/demo.db`) is already built and
committed to the repo. To regenerate it (e.g. after editing `seed.py`):

```bash
cd data/demo_database
python3 seed.py
```

```bash
# 2. Frontend (in a new terminal)
cd frontend
npm install
npm run dev
# -> http://localhost:5173
```

Open the frontend, click one of the example questions, and you'll see the
full pipeline run: SQL generated, validated, executed against the real demo
database, charted, with a "Research / Developer Panel" showing intent,
retrieved RAG context, SQL, validation issues, confidence scores, and
provenance for every answer.

## Connecting your own database

Click **"Connect database"** in the app header. Three options:

- **Demo database** — the bundled e-commerce SQLite DB (default).
- **Upload SQLite** — upload any `.db`/`.sqlite` file; schema is auto-discovered
  (tables, columns, keys, relationships) and re-indexed into RAG immediately.
- **Connect PostgreSQL** — enter host/port/database/user/password. Requires
  `psycopg2-binary` (`pip install psycopg2-binary`) in the backend environment.

**Important:** the zero-config `LLM_PROVIDER=rulebased` fallback is a template
engine hard-coded to the demo schema's table/column names. If you connect a
different database while still on `rulebased`, the app will tell you clearly
that it can't answer rather than silently generating broken SQL. To ask
*arbitrary* questions against *your own* database, set a real LLM provider
first (see below) — the RAG retrieval, intent extraction, and SQL generation
prompts are all schema-agnostic when a real LLM is configured; they read
whatever schema is currently connected and never assume the demo domain.

## Using a real LLM instead of the zero-config template engine

By default `LLM_PROVIDER=rulebased` — a deterministic template engine that
requires no API key so the MVP runs immediately (per the "clone → install →
add key → run" requirement, the key step is optional here, not required).
It only understands a small set of keyword patterns — good for demoing the
*pipeline*, not general question coverage. To handle arbitrary questions,
point it at a real model:

```bash
# In backend/.env
LLM_PROVIDER=openai        # or: groq | gemini
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini      # or a Groq/Gemini model name
```

No other code changes needed — `services/llm_provider.py` is the only file
that knows about provider-specific request formats.

## Example queries

```
What was our monthly revenue last year?
Which product categories generated the most revenue?
Compare Delhi and Mumbai revenue in 2025.
Show the top 10 products by profit.
Show revenue by month and category.
```

Intentionally ambiguous (demonstrate the current limits — Stage 3
clarification isn't wired in yet, so these currently get a best-effort
answer rather than a clarifying question):

```
Which customers are most valuable?
Which products are performing poorly?
What will revenue be next month?
```

## Project structure

```
backend/app/
  api/            FastAPI routes + request/response schemas
  config/         Settings (.env-driven)
  conversation/   Session state — analytical intent across turns
  database/       Connection, schema extraction, safe execution
  evaluation/     Benchmark harness (Stage 6)
  intent/         Intent extraction + clarification scaffold (Stage 3)
  models/         Pydantic models (AnalyticalIntent, Filter)
  powerbi/        PowerBIService (Stage 5)
  rag/            Document builder, TF-IDF vector store, retriever
  services/       LLMProvider abstraction, main pipeline orchestrator
  sql/            SQL generation + multi-level validation
  verification/   Result verification, uncertainty scoring, probing scaffold
  visualization/  Chart-type planner

data/demo_database/   seed.py + the built demo.db
frontend/src/         React app (chat, chart, table, dev panel)
tests/                pytest suite (8 tests, all passing)
docs/                 architecture.md, research_direction.md,
                       powerbi_setup.md, evaluation.md
```

## Running tests

```bash
cd backend
pip install pytest
python3 -m pytest ../tests/ -v
```

## Known limitations

See `docs/research_direction.md` → "Known limitations" for the full list.
The short version: the rule-based fallback is a template engine, not a
general NL-to-SQL model; confidence scores are heuristic and uncalibrated;
Stage 3/5 features are scaffolded but not exercised by real traffic yet.

## Research contribution, novelty classification, suggested experiments

See `docs/research_direction.md`.

## Author

Developed by Dev Dogra.

This repository represents my original project work and implementation.
