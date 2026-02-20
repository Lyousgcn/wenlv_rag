from typing import Iterable, List, Sequence

from ..config import get_settings

settings = get_settings()

_pymilvus_available = False

try:
    from pymilvus import (  # type: ignore[import]
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )

    _pymilvus_available = True
except Exception:
    Collection = object  # type: ignore[assignment]


_memory_store: list[dict] = []


def _ensure_connection() -> None:
    if not _pymilvus_available:
        return
    if not connections.has_connection("default"):
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )


def _ensure_collection(dim: int = 256):
    if not _pymilvus_available:
        return None
    _ensure_connection()
    collection_name = settings.MILVUS_COLLECTION
    if not utility.has_collection(collection_name):
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
            ),
            FieldSchema(name="kb_id", dtype=DataType.INT64),
            FieldSchema(name="doc_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, description="文档向量集合")
        collection = Collection(
            name=collection_name,
            schema=schema,
            using="default",
        )
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "IP",
            "params": {"nlist": 1024},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
    else:
        collection = Collection(collection_name, using="default")
    return collection


def insert_embeddings(
    kb_id: int,
    doc_id: int,
    chunk_indices: Sequence[int],
    embeddings: Sequence[Sequence[float]],
) -> None:
    if settings.TESTING or not _pymilvus_available:
        for idx, emb in zip(chunk_indices, embeddings):
            _memory_store.append(
                {
                    "kb_id": int(kb_id),
                    "doc_id": int(doc_id),
                    "chunk_index": int(idx),
                    "embedding": list(emb),
                }
            )
        return

    collection = _ensure_collection(dim=len(embeddings[0]) if embeddings else 256)
    data: List[Iterable] = [
        [kb_id] * len(chunk_indices),
        [doc_id] * len(chunk_indices),
        list(chunk_indices),
        list(embeddings),
    ]
    collection.insert(data, timeout=60)
    collection.load()


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    s = sum(x * y for x, y in zip(a, b))
    return float(s)


def search_embeddings(
    kb_ids: Sequence[int],
    query_embedding: Sequence[float],
    top_k: int = 5,
) -> list[dict]:
    if settings.TESTING or not _pymilvus_available:
        results: list[dict] = []
        for item in _memory_store:
            if kb_ids and item["kb_id"] not in kb_ids:
                continue
            score = _cosine(query_embedding, item["embedding"])
            results.append(
                {
                    "score": score,
                    "kb_id": item["kb_id"],
                    "doc_id": item["doc_id"],
                    "chunk_index": item["chunk_index"],
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    collection = _ensure_collection(dim=len(query_embedding))
    collection.load()
    expr = f"kb_id in {list(kb_ids)}" if kb_ids else ""
    search_result = collection.search(
        data=[list(query_embedding)],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 16}},
        limit=top_k,
        expr=expr or None,
        output_fields=["kb_id", "doc_id", "chunk_index"],
    )
    hits: list[dict] = []
    for hit in search_result[0]:
        hits.append(
            {
                "score": float(hit.score),
                "kb_id": int(hit.entity.get("kb_id")),
                "doc_id": int(hit.entity.get("doc_id")),
                "chunk_index": int(hit.entity.get("chunk_index")),
            }
        )
    return hits
