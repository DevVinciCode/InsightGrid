"""
VectorStore interface with a dependency-light default implementation.

Why TF-IDF instead of embeddings by default: this MVP must run immediately
after `pip install` with no model download and no API key (requirement:
"clone -> install -> add API key -> run -> ask a question"). TfidfVectorStore
gives real, working semantic-ish retrieval over the schema/business documents
out of the box.

To upgrade to real embeddings later, implement the same interface:

    VectorStore
    ├── TfidfVectorStore      (default — this file)
    ├── FaissVectorStore      (swap in: sentence-transformers + faiss-cpu)
    └── ChromaVectorStore     (swap in: chromadb)

Nothing outside this module needs to change when you swap implementations —
`rag/retriever.py` only calls `.index()` and `.search()`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.rag.documents import RagDocument


class VectorStore(ABC):
    @abstractmethod
    def index(self, documents: list[RagDocument]) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[tuple[RagDocument, float]]: ...


class TfidfVectorStore(VectorStore):
    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = None
        self._documents: list[RagDocument] = []

    def index(self, documents: list[RagDocument]) -> None:
        self._documents = documents
        corpus = [d.text for d in documents]
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 5) -> list[tuple[RagDocument, float]]:
        if self._matrix is None or not self._documents:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(self._documents[i], float(scores[i])) for i in top_idx if scores[i] > 0]


def get_vector_store(kind: str = "tfidf") -> VectorStore:
    if kind == "tfidf":
        return TfidfVectorStore()
    raise ValueError(
        f"Unsupported VECTOR_STORE '{kind}'. Only 'tfidf' ships by default — "
        f"implement FaissVectorStore/ChromaVectorStore against the VectorStore "
        f"interface in this file to add one."
    )
