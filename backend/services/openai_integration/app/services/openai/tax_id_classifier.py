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
    api_key = settings.OPENAI_API_KEY

    if not api_key or api_key.strip() == "":
        logger.error("🔒 OPENAI_API_KEY no está definida o está vacía.")
        raise HTTPException(
            status_code=500,
            detail="API Key de OpenAI no configurada correctamente.",
        )

    logger.info("✅ API Key de OpenAI detectada.")

    tax_ids_candidates = [
        {"tax_id_number": item.id, "description": item.name}
        for item in payload.candidate_tax_ids
        if item.amount == payload.iva_rate
    ]

    productos = [
        item.model_dump(mode="json", exclude_none=True) for item in payload.products
    ]

    prompt = f"""
        Tengo una factura de proveedor: {payload.provider} (NIF: {payload.nif}).

        Productos o servicios adquiridos:
        {productos}

        Se ha detectado un IVA del {payload.iva_rate}%. A continuación se listan los posibles impuestos registrados en Odoo con **esa misma tasa exacta**:

        {tax_ids_candidates}

        Tu tarea es seleccionar el `tax_id_number` más adecuado basándote únicamente en el tipo de producto o servicio.

        ⚠️ IMPORTANTE:
        - **Nunca** devuelvas la opción por defecto (`{DEFAULT_TAX}`) si hay al menos un impuesto en la lista. 
        - Si no estás seguro, **elige el impuesto más general o que aplique a la mayoría de los productos** con esa tasa.
        - Solo devuelve `{DEFAULT_TAX}` si la lista está completamente vacía o no hay ningún impuesto del {payload.iva_rate}% disponible.

        Responde únicamente con un objeto JSON plano, sin explicaciones, sin texto adicional, y sin bloques de código:

        {{
        "tax_id_number": "...",
        "description": "..."
        }}
        """.strip()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"🔎 Intento {attempt}: Clasificando tax_id con OpenAI")

            client = AsyncOpenAI(api_key=api_key)

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

            # Reintenta si es DEFAULT_TAX
            if (
                raw.get("tax_id_number") == DEFAULT_TAX["tax_id_number"]
                and raw.get("description") == DEFAULT_TAX["description"]
                and attempt < MAX_ATTEMPTS
            ):
                logger.warning("🚫 Se recibió DEFAULT_TAX, reintentando...")
                continue

            return TaxIdResponseSchema(**raw)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"[OpenAI Parse Error] Intento {attempt} fallido: {e}")
            if attempt < MAX_ATTEMPTS:
                continue  # Reintenta si aún quedan intentos

        except Exception as e:
            logger.exception("❌ Fallo en la clasificación de tax_id")
            raise HTTPException(
                status_code=502, detail=f"Error al clasificar tax_id: {str(e)}"
            )

    raise HTTPException(
        status_code=502,
        detail="OpenAI no devolvió una respuesta válida después de 2 intentos.",
    )
