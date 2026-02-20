from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """统一接口返回结构"""

    code: int = Field(0, description="状态码，0表示成功")
    message: str = Field("成功", description="提示信息")
    data: Any | None = Field(None, description="具体数据")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str
    captcha_id: str
    captcha_code: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ChunkOut(BaseModel):
    id: int
    doc_id: int
    kb_id: int
    chunk_index: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ChunkUpdate(BaseModel):
    content: str


class ChatSessionCreate(BaseModel):
    name: str


class ChatSessionOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: int
    kb_ids: list[int] = Field(default_factory=list)
    question: str
    temperature: float = 0.8
    top_p: float = 0.8
    max_tokens: int = 1024
    history_rounds: int | None = None
