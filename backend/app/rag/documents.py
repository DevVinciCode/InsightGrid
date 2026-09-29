"""
Builds retrievable text documents from schema metadata. Deliberately NOT just
"embed the table names" — four document kinds, matching the design doc:

  1. schema knowledge      (per table: purpose + columns)
  2. relationship knowledge (foreign keys, in plain language)
  3. semantic knowledge     (business definitions — hand-authored)
  4. analytical knowledge   (metric -> source/aggregation/time-dimension)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.database.schema_extractor import TableMeta, SEMANTIC_NOTES

# Analytical concept knowledge — the "what does 'revenue' mean as a metric"
# layer. Hand-authored for the demo schema; in a general system this could be
# partly inferred, but explicit definitions are more reliable and auditable.
ANALYTICAL_CONCEPTS = [
    {
        "concept": "revenue",
        "text": "Revenue:\n- source: orders.revenue\n- aggregation: SUM\n"
                "- time dimension: orders.order_date\n- filter: status = 'completed'",
    },
    {
        "concept": "profit",
        "text": "Profit:\n- source: orders.profit\n- aggregation: SUM\n"
                "- time dimension: orders.order_date\n- filter: status = 'completed'",
    },
    {
        "concept": "customer",
        "text": "Customer:\n- source: customers table\n"
                "- related to orders through orders.customer_id = customers.customer_id",
    },
    {
        "concept": "category",
        "text": "Category:\n- source: products.category\n"
                "- related to orders through orders.product_id = products.product_id",
    },
    {
        "concept": "units_sold",
        "text": "Units sold:\n- source: orders.quantity\n- aggregation: SUM",
    },
]


@dataclass
class RagDocument:
    doc_id: str
    kind: str          # schema | relationship | semantic | analytical
    text: str


def build_documents(tables: list[TableMeta], include_demo_semantics: bool = True) -> list[RagDocument]:
    """
    include_demo_semantics=False skips SEMANTIC_NOTES/ANALYTICAL_CONCEPTS —
    both are hand-authored for the bundled e-commerce demo schema and would
    be actively misleading if injected into RAG context for a different
    connected database (e.g. "exclude cancelled orders" makes no sense for a
    healthcare or logs schema). Schema and relationship documents are always
    built from the live schema, so they're correct for any database.
    """
    docs: list[RagDocument] = []

    # 1. Schema knowledge — one document per table
    for t in tables:
        col_lines = "\n".join(
            f"- {c.name} ({c.type}){' [primary key]' if c.primary_key else ''}"
            for c in t.columns
        )
        text_block = (
            f"Table: {t.table}\n"
            f"Purpose: {t.description or 'no description available'}\n"
            f"Row count: {t.row_count}\n"
            f"Columns:\n{col_lines}"
        )
        docs.append(RagDocument(doc_id=f"schema:{t.table}", kind="schema", text=text_block))

    # 2. Relationship knowledge
    for t in tables:
        for fk in t.foreign_keys:
            text_block = f"{t.table}.{fk.column} -> {fk.ref_table}.{fk.ref_column}"
            docs.append(RagDocument(
                doc_id=f"relationship:{t.table}.{fk.column}",
                kind="relationship",
                text=text_block,
            ))

    if include_demo_semantics:
        # 3. Semantic knowledge — business definitions
        for i, note in enumerate(SEMANTIC_NOTES):
            docs.append(RagDocument(doc_id=f"semantic:{i}", kind="semantic", text=note))

        # 4. Analytical knowledge — metric definitions
        for concept in ANALYTICAL_CONCEPTS:
            docs.append(RagDocument(
                doc_id=f"analytical:{concept['concept']}",
                kind="analytical",
                text=concept["text"],
            ))

    return docs
