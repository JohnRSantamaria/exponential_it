import re
from typing import List, Tuple


class FiscalIdExtractor:
    """
    Extrae identificaciones fiscales (CIF y VAT) de un texto usando expresiones regulares.
    """

    def __init__(self):
        self.patterns = {
            "cif": r"[A-HJ-NP-SUVW]-?\d{7}[0-9A-J]\b(?![A-Za-z0-9])",
            "vat": r"[A-Za-z]{2}[A-Z0-9]{1}\d{7,8}\b(?![A-Za-z0-9])",
        }

    def extract_all_ids(self, text: str) -> List[Tuple[str, str]]:
        """
        Extrae todas las identificaciones fiscales encontradas, incluyendo su tipo.

        Args:
            text (str): Texto plano OCR.

        Returns:
            List[Tuple[str, str]]: Lista de tuplas (tipo, valor), sin duplicados.
        """
        ids = []
        seen = set()

        for tipo, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                cleaned = match.replace("-", "")
                if cleaned not in seen:
                    ids.append((tipo, cleaned))
                    seen.add(cleaned)

        return ids
