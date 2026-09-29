# DataTalk — Micro Project Review 1 PPT Content

> **12 Slides · Department of CSE-AIML · Micro Project 2026-27**
> Follow the same slide structure as the SkillSync reference PPT.

---

## SLIDE 1 — PROJECT OVERVIEW (Title Slide)

**Header:** MICRO PROJECT 2026-27 · Department of CSE - AIML

**Project Title:**
### DATATALK
*A Conversational Text-to-SQL System with RAG-Based Schema Retrieval, Multi-Level Validation, and Visualization-as-Verification*

**Mentor:** Dr. Srishti Vashishtha

**Presented By:**
- UTKARSH CHAUDHARY (08011502723)
- YASH VERMA (08111502723)
- KARTIKEY GUPTA (08811502723)

*(Slide number: 1)*

---

## SLIDE 2 — TABLE OF CONTENTS

**Header:** MICRO PROJECT 2026-27 · Department of CSE - AIML

- Introduction
- Problem Statement
- Literature Survey
- Research Gap
- Objectives
- Proposed Methodology
- Performance Comparison of Existing Methodology
- Current Progress / Expected Outcomes
- References in IEEE Format

*(Slide number: 2)*

---

## SLIDE 3 — INTRODUCTION: THE PROBLEM

**Header:** INTRODUCTION · MICRO PROJECT 2026-27 · Department of CSE - AIML

**Section Title:** THE PROBLEM

Organizations today sit on massive structured databases containing critical business insights, yet extracting meaningful answers requires specialized SQL expertise. Decision-makers, analysts, and non-technical stakeholders face three major barriers:

- **How do I query this?** → Writing correct SQL demands knowledge of database schema, joins, and syntax — skills most business users lack.
- **Can I trust the results?** → Even when SQL is written (by hand or by an AI), there is no built-in verification that the generated query actually answers the original question correctly.
- **How do I understand the data?** → Raw tabular query outputs are hard to interpret without appropriate visualizations, and manually choosing the right chart type adds another skill requirement.

**EXAMPLE:**
> A marketing manager wants to know *"Which product categories generated the most revenue last quarter?"*
> Today, they must either learn SQL, wait for an analyst, or rely on static dashboards that may not cover this specific question. DataTalk lets them type the question in plain English and instantly get a validated SQL query, verified results, and an auto-generated bar chart — with full provenance of every step.

*(Slide number: 3)*

---

## SLIDE 4 — INTRODUCTION: OUR SOLUTION

**Header:** INTRODUCTION: OUR SOLUTION · MICRO PROJECT 2026-27 · Department of CSE - AIML

### DataTalk — From Question to Insight in One Sentence

**KEY IDEA:**

Instead of solving only *"How do I write this SQL?"*, DataTalk combines:

**Natural Language Understanding + RAG-Based Schema Retrieval + Text-to-SQL Generation + Multi-Level Validation + Safe Execution + Visualization Planning + Verification**

into one explainable, end-to-end conversational analytics pipeline.

**What Makes DataTalk Different:**

| Feature | Traditional BI Tools | Generic Text-to-SQL | DataTalk |
|---------|---------------------|---------------------|----------|
| Natural Language Input | ✗ | ✓ | ✓ |
| Schema-Aware Retrieval (RAG) | ✗ | ✗ | ✓ |
| Multi-Level SQL Validation | ✗ | ✗ | ✓ |
| Auto Error-Retry Loop | ✗ | ✗ | ✓ |
| Visualization-as-Verification | ✗ | ✗ | ✓ |
| Conversational Follow-ups | ✗ | Partial | ✓ |
| Full Provenance Trail | ✗ | ✗ | ✓ |

*(Slide number: 4)*

---

## SLIDE 5 — DETAILED LITERATURE SURVEY – I

**Header:** DETAILED LITERATURE SURVEY-I · MICRO PROJECT 2026-27 · Department of CSE - AIML

**Focus:** Text-to-SQL and Schema-Aware Approaches

