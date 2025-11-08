# Copyright Lukas Licon 2025. All Rights Reserved.

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.ensemble import EnsembleRetriever

def build_hybrid_retriever(chunks: list[dict]):
    docs = [Document(page_content=c["text"], metadata=c["meta"]) for c in chunks]
    bm25 = BM25Retriever.from_documents(docs)            # sparse
    faiss = FAISS.from_documents(docs, OpenAIEmbeddings()).as_retriever(search_kwargs={"k":8})  # dense
    hybrid = EnsembleRetriever(retrievers=[bm25, faiss], weights=[0.4, 0.6])
    return hybrid