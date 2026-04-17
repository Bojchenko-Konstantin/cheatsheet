from abc import ABC, abstractmethod

from src.application.dto import EmailMessage


class INotificationService(ABC):
    """Abstract interface for notification service."""

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> None:
        pass