| Sr. | Paper / System | Year | Key Technique | Limitation |
|-----|----------------|------|---------------|------------|
| 1 | Zhong et al. — *Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning* | 2017 | Seq-to-seq encoder with RL-based policy optimization for SQL generation | Limited to single-table, simple queries; no schema reasoning |
| 2 | Yu et al. — *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Database Semantic Parsing* | 2018 | Benchmark dataset with cross-database generalization for text-to-SQL | Provides evaluation framework but not a solution approach |
| 3 | Scholak et al. — *PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models* | 2021 | Constrained decoding on pre-trained LMs ensuring syntactically valid SQL | No schema-aware retrieval; relies solely on the model's parametric knowledge |
| 4 | Li et al. — *RESDSQL: Decoupling Schema Linking and Skeleton Parsing for Text-to-SQL* | 2023 | Two-stage approach separating schema linking from SQL skeleton generation | Requires task-specific fine-tuning; not plug-and-play with general LLMs |
| 5 | Gao et al. — *Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation* | 2024 | Comprehensive LLM-based Text-to-SQL benchmark using GPT-4, Claude, etc. | No multi-level validation or error correction feedback loop |

**TAKEAWAY:** Existing Text-to-SQL research focuses on generation accuracy but lacks integrated verification, error self-correction, and result visualization.

*(Slide number: 5)*

---

## SLIDE 6 — DETAILED LITERATURE SURVEY – II

**Header:** DETAILED LITERATURE SURVEY-II · MICRO PROJECT 2026-27 · Department of CSE - AIML

**Focus:** RAG, Conversational Analytics and Visualization

| Sr. | Paper / System | Year | Key Technique | Limitation |
|-----|----------------|------|---------------|------------|
| 6 | Lewis et al. — *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* | 2020 | RAG architecture combining retrieval with generation for factual grounding | Applied to open-domain QA, not database schema retrieval |
| 7 | Pourreza and Rafiei — *DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction* | 2024 | Decomposition of Text-to-SQL into sub-tasks with LLM self-correction | No visualization verification; self-correction is prompt-based only |
| 8 | Talaei et al. — *Chess: Contextual Harnessing for Efficient SQL Synthesis* | 2024 | Contextual schema pruning for efficient SQL generation | Focuses on schema pruning, not end-to-end pipeline with verification |
| 9 | Luo et al. — *DBCopilot: Scaling Natural Language Querying to Massive Databases* | 2024 | Routing + schema linking for massive multi-database NL querying | No result verification or visualization component |
| 10 | Liu et al. — *A Survey on Employing LLMs for Text-to-SQL Tasks* | 2024 | Comprehensive survey covering prompting strategies and fine-tuning for Text-to-SQL | Identifies open challenges: validation, error handling, multi-turn remain unsolved |

**TAKEAWAY:** Recent work improves generation through LLMs and RAG, but no existing system integrates RAG-based schema retrieval, multi-level validation, error self-correction, and visualization-as-verification into a single closed-loop pipeline.

*(Slide number: 6)*

---

## SLIDE 7 — RESEARCH GAP

**Header:** RESEARCH GAP · MICRO PROJECT 2026-27 · Department of CSE - AIML

**EXISTING SYSTEMS** generally solve one or two parts:

| Text-to-SQL Generation | Schema Retrieval | SQL Validation | Result Verification | Visualization Planning |
|:-:|:-:|:-:|:-:|:-:|
| Seq2SQL, PICARD, RESDSQL | DIN-SQL (partial) | None | None | None |

There is no single lightweight and explainable pipeline that combines:

**Natural Language Question → RAG Schema Retrieval → Intent Extraction → SQL Generation → Multi-Level Validation → Error-Feedback Retry → Safe Execution → Result Verification → Visualization-as-Verification → Conversational Follow-ups**

**OUR CONTRIBUTION:**
- A user is guided through a **verified, explainable analytics pipeline** rather than receiving a raw, unvalidated SQL response.
- The visualization layer itself acts as an **independent verification step** — if the result shape does not match the intended chart structure, it signals a possible SQL or semantic error.
- Complete **provenance trail** from question → intent → retrieved schema → generated SQL → validated result → chart.

*(Slide number: 7)*

---

## SLIDE 8 — OBJECTIVES

**Header:** OBJECTIVES · MICRO PROJECT 2026-27 · Department of CSE - AIML

**O1.** To design a RAG-based schema retrieval module that automatically indexes database structure (tables, columns, keys, relationships, and sample values) and retrieves relevant schema context for each user question using TF-IDF vector similarity.

**O2.** To implement intent extraction from natural language questions, identifying the analytical type (trend, comparison, ranking, aggregation, filtering, lookup), target metric, dimensions, and filters.

**O3.** To build a Text-to-SQL generation engine powered by LLMs (supporting OpenAI, Groq, Gemini) that produces syntactically and semantically valid SQL from the retrieved schema context and extracted intent.

**O4.** To implement multi-level SQL validation comprising syntax checking, schema validation (table/column existence), safety enforcement (blocking DELETE, DROP, UPDATE), and semantic verification against the analytical intent.

