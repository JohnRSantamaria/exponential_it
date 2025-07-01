import re
import json

from fastapi import HTTPException
from pydantic import ValidationError
from openai import AsyncOpenAI

from app.core.settings import settings
from app.core.logging import logger
from app.services.openai.schemas.classification_tax_request import (
    ClasificacionRequest,
    TaxIdResponseSchema,
)

DEFAULT_TAX = {
    "tax_id_number": -1,
    "description": "Sin coincidencia clara",
}

MAX_ATTEMPTS = 2


async def classify_tax_id(payload: ClasificacionRequest) -> TaxIdResponseSchema:
    # 🔒 Verifica que la API Key esté presente
    api_key = settings.OPENAI_API_KEY

    if not api_key or api_key.strip() == "":
        logger.error("🔒 OPENAI_API_KEY no está definida o está vacía.")
        raise HTTPException(
            status_code=500,
            detail="API Key de OpenAI no configurada correctamente.",
        )
    else:
        logger.info("✅ API Key de OpenAI detectada.")

    # Filtra los impuestos por tasa
    tax_ids_candidates = [
        {"tax_id_number": item.id, "description": item.name}
        for item in payload.candidate_tax_ids
        if item.amount == payload.iva_rate
    ]

    # Convierte los productos a JSON limpio
    productos = [
        item.model_dump(mode="json", exclude_none=True) for item in payload.products
    ]

    # Arma el prompt para OpenAI
    prompt = f"""
        Tengo una factura de proveedor: {payload.provider} (NIF: {payload.nif}).

        Productos o servicios adquiridos:
        {productos}

        Se ha detectado un IVA del {payload.iva_rate}%. A continuación se listan los posibles impuestos registrados en Odoo con esa misma tasa:

        {tax_ids_candidates}

        Con base en el tipo de producto o servicio, ¿cuál es el tax_id más adecuado?
        Si no hay coincidencia clara, responde exactamente así:
        {DEFAULT_TAX}

        Responde únicamente con un objeto JSON plano, sin explicaciones, sin texto adicional, y sin bloques de código:
        {{
        "tax_id_number": "...",
        "description": "..."
        }}
    """.strip()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"🔎 Intento {attempt}: Clasificando tax_id con OpenAI")

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto contable y fiscal en clasificación de impuestos para facturas.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
            )

            content = response.choices[0].message.content.strip()

            cleaned = re.sub(
                r"^```(json)?\s*|\s*```$", "", content, flags=re.IGNORECASE
            ).strip()

            raw = json.loads(cleaned)
            logger.info(f"✅ Respuesta recibida y parseada: {raw}")
            return TaxIdResponseSchema(**raw)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"[OpenAI Parse Error] Intento {attempt} fallido: {e}")

        except Exception as e:
            logger.exception("❌ Fallo en la clasificación de tax_id")
            raise HTTPException(
                status_code=502, detail=f"Error al clasificar tax_id: {str(e)}"
            )

    raise HTTPException(
        status_code=502,
        detail="OpenAI no devolvió una respuesta válida después de 2 intentos.",
    )
