from abc import ABC, abstractmethod


class CreateProvider(ABC):
    @abstractmethod
    async def register_company(client_vat: str):
        pass
