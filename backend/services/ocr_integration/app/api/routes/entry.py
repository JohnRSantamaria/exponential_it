from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    Response,
    UploadFile,
    HTTPException,
    status,
)
from app.api.dependencies import required_service
from app.core.logging import logger
from app.core.settings import settings
from app.core.interface.provider_config import ProviderConfig
from app.services.admin.client import AdminService
from app.services.admin.schemas import UserDataSchema
from app.services.ocr.process import optical_character_recognition

router = APIRouter()


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def ocr_invoices(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    user_data: UserDataSchema = Depends(required_service([settings.SERVICE_ID])),
):
    """
    Procesa documentos OCR para usuarios autenticados mediante un JWT de Django.
    """
    raw_auth = request.headers.get("Authorization")
    if not raw_auth:
        logger.warning("Falta encabezado Authorization en la solicitud OCR")
        raise HTTPException(status_code=401, detail="Authorization header is missing")

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

    return Response(status_code=201)
