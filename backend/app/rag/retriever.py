"""
Thin orchestration layer: build documents from live schema metadata, index
them, retrieve top-k relevant documents for a question.

Question -> Embedding -> Vector retrieval -> Relevant schema + semantic context
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine

from app.database.schema_extractor import extract_schema
from app.rag.documents import RagDocument, build_documents
from app.rag.vector_store import VectorStore, get_vector_store


@dataclass
class RetrievedContext:
    documents: list[RagDocument]
    scores: list[float]

    def as_prompt_block(self) -> str:
        lines = []
        for doc, score in zip(self.documents, self.scores):
            lines.append(f"[{doc.kind} | relevance={score:.2f}]\n{doc.text}")
        return "\n\n".join(lines)


class Retriever:
    """Owns one VectorStore instance and (re)indexes it from the live schema."""

    def __init__(self, engine: Engine, store_kind: str = "tfidf") -> None:
        self._engine = engine
        self._store: VectorStore = get_vector_store(store_kind)
        self._indexed = False

    def build_index(self) -> int:
        from app.database.manager import database_manager

        tables = extract_schema(self._engine)
        is_demo_db = database_manager.info.kind == "demo"
        documents = build_documents(tables, include_demo_semantics=is_demo_db)
        self._store.index(documents)
        self._indexed = True
        return len(documents)

    def get_full_schema_summary(self) -> str:
        tables = extract_schema(self._engine)
        lines = ["=== ACTIVE DATABASE SCHEMA ==="]
        for t in tables:
            cols = []
            for c in t.columns:
                pk = " [PK]" if c.primary_key else ""
                sample = f" (e.g. {c.sample_values[:2]})" if c.sample_values else ""
                cols.append(f"{c.name} {c.type}{pk}{sample}")
            lines.append(f"Table '{t.table}' ({t.row_count} rows):")
            lines.append("  Columns: " + ", ".join(cols))
            if t.foreign_keys:
                fks = [f"{t.table}.{fk.column} -> {fk.ref_table}.{fk.ref_column}" for fk in t.foreign_keys]
                lines.append("  Explicit Foreign Keys: " + "; ".join(fks))

        # Relational analytics join inference (covers cases where SQLite DDL doesn't declare explicit foreign keys)
        t_names = {t.table.lower() for t in tables}
        relationships = []
        if "orders" in t_names and "customers" in t_names:
            relationships.append("orders.customer_id = customers.customer_id")
        if "orders" in t_names and "order_items" in t_names:
            relationships.append("order_items.order_id = orders.order_id")
        if "order_items" in t_names and "products" in t_names:
            relationships.append("order_items.product_id = products.product_id")
        if relationships:
            lines.append("Inferred Relationships: " + " | ".join(relationships))

        # Metric computation notes
        if "order_items" in t_names:
            lines.append("Sales / Revenue Formula: SUM(order_items.quantity * order_items.unit_price)")
        elif "orders" in t_names and any("revenue" in [c.name.lower() for c in t.columns] for t in tables if t.table == "orders"):
            lines.append("Sales / Revenue Formula: SUM(orders.revenue)")

        return "\n".join(lines)

    def retrieve(self, question: str, top_k: int = 5) -> RetrievedContext:
        if not self._indexed:
            self.build_index()
        results = self._store.search(question, top_k=top_k)

        # Always include the full live database schema so the LLM is never missing context
        schema_summary = self.get_full_schema_summary()
        always_docs = [RagDocument(doc_id="schema_full_overview", kind="schema_overview", text=schema_summary)]

        matched_docs = [d for d, _ in results if d.doc_id != "schema_full_overview"]
        matched_scores = [s for _, s in results]

        all_docs = always_docs + matched_docs
        all_scores = [1.0] + matched_scores

        return RetrievedContext(
            documents=all_docs,
            scores=all_scores,
        )
