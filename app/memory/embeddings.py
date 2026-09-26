"""Embedding abstraction reserved for the RAG phase."""


def prepare_text_for_embedding(text: str) -> str:
    return " ".join(text.split())
