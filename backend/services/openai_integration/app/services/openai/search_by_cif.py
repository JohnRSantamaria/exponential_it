import re
import json

from fastapi import HTTPException
from openai import AsyncOpenAI
from app.core.settings import settings
from app.core.logging import logger

DEFAULT_CIF = {"CIF": "0"}
MAX_ATTEMPTS = 2


async def search_cif_by_partner(partner_name: str) -> dict:
    # Verifica API Key
    api_key = settings.OPENAI_API_KEY
    if not api_key or api_key.strip() == "":
        logger.error("🔒 OPENAI_API_KEY no está definida o está vacía.")
        raise HTTPException(
            status_code=500,
            detail="API Key de OpenAI no configurada correctamente.",
        )

    logger.info("✅ API Key de OpenAI detectada.")

    # Prompt para OpenAI
    prompt = f"""
        Dado el nombre de la empresa: "{partner_name}"

        Busca el CIF español asociado a esta empresa.
        Si no puedes encontrarlo, responde exactamente así:
        {DEFAULT_CIF}

        Responde únicamente con un objeto JSON plano, sin texto adicional ni bloques de código:
        {{
        "CIF": "..."
        }}
    """.strip()

    client = AsyncOpenAI(api_key=api_key)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(
                f"🔎 Intento {attempt}: Buscando CIF con OpenAI para {partner_name}"
            )

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en datos empresariales españoles.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=100,
            )

            content = response.choices[0].message.content.strip()
            cleaned = re.sub(
                r"^```(json)?\s*|\s*```$", "", content, flags=re.IGNORECASE
            ).strip()
            raw = json.loads(cleaned)

            # Si no devuelve el campo esperado, usar DEFAULT_CIF
            if "CIF" not in raw or not raw["CIF"]:
                logger.warning("⚠️ Respuesta sin CIF válido, usando valor por defecto.")
                return DEFAULT_CIF

            logger.info(f"✅ CIF encontrado: {raw}")
            return raw

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[OpenAI Parse Error] Intento {attempt} fallido: {e}")

        except Exception as e:
            logger.exception("❌ Error inesperado al buscar CIF")
            raise HTTPException(
                status_code=502, detail=f"Error al buscar CIF: {str(e)}"
            )

    return DEFAULT_CIF
