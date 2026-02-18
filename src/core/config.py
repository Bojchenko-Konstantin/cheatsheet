import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = os.getenv("ENV_FILE")


class DatabaseConfig(BaseModel):
    db_name: str
    db_user: str
    db_host: str
    db_port: int
    db_password: str
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class LoggingConfig(BaseModel):
    log_level: str = "ERROR"


class JWTConfig(BaseModel):
    access_token_expires_in: int
    refresh_token_expires_in: int
    algorithm: str
    private_key: str
    public_key: str


class RedisConfig(BaseModel):
    host: str
    port: int
    password: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(f"{BASE_DIR}/{ENV_FILE}"),
        case_sensitive=False,
        env_nested_delimiter="__",
    )
    database: DatabaseConfig
    logging: LoggingConfig = LoggingConfig()
    jwt: JWTConfig
    redis: RedisConfig


settings = Settings()  # type: ignore
