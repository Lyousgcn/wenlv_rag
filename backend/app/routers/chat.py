from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..dependencies import get_current_user
from ..models import ChatSession, User
from ..schemas import ChatRequest, ChatSessionCreate, ChatSessionOut, ResponseModel
from ..services.rag import (
    build_context_from_milvus,
    call_qwen_stream,
    get_chat_history,
    save_chat_messages,
)


router = APIRouter(prefix="/chat", tags=["对话问答"])

settings = get_settings()


@router.post("/sessions", response_model=ResponseModel)
async def create_session(
    payload: ChatSessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """创建新的对话Session"""
    session = ChatSession(user_id=current_user.id, name=payload.name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ResponseModel(
        code=0,
        message="创建成功",
        data=ChatSessionOut.from_orm(session),
    )


@router.get("/sessions", response_model=ResponseModel)
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """列出当前用户的对话Session"""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return ResponseModel(
        code=0,
        message="成功",
        data=[ChatSessionOut.from_orm(s) for s in sessions],
    )


@router.delete("/sessions/{session_id}", response_model=ResponseModel)
async def delete_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """删除对话Session"""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.delete(session)
    await db.commit()
    return ResponseModel(code=0, message="删除成功", data=None)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """流式对话接口"""
    stmt = select(ChatSession).where(
        ChatSession.id == payload.session_id,
        ChatSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    history_rounds = (
        payload.history_rounds
        if payload.history_rounds is not None
        else settings.MAX_HISTORY_ROUNDS
    )
    history = await get_chat_history(db, session.id, history_rounds)

    context = await build_context_from_milvus(db, payload.kb_ids, payload.question)
    llm_stream = await call_qwen_stream(
        question=payload.question,
        context=context,
        history=history,
        temperature=payload.temperature,
        top_p=payload.top_p,
        max_tokens=payload.max_tokens,
    )

    async def event_generator():
        answer_parts: list[str] = []
        try:
            async for token in llm_stream:
                answer_parts.append(token)
                yield f"data: {token}\n\n"
        except Exception:
            fallback = "对话服务暂时不可用，请稍后重试。"
            if not answer_parts:
                answer_parts.append(fallback)
                yield f"data: {fallback}\n\n"
        finally:
            if not answer_parts:
                answer_parts.append("暂无可用回答。")
            full_answer = "".join(answer_parts)
            await save_chat_messages(db, session, payload.question, full_answer)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