**O5.** To design an error-feedback self-correction loop where SQL execution errors are fed back to the LLM for automatic query regeneration (reflexion pattern), with bounded retry limits.

**O6.** To develop a rule-based visualization planner that maps analytical intent and result shape to appropriate chart types (bar, line, area, donut, table) and uses structural mismatch detection as a secondary verification signal.

**O7.** To integrate the above into one working web application with a React + Recharts frontend and a Python FastAPI backend, supporting conversational follow-ups, database upload (SQLite/CSV), and a full developer provenance panel.

*(Slide number: 8)*

---

## SLIDE 9 — PROPOSED METHODOLOGY: PIPELINE

**Header:** PROPOSED METHODOLOGY—PIPELINE · MICRO PROJECT 2026-27 · Department of CSE - AIML

### DataTalk End-to-End Pipeline

```
 ┌──────────────────┐
 │  User Question    │   "What was our monthly revenue last year?"
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ RAG Retrieval     │   Schema documents indexed via TF-IDF;
 │ (rag/retriever)   │   retrieves relevant tables, columns, keys
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Intent Extraction │   Identifies: trend_analysis, metric=revenue,
 │ (intent/extractor)│   dimensions=[month], filters=[year=last year]
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ SQL Generation    │   LLM generates SQL using schema context +
 │ (sql/generator)   │   extracted intent as prompt
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Multi-Level       │   Syntax → Schema → Safety → Semantic
 │ Validation        │   validation checks
 │ (sql/validator)   │   Blocks unsafe operations (DROP, DELETE)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Safe Execution    │   Executes validated SQL against the database
 │ + Retry Loop      │   On error → feeds error back to LLM →
 │ (pipeline.py)     │   regenerates SQL (up to 3 retries)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Result            │   Verifies result shape, row count,
 │ Verification      │   column types against expected intent
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Visualization     │   Maps intent + result shape → chart type
 │ Planner           │   Detects structure mismatch (viz-as-verification)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Conversational    │   Updates session state for follow-up questions
 │ State Update      │   Maintains analytical context across turns
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │ Frontend Display  │   React UI renders chart (Bar/Line/Area/Donut),
 │ (React+Recharts)  │   data table, KPI cards, provenance panel
 └──────────────────┘
```

**Key Points:**
- DataTalk starts by indexing the connected database schema into a RAG vector store.
- Each question triggers the full pipeline: retrieve → understand → generate → validate → execute → verify → visualize.
- The error-feedback retry loop and visualization-as-verification make the system self-correcting.
- The system supports SQLite file upload, CSV ingestion, and PostgreSQL connections.

*(Slide number: 9)*

---

## SLIDE 10 — PERFORMANCE COMPARISON OF EXISTING METHODOLOGY

**Header:** PERFORMANCE COMPARISON OF EXISTING METHODOLOGY · MICRO PROJECT 2026-27 · Department of CSE - AIML

| Feature / Capability | ChatGPT (Code Interpreter) | Seq2SQL / PICARD | DIN-SQL | DBCopilot | **DataTalk (Ours)** |
|---|---|---|---|---|---|
| Natural Language → SQL | ✓ | ✓ | ✓ | ✓ | ✓ |
| Schema-Aware RAG Retrieval | ✗ | ✗ | Partial | ✓ | ✓ |
| Multi-Level SQL Validation | ✗ | ✗ | ✗ | ✗ | ✓ |
| Error Self-Correction Loop | ✗ | ✗ | ✓ (prompt) | ✗ | ✓ (execution-level) |
| Safety Enforcement (DDL block) | ✗ | ✗ | ✗ | ✗ | ✓ |
| Result Verification | ✗ | ✗ | ✗ | ✗ | ✓ |
| Visualization-as-Verification | ✗ | ✗ | ✗ | ✗ | ✓ |
| Auto Visualization | ✗ | ✗ | ✗ | ✗ | ✓ |
| Conversational Follow-ups | ✓ (generic) | ✗ | ✗ | ✗ | ✓ (analytics-aware) |
| Provenance / Explainability | ✗ | ✗ | ✗ | ✗ | ✓ |
| Database Upload (SQLite/CSV) | ✓ | ✗ | ✗ | ✗ | ✓ |
| Runs Locally / Self-Hosted | ✗ | ✓ | ✓ | ✓ | ✓ |

**Key Differentiator:** DataTalk is the only system that integrates RAG retrieval, multi-level validation, execution-level error self-correction, and visualization-as-verification into a single closed-loop pipeline with full provenance.

