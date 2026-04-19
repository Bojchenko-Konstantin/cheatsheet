from typing import Any

import httpx

from src.application.dto import EmailMessage
from src.application.exceptions import SendEmailError
from src.application.interfaces import INotificationService
from src.core.config import settings


class NotiSendNotificationService(INotificationService):
    """Implementation of notification service using NotiSend REST API."""

    def __init__(self) -> None:
        self._api_url: str = settings.notisend.api_url.rstrip("/")
        self._api_key: str = settings.notisend.api_key
        self._from_email: str = settings.notisend.from_email
        self._from_name: str | None = settings.notisend.from_name
        self._timeout: int = settings.notisend.timeout
        self._max_retries: int = settings.notisend.max_retries

        self._send_endpoint: str = f"{self._api_url}/email/messages"

        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def send_email(self, message: EmailMessage) -> None:
        """Send an email message using NotiSend API with retry logic."""
        try:
            await self._post_message_with_retry(message)
        except Exception as e:
            raise SendEmailError from e

    async def _post_message_with_retry(self, message: EmailMessage) -> None:
        """Make HTTP request to NotiSend API."""
        payload: dict[str, Any] = {
            "to": message.to,
            "subject": message.subject,
            "text": message.text,
            "from_email": self._from_email,
        }

        if self._from_name:
            payload["from_name"] = self._from_name

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response: httpx.Response = await client.post(
                self._send_endpoint,
                headers=self._headers,
                json=payload,
            )

            response.raise_for_status()
