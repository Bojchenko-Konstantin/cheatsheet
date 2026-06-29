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
    issuer: str
    audience: list[str]


class NotificationConfig(BaseModel):
    api_url: str
    api_key: str
    from_email: str
    from_name: str | None = None
    timeout: int = 10
    max_retries: int = 3


class BrokerConfig(BaseModel):
    host: str
    vhost: str
    port: int
    management_port: int
    user: str
    password: str


class PasswordResetConfig(BaseModel):
    token_expires_in_minutes: int = 10
    frontend_url: str = "http://localhost:3000/reset-password"


class EmailTemplateConfig(BaseModel):
    token_expires_in_minutes: int = 30


class EmailVerificationConfig(BaseModel):
    token_expires_in_hours: int = 24
    frontend_url: str = "http://localhost:3000/verify-email"


class YandexOAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    callback_url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(f"{BASE_DIR}/{ENV_FILE}"),
        case_sensitive=False,
        env_nested_delimiter="__",
    )
    database: DatabaseConfig
    logging: LoggingConfig = LoggingConfig()
    jwt: JWTConfig
    notification: NotificationConfig
    broker: BrokerConfig
    password_reset: PasswordResetConfig = PasswordResetConfig()
    email_template: EmailTemplateConfig = EmailTemplateConfig()
    email_verification: EmailVerificationConfig = EmailVerificationConfig()
    yandex_oauth: YandexOAuthConfig


settings = Settings()  # type: ignore
