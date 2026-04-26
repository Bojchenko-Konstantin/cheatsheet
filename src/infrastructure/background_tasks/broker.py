from taskiq import SimpleRetryMiddleware, TaskiqEvents, TaskiqState, async_shared_broker
from taskiq_aio_pika import AioPikaBroker

from src.application.use_cases.notification import NotificationUseCase
from src.core.config import settings
from src.infrastructure.services.email_template_service import EmailTemplateService
from src.infrastructure.services.notification_service import NotiSendNotificationService

BROKER = AioPikaBroker(
    f"amqp://{settings.broker.user}:{settings.broker.password}"
    f"@{settings.broker.host}:{settings.broker.port}"
).with_middlewares(
    SimpleRetryMiddleware(default_retry_count=3),
)
async_shared_broker.default_broker(BROKER)


@BROKER.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    notification_service = NotiSendNotificationService()
    email_template_service = EmailTemplateService()
    state.notification_use_case = NotificationUseCase(
        notification_service, email_template_service
    )
