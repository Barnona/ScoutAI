"""Minimal FAISS wrapper for the future persistent research memory layer."""

import numpy as np
import faiss


class VectorStore:
    def __init__(self, dimension: int = 1536):
        self.index = faiss.IndexFlatL2(dimension)

    def add(self, embeddings: list[list[float]]) -> None:
        if not embeddings:
            return
        self.index.add(np.asarray(embeddings, dtype="float32"))

    def search(self, embedding: list[float], k: int = 5):
        vector = np.asarray([embedding], dtype="float32")
        return self.index.search(vector, k)
