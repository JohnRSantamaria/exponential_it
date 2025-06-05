import re
import json

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.logger import configure_logging
from app.services.openai.client import openai_client
from app.services.openai.schemas.account_category import AccountCategory

# Logger
logger = configure_logging()

DEFAULT_CATEGORY = {
    "account_id": "6222726000000035005",
    "account_name": "Sin categorizar",
}

MAX_ATTEMPTS = 2


async def classify_account(text: str, chart: list[dict]) -> AccountCategory:
    prompt = f"""
        Dado el siguiente texto extraído de una factura:

        \"\"\"{text}\"\"\"

        Y el siguiente listado de cuentas contables:

        \"\"\"{chart}\"\"\"

        Selecciona la cuenta contable más adecuada basándote únicamente en el texto y que esté activa ("is_active": true).
        Si no hay coincidencia clara, responde exactamente así:
        {DEFAULT_CATEGORY}

        Responde únicamente con un objeto JSON plano, sin explicaciones, sin texto adicional, y sin bloques de código:
        {{
        "account_id": "...",
        "account_name": "..."
        }}
    """

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente contable experto.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            # Limpia bloques de código ```json o ```
            cleaned = re.sub(
                r"^```(json)?\s*|\s*```$", "", content, flags=re.IGNORECASE
            ).strip()

            raw = json.loads(cleaned)
            return AccountCategory(**raw)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"[OpenAI Parse Error] Intento {attempt} fallido: {e}")

        except Exception as e:
            raise HTTPException(
                status_code=502, detail=f"Error al clasificar: {str(e)}"
            )

    raise HTTPException(
        status_code=502,
        detail="OpenAI no devolvió una respuesta válida después de 2 intentos.",
    )
