from typing import Annotated
from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from app.api.dependencies import required_service

from app.core.logger import configure_logging
from app.core.settings import settings
from app.core.interface.provider_config import ProviderConfig

from app.services.admin.client import AdminService
from app.services.admin.schemas import UserDataSchema
from app.services.ocr.process import optical_character_recognition


logger = configure_logging()
router = APIRouter()


@router.post("/invoices")
async def ocr_invoices(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema = Depends(required_service([settings.SERVICE_ID])),
):
    """
    Esta ruta procesa documentos OCR solo si el usuario está autenticado correctamente con un JWT emitido por Django.
    """

    logger.info("Proceso de Optical Character Recognition (OCR) iniciado.")

    raw_auth = request.headers.get("Authorization")

    admin_service = AdminService(
        config=ProviderConfig(
            server_url=settings.URL_ADMIN,
            token=raw_auth,
        )
    )

    await optical_character_recognition(
        file=file,
        user_data=user_data,
        admin_service=admin_service,
    )

    logger.info("Proceso de Optical Character Recognition (OCR) finalizado con éxito.")
    return Response(status_code=201)
