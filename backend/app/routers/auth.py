from datetime import timedelta
from typing import Annotated

from captcha.image import ImageCaptcha
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_access_token, get_password_hash, verify_password
from ..config import get_settings
from ..db import get_db
from ..models import User
from ..schemas import ResponseModel, Token, UserCreate, UserLogin, UserOut


router = APIRouter(prefix="/auth", tags=["用户与认证"])

settings = get_settings()

_captcha_store: dict[str, str] = {}


@router.get("/captcha", response_model=ResponseModel)
async def get_captcha() -> ResponseModel:
    """获取图形验证码，返回base64图片和验证码ID"""
    import base64
    import io
    import secrets
    import string

    image = ImageCaptcha(width=120, height=40)
    chars = string.digits
    code = "".join(secrets.choice(chars) for _ in range(4))
    captcha_id = secrets.token_hex(16)
    _captcha_store[captcha_id] = code

    data = image.generate(code)
    image_bytes = io.BytesIO(data.read())
    base64_str = base64.b64encode(image_bytes.getvalue()).decode("ascii")
    return ResponseModel(
        code=0,
        message="成功",
        data={"captcha_id": captcha_id, "image_base64": base64_str},
    )


@router.post("/register", response_model=ResponseModel)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResponseModel:
    """用户注册"""
    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="该账号已存在")

    user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return ResponseModel(
        code=0,
        message="注册成功",
        data=UserOut.from_orm(user),
    )


@router.post("/login", response_model=ResponseModel)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResponseModel:
    """账号密码登录"""
    if not settings.TESTING:
        if not payload.captcha_id or not payload.captcha_code:
            raise HTTPException(status_code=400, detail="验证码不能为空")
        real_code = _captcha_store.get(payload.captcha_id)
        if not real_code or real_code.lower() != payload.captcha_code.lower():
            raise HTTPException(status_code=400, detail="验证码错误或已过期")

    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="账号或密码错误")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    token = Token(access_token=access_token)
    return ResponseModel(
        code=0,
        message="登录成功",
        data={"token": token.access_token, "token_type": token.token_type},
    )
