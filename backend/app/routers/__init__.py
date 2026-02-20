from fastapi import APIRouter

from . import auth, chat, knowledge


api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(knowledge.router)
api_router.include_router(chat.router)

