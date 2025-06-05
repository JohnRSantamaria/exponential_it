from typing import List
from app.utils.comparator import are_similar, all_similar


class TaxIdValidator:
    def __init__(self, expected_cif: str, similarity_threshold: float = 0.9):
        self.expected_cif = expected_cif
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def extract_text_from_payload(payload: dict) -> str:
        """Extrae texto OCR de un payload."""
        return payload.get("text", {}).get("text", "")

    def get_supplier_tax_id(self, found_ids: List[str]) -> str:
        """
        Devuelve la identificación fiscal del proveedor, si es posible determinarla.
        """
        filtered = [
            tax_id
            for tax_id in found_ids
            if not are_similar(tax_id, self.expected_cif, self.similarity_threshold)
        ]

        if len(filtered) == 1:
            return filtered[0]

        if len(filtered) > 1 and all_similar(filtered, self.similarity_threshold):
            return max(filtered, key=len)

        return ""
