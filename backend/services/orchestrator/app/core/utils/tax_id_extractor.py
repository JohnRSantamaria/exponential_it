import difflib
import re
from typing import List, Tuple
from stdnum.eu import vat as vat_validator

from app.core.exceptions import (
    MultipleCompanyTaxIdMatchesError,
    MultiplePartnerTaxIdsError,
    PartnerTaxIdNotFoundError,
    TaxIdNotFoundError,
)


class TaxIdExtractor:
    """
    Extrae identificaciones fiscales (CIF y VAT) de un texto usando expresiones regulares.
    Al instanciarla, se ejecuta automáticamente la extracción y guarda los resultados.
    También permite filtrar los válidos y deducir el identificador fiscal del proveedor.
    """

    def __init__(
        self,
        text: str,
        all_tax_ids: list[str],
        similarity_threshold: float = 0.9,
    ):
        self.text = text
        self.text_cleaned = re.sub(
            r"([A-HJ-NP-SUVW])\s?(\d{2})\s?(\d{4})\s?(\d{1,2})\b",
            r"\1\2\3\4",
            self.text,
        )
        self.similarity_threshold = similarity_threshold
        self.patterns = {
            "cif": r"[A-HJ-NP-SUVW]-?\d{7}[0-9A-J]\b(?![A-Za-z0-9])",
            "vat": r"[A-Za-z]{2}[A-Z0-9]{1}\d{7,8}\b(?![A-Za-z0-9])",
        }
        self.all_tax_ids: List[str] = all_tax_ids
        self.candidates: List[Tuple[str, str]] = self._extract_all_ids()

    @staticmethod
    def normalize_tax_id(tax_id: str) -> str:
        """
        Normaliza el identificador fiscal eliminando prefijos de país (como ES, PT, etc.)
        """
        tax_id = tax_id.strip().upper()
        return re.sub(r"^([A-Z]{2})(?=\w{8,})", "", tax_id)

    @staticmethod
    def validate_candidates(candidates: List[Tuple[str, str]]) -> List[str]:
        """
        Valida una lista de tuplas (tipo, valor) y retorna solo los identificadores válidos,
        evitando duplicados mediante normalización.
        """
        valid = []
        seen_normalized = set()

        for tipo, valor in candidates:
            valor = valor.strip().upper()

            # Normalizar para comparación
            normalized = TaxIdExtractor.normalize_tax_id(valor)

            if normalized in seen_normalized:
                continue  # Ya fue agregado un equivalente

            if tipo == "vat":
                try:
                    if vat_validator.is_valid(valor):
                        valid.append(valor)
                        seen_normalized.add(normalized)
                except Exception:
                    continue
            elif tipo == "cif":
                if TaxIdExtractor._is_valid_cif(valor):
                    valid.append(valor)
                    seen_normalized.add(normalized)

        return valid

    @staticmethod
    def _is_valid_cif(cif: str) -> bool:
        """
        Valida un CIF español según su formato y dígito de control.
        """
        cif = cif.upper()
        if not re.match(r"^[A-HJ-NP-SUVW]\d{7}[0-9A-J]$", cif):
            return False

        letters = "JABCDEFGHI"
        letter = cif[0]
        digits = cif[1:-1]
        control = cif[-1]

        suma_par = sum(int(digits[i]) for i in range(1, 7, 2))
        suma_impar = sum(
            int(c) for i in range(0, 7, 2) for c in str(int(digits[i]) * 2)
        )
        control_digit = (10 - (suma_par + suma_impar) % 10) % 10

        if letter in "KPQRSNW":
            return control == letters[control_digit]
        elif letter in "ABEH":
            return control == str(control_digit)
        return control == str(control_digit) or control == letters[control_digit]

    def _extract_all_ids(self) -> List[Tuple[str, str]]:
        """
        Extrae todas las identificaciones fiscales del texto y elimina duplicados.
        """
        ids = []
        seen = set()

        for tipo, pattern in self.patterns.items():
            matches = re.findall(pattern, self.text_cleaned)
            for match in matches:
                cleaned = match.replace("-", "")
                if cleaned not in seen:
                    ids.append((tipo, cleaned))
                    seen.add(cleaned)
        return ids

    def _are_similar(self, a: str, b: str, threshold: float = 0.9) -> bool:
        """
        Compara dos identificadores fiscales eliminando prefijos como ES, y mide su similitud.
        """
        if not a or not b:
            return False
        a_norm = self.normalize_tax_id(a)
        b_norm = self.normalize_tax_id(b)
        return difflib.SequenceMatcher(None, a_norm, b_norm).ratio() >= threshold

    def _all_similar(self, items: List[str], threshold: float = 0.9) -> bool:
        if not items:
            return False
        base = items[0]
        return all(
            self._are_similar(base, item, threshold=threshold) for item in items[1:]
        )

    def valid_tax_ids(self) -> List[str]:
        """
        Retorna solo los identificadores fiscales válidos (VAT y CIF) en una lista plana.
        """
        return self.validate_candidates(self.candidates)

    def get_company_tax_id_or_fail(self) -> str:
        """
        Retorna el único identificador fiscal del texto que coincida con alguno de self.all_tax_ids.
        Lanza un ValueError si no hay coincidencias o hay más de una.
        """
        valid_ids = self.valid_tax_ids()

        matches = [
            tax_id
            for tax_id in valid_ids
            for own_id in self.all_tax_ids
            if self._are_similar(tax_id, own_id, self.similarity_threshold)
        ]

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise TaxIdNotFoundError()

        raise MultipleCompanyTaxIdMatchesError(matches)

    def get_partner_tax_id_or_fail(self, company_vat: str) -> str:
        """
        Devuelve el identificador fiscal del proveedor (partner), excluyendo el de la empresa contratada.
        Si hay múltiples posibles pero son suficientemente similares, retorna uno.
        Lanza ValueError si no hay ninguno o si hay varios distintos.
        """
        valid_ids = self.valid_tax_ids()

        # Filtrar los que NO son de la empresa
        candidates = [
            tax_id
            for tax_id in valid_ids
            if not self._are_similar(tax_id, company_vat, self.similarity_threshold)
        ]

        if len(candidates) == 1:
            return candidates[0]

        if len(candidates) > 1:
            if self._all_similar(candidates, threshold=self.similarity_threshold):
                # Puedes retornar el más largo o más limpio
                return max(candidates, key=len)
            raise MultiplePartnerTaxIdsError(candidates)

        raise PartnerTaxIdNotFoundError()
