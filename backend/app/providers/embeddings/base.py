from typing import Protocol


class EmbeddingProvider(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one normalized embedding vector for each input text."""
        ...
