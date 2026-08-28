"""Pluggable text embedding providers.

The active provider is chosen by ``APP_EMBEDDING_PROVIDER``:

- ``local``  – sentence-transformers, multilingual, 384 dims, no API key (default)
- ``openai`` – OpenAI ``text-embedding-3-small``, 1536 dims, needs ``APP_OPENAI_API_KEY``
- ``fake``   – deterministic hashing vectorizer, no dependencies (used in tests)

Every provider's ``dim`` must match ``EMBEDDING_DIM`` (the ``embedding`` column
size). ``get_embedder()`` enforces that.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from abc import ABC, abstractmethod
from functools import lru_cache

from realestate_rag_agent.core.config import get_settings
from realestate_rag_agent.repositories.models import EMBEDDING_DIM

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    norm = unicodedata.normalize("NFKD", text.lower())
    norm = norm.encode("ascii", "ignore").decode("ascii")
    return _TOKEN_RE.findall(norm)


class Embedder(ABC):
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class FakeEmbedder(Embedder):
    """Deterministic bag-of-words hashing vectorizer.

    Not semantic, but text sharing words maps to nearby vectors, which is enough
    to test the search wiring without a model.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _tokenize(text):
            digest = hashlib.md5(token.encode()).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        get_dim = getattr(
            self._model,
            "get_embedding_dimension",
            self._model.get_sentence_embedding_dimension,
        )
        self.dim = get_dim()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return vectors.tolist()


class OpenAIEmbedder(Embedder):
    _DIMS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}

    def __init__(self, model_name: str, api_key: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model_name
        self.dim = self._DIMS.get(model_name, EMBEDDING_DIM)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in resp.data]


@lru_cache
def get_embedder() -> Embedder:
    settings = get_settings()
    provider = settings.embedding_provider

    if provider == "fake":
        embedder: Embedder = FakeEmbedder()
    elif provider == "local":
        embedder = SentenceTransformerEmbedder(settings.embedding_model_local)
    elif provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("APP_OPENAI_API_KEY is required for embedding_provider=openai")
        embedder = OpenAIEmbedder(settings.embedding_model_openai, settings.openai_api_key)
    else:  # pragma: no cover - guarded by Literal
        raise RuntimeError(f"unknown embedding provider: {provider}")

    if embedder.dim != EMBEDDING_DIM:
        raise RuntimeError(
            f"embedding provider {provider!r} produces {embedder.dim}-dim vectors "
            f"but the database column is {EMBEDDING_DIM}-dim; run a migration to change it"
        )
    return embedder


def embedding_text(title: str, description: str) -> str:
    """Canonical text that represents a property for embedding."""
    return f"{title}. {description}".strip()
