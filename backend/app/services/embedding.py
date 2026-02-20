import hashlib
from typing import Iterable, List


class SimpleChineseEmbedder:
    """简单的中文文本向量化工具，用于示例和测试环境"""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _hash_token(self, token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self.dim

    def embed(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim
        vec = [0.0] * self.dim
        for ch in text:
            idx = self._hash_token(ch)
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]

    def embed_batch(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


default_embedder = SimpleChineseEmbedder()

