from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request

# Multilingual model suitable for the Vietnamese corpora used in this Lab.

# The local backend remains optional; required checkpoints use MockEmbedder.
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._backend_name = model_name

    def __call__(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        results = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.embeddings.create(model=self.model_name, input=batch)
                results.extend([[float(v) for v in item.embedding] for item in response.data])
            except Exception:
                payload = json.dumps({"model": self.model_name, "input": batch}).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    data=payload,
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    body = json.loads(response.read().decode("utf-8"))
                    sorted_data = sorted(body["data"], key=lambda x: x["index"])
                    results.extend([[float(v) for v in item["embedding"]] for item in sorted_data])
        return results




class HuggingFaceEmbedder:
    """Hugging Face API-backed embedder using huggingface_hub InferenceClient."""

    def __init__(
        self,
        model_name: str = LOCAL_EMBEDDING_MODEL,
        token: str | None = None,
    ) -> None:
        import os
        from huggingface_hub import InferenceClient

        self.model_name = model_name
        self._backend_name = f"huggingface: {model_name}"
        api_token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.client = InferenceClient(token=api_token)
        self._cache: dict[str, list[float]] = {}

    def __call__(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        try:
            res = self.client.feature_extraction(text, model=self.model_name)
            if hasattr(res, "tolist"):
                res = res.tolist()
            if isinstance(res, list):
                if res and isinstance(res[0], list):
                    dim = len(res[0])
                    res = [sum(res[i][d] for i in range(len(res))) / len(res) for d in range(dim)]
                vec = [float(x) for x in res]
                import math
                norm = math.sqrt(sum(x * x for x in vec))
                if norm > 1e-9:
                    vec = [x / norm for x in vec]
                self._cache[text] = vec
                return vec
            vec = [float(x) for x in res]
            import math
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 1e-9:
                vec = [x / norm for x in vec]
            self._cache[text] = vec
            return vec
        except Exception as e:
            print(f"HuggingFace API embedder notice: {e}, falling back to mock embedder.")
            return _mock_embed(text)


_mock_embed = MockEmbedder()

