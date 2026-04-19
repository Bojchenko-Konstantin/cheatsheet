from abc import ABC, abstractmethod

from src.application.dto import EmailMessage


class INotificationService(ABC):
    """Notification service interface."""

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> None:
        pass
