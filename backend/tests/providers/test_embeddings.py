from app.providers.embeddings.fake import FakeEmbeddingProvider


def test_fake_embeddings_are_deterministic() -> None:
    provider = FakeEmbeddingProvider(dimension=2560)
    a = provider.embed(["hello"])[0]
    b = provider.embed(["hello"])[0]
    assert a == b
    assert len(a) == 2560


def test_fake_embeddings_are_normalized() -> None:
    provider = FakeEmbeddingProvider(dimension=2560)
    vector = provider.embed(["hello"])[0]
    norm = sum(v * v for v in vector) ** 0.5
    assert round(norm, 5) == 1.0


def test_different_inputs_yield_different_embeddings() -> None:
    provider = FakeEmbeddingProvider(dimension=2560)
    a = provider.embed(["hello"])[0]
    b = provider.embed(["world"])[0]
    assert a != b
