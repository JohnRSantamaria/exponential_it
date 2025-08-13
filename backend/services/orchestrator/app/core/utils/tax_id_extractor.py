import difflib
import re
from typing import List, Tuple
from stdnum.eu import vat as vat_validator
from app.core.logging import logger
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
            r"\b([A-HJ-NP-SUVW])\s?(\d{1,2})\s?(\d{3})\s?(\d{3})([0-9A-J])\b",
            r"\1\2\3\4\5",
            self.text,
        )
        self.similarity_threshold = similarity_threshold
        self.patterns = {
            "cif": r"[A-HJ-NP-SUVW]-?\d{7}[0-9A-J]\b(?![A-Za-z0-9])",
            "cif2": r"[A-HJ-NP-SUVW](?:-| )?(?:\d{8}|\d{2}\.?\d{3}\.?\d{3})",
            # VAT: no aplica puntos de miles ni guiones, se deja igual
            "vat": r"[A-Za-z]{2}[A-Z0-9]{1}\d{7,8}\b(?![A-Za-z0-9])",
            # NIF: ya soporta puntos y guion opcional antes de la letra de control
            "nif": r"(?:\d{8}|\d{1,2}\.?\d{3}\.?\d{3})(?:-)?[TRWAGMYFPDXBNJZSQVHLCKE]\b(?![A-Za-z0-9])",
            # DIG: ahora soporta formato XX.XXX.XXX o 8 dígitos
            "dig": r"(?<!\d)(?:\d{8}|\d{1,2}\.?\d{3}\.?\d{3})(?!\d)",
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

            normalized = TaxIdExtractor.normalize_tax_id(valor)

            if normalized in seen_normalized:
                continue

            if tipo == "vat":
                try:
                    if vat_validator.is_valid(valor):
                        valid.append(valor)
                        seen_normalized.add(normalized)
                except Exception:
                    continue
            elif tipo == "cif" or tipo == "cif2":
                if TaxIdExtractor._is_valid_cif(valor):
                    valid.append(valor)
                    seen_normalized.add(normalized)

            elif tipo == "dig":
                if TaxIdExtractor._is_valid_numeric_cif(valor):
                    valid.append(valor)
                    seen_normalized.add(normalized)
                else:
                    logger.warning(f"{valor} NO es un CIF numérico válido")
            elif tipo == "nif":
                if TaxIdExtractor._is_valid_nif(valor):
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

    @staticmethod
    def _is_valid_nif(nif: str) -> bool:
        """
        Valida un NIF español de persona física (DNI con letra de control).
        """
        nif = nif.upper().replace(".", "").replace("-", "")

        # Debe ser 8 dígitos seguidos de una letra válida
        if not re.match(r"^\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]$", nif):
            return False

        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        numero = int(nif[:8])
        letra_control = nif[-1]

        return letras[numero % 23] == letra_control

    @staticmethod
    def _is_valid_numeric_cif(number: str) -> bool:
        """
        Valida un CIF que contiene solo 8 dígitos (sin letra inicial ni final),
        aplicando la lógica estándar de dígito de control de CIF.
        """
        if not re.match(r"^\d{8}$", number):
            return False

        digits = number[:7]
        control = number[-1]

        # Cálculo del dígito de control
        suma_par = sum(int(digits[i]) for i in range(1, 7, 2))
        suma_impar = sum(
            int(c) for i in range(0, 7, 2) for c in str(int(digits[i]) * 2)
        )
        control_digit = (10 - (suma_par + suma_impar) % 10) % 10

        return control == str(control_digit)

    def _extract_all_ids(self) -> List[Tuple[str, str]]:
        """
        Extrae todas las identificaciones fiscales del texto y elimina duplicados.
        """
        ids = []
        seen = set()

        for tipo, pattern in self.patterns.items():
            matches = re.findall(pattern, self.text_cleaned)
            for match in matches:
                cleaned = match.replace("-", "").replace(".", "")
                if cleaned not in seen:
                    ids.append((tipo, cleaned))
                    seen.add(cleaned)
        return ids

    def _are_similar(self, a: str, b: str, threshold: float = 0.9) -> bool:
        """
        Compara dos identificadores fiscales eliminando prefijos como ES, y mide su similitud.
        Imprime el valor de la similitud para depuración.
        """
        if not a or not b:
            return False

        a_norm = self.normalize_tax_id(a)
        b_norm = self.normalize_tax_id(b)

        similarity = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
        return similarity >= threshold

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

        matches = []
        for tax_id in valid_ids:
            for own_id in self.all_tax_ids:
                if self._are_similar(tax_id, own_id, self.similarity_threshold):
                    if not any(
                        self._are_similar(tax_id, m, self.similarity_threshold)
                        for m in matches
                    ):
                        matches.append(tax_id)
                    break

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise TaxIdNotFoundError()

        raise MultipleCompanyTaxIdMatchesError(matches)

    def get_partner_tax_id_or_fail(
        self,
        company_vat: str,
    ) -> str | list:
        """
        Devuelve el identificador fiscal del proveedor (partner), excluyendo el de la empresa contratada.
        Si hay múltiples posibles pero son variantes similares, retorna el más completo.
        Lanza MultiplePartnerTaxIdsError si hay varios distintos.
        Lanza PartnerTaxIdNotFoundError si no encuentra ninguno.
        """
        valid_ids = self.valid_tax_ids()

        candidates = [
            tax_id
            for tax_id in valid_ids
            if not self._are_similar(tax_id, company_vat, self.similarity_threshold)
        ]

        matches = []
        for tax_id in candidates:
            if not any(
                self._are_similar(tax_id, m, self.similarity_threshold) for m in matches
            ):
                matches.append(tax_id)

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise PartnerTaxIdNotFoundError()

        # ✅ Si hay múltiples, pero son similares entre sí → devolver el más largo
        if self._all_similar(matches, threshold=self.similarity_threshold):
            return max(matches, key=lambda x: (len(x), x))

        raise MultiplePartnerTaxIdsError(matches)

    def resolve_company_and_partner_vat(
        self,
        supposed_company_vat: str | None,
        supposed_partner_vat: str | None,
    ) -> tuple[str | None, str | None]:
        """
        Valida company_vat y partner_vat contra self.all_tax_ids.

        Reglas:
        - Ninguno coincide -> TaxIdNotFoundError
        - EXACTAMENTE uno coincide -> retorna los valores, haciendo swap si el que coincide fue el partner
        - Ambos coinciden -> MultipleCompanyTaxIdMatchesError
        """

        def match_in_all(tax_id: str | None) -> str | None:
            if not tax_id:
                return None
            for own_id in self.all_tax_ids:
                if self._are_similar(tax_id, own_id, self.similarity_threshold):
                    return own_id
            return None

        comp_hit = match_in_all(supposed_company_vat)
        part_hit = match_in_all(supposed_partner_vat)

        # Ninguno coincide
        if comp_hit is None and part_hit is None:
            raise TaxIdNotFoundError()

        # Solo uno coincide
        if (comp_hit is not None) ^ (part_hit is not None):
            if comp_hit is not None:
                return supposed_company_vat, supposed_partner_vat
            else:
                # el partner es quien coincide -> promover a company
                return supposed_partner_vat, supposed_company_vat

        # Ambos coinciden
        raise MultipleCompanyTaxIdMatchesError(
            matches=[supposed_company_vat or "", supposed_partner_vat or ""]
        )
