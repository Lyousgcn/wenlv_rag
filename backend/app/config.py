import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """全局配置，从环境变量中读取"""

    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "12345678")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "innerQaSystem")

    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT", "19530")
    MILVUS_DATABASE: str = os.getenv("MILVUS_DATABASE", "itcast")
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "innerQA")

    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-max")
    MAX_HISTORY_ROUNDS: int = int(os.getenv("MAX_HISTORY_ROUNDS", "5"))

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
    )
    TESTING: bool = os.getenv("TESTING", "0") == "1"

    @property
    def sqlalchemy_database_uri(self) -> str:
        """构建异步SQLAlchemy连接URL"""
        if self.TESTING:
            return "sqlite+aiosqlite:///./test.db"
        return (
            "mysql+asyncmy://"
            f"{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()
