from abc import abstractmethod


class IOAuthService:
    @abstractmethod
    def generate_authorization_request_url(self, state: str) -> str:
        pass

    @abstractmethod
    def generate_state_value(self) -> str:
        pass

    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, str]:
        pass

    @abstractmethod
    async def aclose(self):
        pass
