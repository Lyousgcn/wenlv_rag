from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user
from ..db import get_db
from ..models import Document, DocumentChunk, KnowledgeBase, User
from ..schemas import (
    ChunkOut,
    ChunkUpdate,
    DocumentOut,
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
    ResponseModel,
)
from ..services.embedding import default_embedder
from ..services.file_parser import SUPPORTED_EXTENSIONS, iter_file_chunks
from ..services.milvus_client import insert_embeddings


router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.post("/bases", response_model=ResponseModel)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """创建知识库"""
    stmt = select(KnowledgeBase).where(KnowledgeBase.name == payload.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="知识库名称已存在")
    kb = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return ResponseModel(
        code=0,
        message="创建成功",
        data=KnowledgeBaseOut.from_orm(kb),
    )


@router.get("/bases", response_model=ResponseModel)
async def list_knowledge_bases(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """列出知识库"""
    stmt = select(KnowledgeBase)
    result = await db.execute(stmt)
    bases = result.scalars().all()
    return ResponseModel(
        code=0,
        message="成功",
        data=[KnowledgeBaseOut.from_orm(b) for b in bases],
    )


@router.delete("/bases/{kb_id}", response_model=ResponseModel)
async def delete_knowledge_base(
    kb_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """删除知识库（同时删除文档及向量）"""
    stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    await db.delete(kb)
    await db.commit()
    return ResponseModel(code=0, message="删除成功", data=None)


@router.post("/bases/{kb_id}/documents", response_model=ResponseModel)
async def upload_document(
    kb_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    use_hybrid: bool = False,
) -> ResponseModel:
    """上传文档并解析向量化"""
    import tempfile
    from pathlib import Path

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir) / (file.filename or "upload")
    content = await file.read()
    tmp_path.write_bytes(content)

    doc = Document(
        kb_id=kb_id,
        filename=file.filename or "upload",
        original_path=str(tmp_path),
        status="processing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    chunks_text: list[str] = []
    indices: list[int] = []
    for idx, chunk in iter_file_chunks(tmp_path, chunk_size, chunk_overlap):
        indices.append(idx)
        chunks_text.append(chunk)
        db.add(
            DocumentChunk(
                doc_id=doc.id,
                kb_id=kb_id,
                chunk_index=idx,
                content=chunk,
            )
        )
    await db.flush()

    if chunks_text:
        embeddings = default_embedder.embed_batch(chunks_text)
        insert_embeddings(
            kb_id=kb_id,
            doc_id=doc.id,
            chunk_indices=indices,
            embeddings=embeddings,
        )

    doc.status = "done"
    await db.commit()
    await db.refresh(doc)

    return ResponseModel(
        code=0,
        message="上传并解析成功",
        data=DocumentOut.from_orm(doc),
    )


@router.get("/bases/{kb_id}/documents", response_model=ResponseModel)
async def list_documents(
    kb_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """列出知识库下的文档"""
    stmt = select(Document).where(Document.kb_id == kb_id)
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return ResponseModel(
        code=0,
        message="成功",
        data=[DocumentOut.from_orm(d) for d in docs],
    )


@router.get("/documents/{doc_id}/chunks", response_model=ResponseModel)
async def list_document_chunks(
    doc_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
) -> ResponseModel:
    """分页预览文档块"""
    from sqlalchemy import func

    stmt = select(DocumentChunk).where(DocumentChunk.doc_id == doc_id)
    if keyword:
        stmt = stmt.where(DocumentChunk.content.like(f"%{keyword}%"))
    total_stmt = (
        select(func.count(DocumentChunk.id)).where(DocumentChunk.doc_id == doc_id)
    )
    result_total = await db.execute(total_stmt)
    total = int(result_total.scalar_one())

    stmt = stmt.order_by(DocumentChunk.chunk_index).offset(
        (page - 1) * page_size
    ).limit(page_size)
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    return ResponseModel(
        code=0,
        message="成功",
        data={
            "total": total,
            "items": [ChunkOut.from_orm(c) for c in chunks],
        },
    )


@router.put("/chunks/{chunk_id}", response_model=ResponseModel)
async def update_chunk(
    chunk_id: int,
    payload: ChunkUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """编辑文档块内容"""
    stmt = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
    result = await db.execute(stmt)
    chunk = result.scalar_one_or_none()
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    chunk.content = payload.content
    await db.commit()
    await db.refresh(chunk)
    return ResponseModel(
        code=0,
        message="更新成功",
        data=ChunkOut.from_orm(chunk),
    )


@router.delete("/chunks/{chunk_id}", response_model=ResponseModel)
async def delete_chunk(
    chunk_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseModel:
    """删除文档块"""
    stmt = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
    result = await db.execute(stmt)
    chunk = result.scalar_one_or_none()
    if chunk is None:
        raise HTTPException(status_code=404, detail="文档块不存在")
    await db.delete(chunk)
    await db.commit()
    return ResponseModel(code=0, message="删除成功", data=None)
