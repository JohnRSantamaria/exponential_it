import httpx
from typing import Optional
from fastapi import UploadFile

from exponential_core.exceptions import CustomAppException
from exponential_core.cluadeai import InvoiceResponseSchema

from app.core.logging import logger
from app.core.settings import settings
from app.core.client_provider import ProviderConfig
from app.services.claudeai.utils.safe_json import _safe_json


class ClaudeAIService:
    def __init__(self, config: ProviderConfig):
        self.path = config.path
        self.timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT_CONNECT,
            read=120.0,
            write=settings.HTTP_TIMEOUT_WRITE,
            pool=settings.HTTP_TIMEOUT_POOL,
        )

    async def extract_claude_invoce(
        self,
        file: UploadFile,
        file_content: Optional[bytes] = None,
    ) -> InvoiceResponseSchema:
        """
        Llama a /line-items del microservicio de Claude:
        """
        url = f"{self.path}/line-items"
        logger.debug(f"POST {url} (extract line items)")

        content = file_content or await file.read()
        ctype = file.content_type or "application/octet-stream"
        fname = (file.filename or "upload").strip() or "upload"

        files = {"file": (fname, content, ctype)}

        # --- Llamada HTTP ---
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url=url, files=files)
        except httpx.RequestError as err:
            # Red/timeout/DNS/etc.
            raise CustomAppException(
                message="No se pudo contactar el extractor.",
                data={"reason": str(err), "url": url},
                status_code=503,
            ) from err

        # --- Manejo de errores HTTP ---
        if resp.status_code >= 400:
            payload = _safe_json(resp)
            detail = payload.get("detail", payload)
            if isinstance(detail, dict):
                message = (detail.get("message") or "").strip() or (
                    resp.text or "Error"
                ).strip()
                data = detail.get("data") or {}
            else:
                message = (str(detail) or resp.text or "Error").strip()
                data = {}
            raise CustomAppException(
                message=message, data=data, status_code=resp.status_code
            )

        payload = _safe_json(resp)
        try:
            return InvoiceResponseSchema.model_validate(payload)
        except Exception as ve:
            raise CustomAppException(
                message="Respuesta del extractor no coincide con el esquema.",
                data={"validation_error": str(ve), "raw": payload},
                status_code=422,
            )
