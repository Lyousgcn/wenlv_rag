from collections.abc import Sequence
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import ChatMessage, ChatSession, DocumentChunk
from .embedding import default_embedder
from .milvus_client import search_embeddings

settings = get_settings()


async def build_context_from_milvus(
    db: AsyncSession,
    kb_ids: Sequence[int],
    question: str,
    top_k: int = 5,
) -> str:
    """根据问题在Milvus中检索相似文档块并拼接上下文"""
    embedding = default_embedder.embed(question)
    hits = search_embeddings(kb_ids, embedding, top_k=top_k)
    if not hits:
        return ""
    doc_ids = {h["doc_id"] for h in hits}
    chunk_indices = {h["chunk_index"] for h in hits}
    stmt = select(DocumentChunk).where(
        DocumentChunk.doc_id.in_(doc_ids),
        DocumentChunk.chunk_index.in_(chunk_indices),
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    sorted_chunks = sorted(chunks, key=lambda c: (c.doc_id, c.chunk_index))
    return "\n\n".join(c.content for c in sorted_chunks)


async def get_chat_history(
    db: AsyncSession,
    session_id: int,
    limit_rounds: int,
) -> list[dict[str, str]]:
    """查询指定会话的历史轮次对话"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit_rounds * 2)
    )
    result = await db.execute(stmt)
    messages = list(reversed(result.scalars().all()))
    history: list[dict[str, str]] = []
    for msg in messages:
        history.append({"role": msg.role, "content": msg.content})
    return history


async def call_qwen_stream(
    question: str,
    context: str,
    history: list[dict[str, str]],
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> Any:
    """调用通义千问流式接口，返回异步流结果"""
    if settings.TESTING or not settings.QWEN_API_KEY:
        async def fake_stream():
            text = "测试环境未配置通义千问API，将返回模拟回答。"
            for ch in text:
                yield ch

        return fake_stream()

    system_prompt = (
        "你是一个专业的文旅智能客服助手，需要严格依据提供的知识库内容进行回答，"
        "优先使用知识库中的信息，不要编造。如果知识库中没有相关内容，要明确说明。"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": f"以下是与用户问题相关的知识库内容，请结合这些内容回答：\n{context}",
            }
        )
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.QWEN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.QWEN_MODEL,
        "stream": False,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }

    async def stream_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if not choices:
                return
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if not isinstance(content, str):
                return
            for ch in content:
                yield ch

    return stream_generator()


async def save_chat_messages(
    db: AsyncSession,
    session: ChatSession,
    question: str,
    answer: str,
) -> None:
    """保存一轮问答到数据库"""
    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            content=question,
        )
    )
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
        )
    )
    await db.commit()
