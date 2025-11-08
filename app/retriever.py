# app/retriever.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple
from collections import defaultdict

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

def _doc_key(doc: Document) -> Tuple[str, str]:
    meta = doc.metadata or {}
    return (str(meta.get("doc_id") or meta.get("url") or ""), doc.page_content)

def rrf_merge(
    s_docs: Iterable[Document],
    d_docs: Iterable[Document],
    *,
    k: int = 8,
    k_rrf: int = 60,
    weights: Tuple[float, float] = (0.4, 0.6),
) -> List[Document]:
    w_s, w_d = weights
    scores: Dict[Tuple[str, str], float] = defaultdict(float)
    keep: Dict[Tuple[str, str], Document] = {}

    for r, doc in enumerate(list(s_docs)[:k], start=1):
        key = _doc_key(doc)
        keep[key] = doc
        scores[key] += w_s * (1.0 / (k_rrf + r))

    for r, doc in enumerate(list(d_docs)[:k], start=1):
        key = _doc_key(doc)
        keep.setdefault(key, doc)
        scores[key] += w_d * (1.0 / (k_rrf + r))

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], len(kv[0][1])))
    return [keep[key] for key, _ in ranked]

class SimpleHybridRetriever(BaseRetriever):
    k: int = 8
    k_rrf: int = 60
    weights: Tuple[float, float] = (0.4, 0.6)
    sparse: Any
    dense: Any

    class Config:
        arbitrary_types_allowed = True

    # LangChain calls this internally when you do .invoke() or get_relevant_documents()
    def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> List[Document]:
        s_docs: List[Document] = list(self.sparse.invoke(query))[: self.k]
        d_docs: List[Document] = list(self.dense.invoke(query))[: self.k]
        return rrf_merge(s_docs, d_docs, k=self.k, k_rrf=self.k_rrf, weights=self.weights)

def build_hybrid_retriever(chunks: List[Dict[str, Any]]) -> SimpleHybridRetriever:
    docs = [Document(page_content=c["text"], metadata=c.get("meta", {})) for c in chunks]
    bm25 = BM25Retriever.from_documents(docs)
    embeddings = OpenAIEmbeddings()
    faiss = FAISS.from_documents(docs, embeddings).as_retriever(search_kwargs={"k": 8})
    return SimpleHybridRetriever(sparse=bm25, dense=faiss, k=8, k_rrf=60, weights=(0.4, 0.6))
