import hashlib
import math
import random


class FakeEmbeddingProvider:
    """Deterministic, offline-safe embedding provider for tests and local dev.

    Embeddings are generated from a hash of the input text, so identical inputs
    always return identical vectors. The vectors are unit-normalized so cosine
    similarity can be used for ranking.
    """

    def __init__(self, dimension: int = 2560):
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            norm = 1
        return [round(v / norm, 6) for v in vector]
