from abc import ABC, abstractmethod

from src.application.dto import EmailMessage, WelcomeEmailData


class IEmailTemplateService(ABC):
    """Email content generator interface."""

    @abstractmethod
    def generate_welcome_email(self, data: WelcomeEmailData) -> EmailMessage:
        pass
