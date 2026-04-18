from taskiq import SimpleRetryMiddleware
from taskiq_aio_pika import AioPikaBroker

from src.core.config import settings

BROKER = AioPikaBroker(
    f"amqp://{settings.broker.user}:{settings.broker.password}"
    f"@{settings.broker.host}:{settings.broker.port}"
).with_middlewares(
    SimpleRetryMiddleware(default_retry_count=3),
)
