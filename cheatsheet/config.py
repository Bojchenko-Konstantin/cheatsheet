from pathlib import Path

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)",
        "uq": "uq_%(table_name)_%(column_0_N_name)",
        "ck": "ck_%(table_name)_%(constraint_name)",
        "fk": "fk_%(table_name)_%(column_0_name)s_%(referred_table_name)",
        "pk": "pk_%(table_name)",
    }


class LoggingConfig(BaseModel):
    log_level: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    db: DatabaseConfig
    logging: LoggingConfig


settings = Settings()  # type: ignore
