from fastapi import UploadFile
from app.core.settings import settings
from app.core.logging import logger
from app.core.client_provider import ProviderConfig
from app.core.lifespan import get_taggun_service
from app.services.taggun.client import TaggunService
from app.services.taggun.extractor import TaggunExtractor
from app.services.taggun.process import TaggunProcess
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice


async def extract_ocr_payload(file: UploadFile, file_content: bytes) -> dict:
    """Retorna todos los datos extraidos directamente desde Taggun"""
    taggun_service = get_taggun_service()
    logger.info(f"taggun_service : [{taggun_service}]")

    if taggun_service is None:  # 🔹 fallback para pruebas locales
        taggun_service = TaggunService(
            config=ProviderConfig(
                server_url=settings.TAGGUN_URL,
                api_key=settings.TAGGUN_APIKEY,
            )
        )

    process = await TaggunProcess.create(
        file=file, file_content=file_content, taggun_service=taggun_service
    )
    return await process.run_orc()


def extract_taggun_data(payload: dict) -> TaggunExtractedInvoice:
    TaggunExtractor(payload=payload).extrac_base_values()
