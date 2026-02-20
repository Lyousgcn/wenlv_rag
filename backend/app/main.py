from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import api_router


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(title="文旅智能问答系统", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist_path.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(dist_path), html=True),
            name="frontend",
        )

    return app


app = create_app()

