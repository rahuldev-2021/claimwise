import pytest

from app.modules.rag.embedding_provider import DeterministicEmbeddingProvider, EmbeddingError


def test_deterministic_dimensions_and_batch():
    provider = DeterministicEmbeddingProvider(dimension=16)
    vectors = provider.embed_documents(["brake pad", "engine noise"])
    assert len(vectors) == 2
    assert all(len(v) == 16 for v in vectors)


def test_query_matches_document_space():
    provider = DeterministicEmbeddingProvider(dimension=12)
    q = provider.embed_query("coolant leak")
    assert len(q) == 12


def test_blank_query_raises():
    provider = DeterministicEmbeddingProvider()
    with pytest.raises(EmbeddingError):
        provider.embed_query("   ")
