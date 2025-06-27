from abc import ABC, abstractmethod
from typing import List


class AccountingProvider(ABC):

    @abstractmethod
    async def create_vendor(self, payload) -> dict:
        pass

    async def create_bill(self, payload) -> dict:
        raise NotImplementedError(
            "create_bill() no está implementado para este proveedor"
        )

    async def get_all_contacts(self) -> List[dict]:
        raise NotImplementedError(
            "get_all_contacts() no está implementado para este proveedor"
        )

    async def get_all_bills(self) -> List[dict]:
        raise NotImplementedError(
            "get_all_bills() no está implementado para este proveedor"
        )

    async def attach_file_to_bill(
        self, bill_id: str, file, file_content: bytes
    ) -> dict:
        raise NotImplementedError(
            "attach_file_to_bill() no está implementado para este proveedor"
        )

    async def get_chart_of_accounts(self) -> List[dict]:
        raise NotImplementedError(
            "get_chart_of_accounts() no está implementado para este proveedor"
        )

    async def get_all_taxes(self) -> List[dict]:
        raise NotImplementedError(
            "get_all_taxes() no está implementado para este proveedor"
        )

    async def create_company(self, client_vat: str):
        raise NotImplementedError(
            "create_company() no está implementado para este proveedor"
        )
