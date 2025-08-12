import re


VAT_PATTERNS = [
    r"[A-HJNP-SUVW]\d{7}[0-9A-J]",  # CIF
    r"\d{8}[A-Z]",  # NIF
    r"[XYZ]\d{7}[A-Z]",  # NIE
    r"[A-Z]{2}[A-Z0-9]{8,12}",  # EU VAT (ES..., FR..., etc.)
    r"[A-Z0-9]{9,12}",  # fallback conservador
]
VAT_REGEX = re.compile(r"\b(?:" + "|".join(VAT_PATTERNS) + r")\b", re.IGNORECASE)


# ===== JSON Schema de salida para OpenAI =====
PARTNER_JSON_SCHEMA = {
    "name": "vendor_partner_vat",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "partner_name": {"type": "string"},
            "partner_tax_it": {"type": "string"},
        },
        "required": ["partner_name", "partner_tax_it"],
    },
}

PROMPT_VENDOR = (
    "Eres un extractor ESTRICTO de FACTURAS. Debes identificar únicamente al "
    "PROVEEDOR/EMISOR (seller/vendor/issuer), NO al cliente (buyer/bill-to/ship-to), "
    "NI a transportistas/logística, bancos, IBAN, pie legal o condiciones.\n\n"
    "REGLAS CLAVE:\n"
    "1) Devuelve exclusivamente el NOMBRE LEGAL del proveedor/emisor y su CIF/NIF/VAT.\n"
    "2) Prioriza membrete/encabezado y bloques de datos del emisor. Ignora 'Observaciones' (p. ej., transportistas).\n"
    "3) Si hay múltiples NIF/CIF, elige el asociado al emisor. No uses el del cliente ni terceros.\n"
    "4) Normaliza el VAT sin espacios ni guiones (puede tener prefijo país, p. ej. ESB60380540).\n"
    "5) Responde SOLO en JSON siguiendo el esquema pedido (sin texto extra).\n"
)