*(Slide number: 10)*

---

## SLIDE 11 — CURRENT PROGRESS / EXPECTED OUTCOMES

**Header:** CURRENT PROGRESS · MICRO PROJECT 2026-27 · Department of CSE - AIML

### Current Progress

| Milestone | Status |
|-----------|--------|
| **Literature Review** | Completed — Studied 10+ papers on Text-to-SQL, RAG, conversational analytics, and visualization systems |
| **Architecture Design** | Completed — Full pipeline design with staged development strategy (6 stages) |
| **Backend Core Pipeline** | Completed — RAG retriever, intent extractor, SQL generator, multi-level validator, safe executor, retry loop, result verifier, visualization planner — all wired and functional |
| **LLM Provider Abstraction** | Completed — Supports OpenAI, Groq, Gemini, and a zero-config rule-based fallback |
| **Frontend UI** | Completed — React app with chat interface, ChartView (Bar/Line/Area/Donut), DatasetExplorer sidebar, KPI metric cards, database connect modal, provenance panel |
| **Database Support** | Completed — SQLite upload, CSV ingestion, PostgreSQL connection |
| **Testing** | 8 integration tests passing |

### Expected Outcomes

- **Accurate SQL Generation** from natural language questions against any user-uploaded database.
- **Self-Correcting Queries** through the error-feedback retry loop, reducing manual intervention.
- **Automatic Visualization** with smart chart selection based on data shape and analytical intent.
- **Visualization-as-Verification** detecting structural mismatches between expected and actual result shapes.
- **Conversational Follow-ups** maintaining analytical context across multiple turns.
- **Full Provenance** showing Question → Intent → Schema Context → SQL → Validation → Result → Chart for every answer.

*(Slide number: 11)*

---

## SLIDE 12 — REFERENCES IN IEEE FORMAT

**Header:** REFERENCES · MICRO PROJECT 2026-27 · Department of CSE - AIML

[1] V. Zhong, C. Xiong, and R. Socher, "Seq2SQL: Generating structured queries from natural language using reinforcement learning," arXiv preprint arXiv:1709.00103, 2017.

[2] T. Yu et al., "Spider: A large-scale human-labeled dataset for complex and cross-database semantic parsing and text-to-SQL task," in Proc. of the 2018 Conf. on Empirical Methods in Natural Language Processing (EMNLP), 2018, pp. 3911-3921, doi: 10.18653/v1/D18-1425.

[3] T. Scholak, N. Schucher, and D. Baez, "PICARD: Parsing incrementally for constrained auto-regressive decoding from language models," in Proc. of the 2021 Conf. on Empirical Methods in Natural Language Processing (EMNLP), 2021, pp. 9895-9901.

[4] H. Li et al., "RESDSQL: Decoupling schema linking and skeleton parsing for text-to-SQL," in Proc. of the AAAI Conf. on Artificial Intelligence, vol. 37, no. 11, 2023, pp. 13067-13075, doi: 10.1609/aaai.v37i11.26535.

[5] D. Gao et al., "Text-to-SQL empowered by large language models: A benchmark evaluation," Proc. of the VLDB Endowment, vol. 17, no. 5, pp. 1132-1145, 2024, doi: 10.14778/3641204.3641221.

[6] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 9459-9474.

[7] M. Pourreza and D. Rafiei, "DIN-SQL: Decomposed in-context learning of text-to-SQL with self-correction," in Advances in Neural Information Processing Systems (NeurIPS), vol. 36, 2024.

[8] S. Talaei et al., "Chess: Contextual harnessing for efficient SQL synthesis," arXiv preprint arXiv:2405.16755, 2024.

[9] X. Luo et al., "DBCopilot: Scaling natural language querying to massive databases," in Proc. of the ACM SIGMOD Int. Conf. on Management of Data, 2024, pp. 309-322, doi: 10.1145/3639269.

[10] B. Liu et al., "A survey on employing large language models for text-to-SQL tasks," arXiv preprint arXiv:2407.15186, 2024.

*(Slide number: 12)*

---

## DESIGN NOTES

- **Template Style:** Follow the same dark-header / white-body layout as the SkillSync reference PPT.
- **Every slide should have:** "MICRO PROJECT 2026-27" + "Department of CSE - AIML" in the header/footer.
- **Slide numbers** in bottom-right corner.
- **Duration:** 10-15 minutes presentation.
- **Total Slides:** 12 (matches the prescribed format from the college notice).
