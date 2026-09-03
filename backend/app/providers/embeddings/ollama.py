import httpx

from ...config import Settings


class OllamaEmbeddingProvider:
    """Local Ollama embedding adapter.

    Requires the configured embedding model to be pulled and Ollama to be
    reachable at `ollama_base_url`.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.ollama_embedding_model
        self.dimension = settings.embedding_dimension
        self.base_url = settings.ollama_base_url.rstrip("/")
        self._timeout = httpx.Timeout(120.0, connect=10.0)

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        with httpx.Client(timeout=self._timeout) as client:
            for text in texts:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                response.raise_for_status()
                payload = response.json()
                embedding = payload.get("embedding")
                if not isinstance(embedding, list) or len(embedding) != self.dimension:
                    dim = len(embedding) if isinstance(embedding, list) else None
                    raise RuntimeError(
                        f"Ollama returned embedding dimension {dim}, expected {self.dimension}"
                    )
                results.append(embedding)
        return results
