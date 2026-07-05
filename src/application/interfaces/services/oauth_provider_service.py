from abc import abstractmethod


class IOAuthProviderService:
    @abstractmethod
    def generate_authorization_request_url(
        self, state: str, code_challenge: str
    ) -> str:
        pass

    @abstractmethod
    async def get_access_token(self, code: str, code_verifier: str) -> str:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, str]:
        pass

    @abstractmethod
    async def aclose(self):
        pass

    @abstractmethod
    @staticmethod
    def generate_state_value() -> str:
        pass

    @abstractmethod
    @staticmethod
    def generate_pkce_pair() -> tuple[str, str]:
        pass
