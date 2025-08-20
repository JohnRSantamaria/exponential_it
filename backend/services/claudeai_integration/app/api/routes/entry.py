from fastapi import APIRouter, File, HTTPException, UploadFile
from app.core.logging import logger
from exponential_core.exceptions import CustomAppException

from app.services.claude.client import invoice_formater
from exponential_core.cluadeai import InvoiceResponseSchema

router = APIRouter()


from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.core.logging import logger

from exponential_core.exceptions import CustomAppException
from exponential_core.cluadeai import InvoiceResponseSchema

from app.services.claude.client import invoice_formater
from app.services.claude.exceptions import (
    APIKeyNotConfiguredException,
    UnsupportedFileFormatException,
    FileProcessingException,
    AnthropicAPIException,
    JSONParsingException,
    InvalidInvoiceException,
)

router = APIRouter()


@router.post("/line-items", response_model=InvoiceResponseSchema)
async def extract_invoice_items(file: UploadFile = File(...)):
    """
    Endpoint para extraer elementos de línea de una factura (PDF o imagen)
    """
    try:
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided",
            )

        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
        fname = (file.filename or "").lower()
        if not any(fname.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File '{file.filename}' must be PDF or image (JPG, PNG, WEBP)",
            )

        logger.info(f"🚀 Processing file: {file.filename}")
        return await invoice_formater(file)

    except APIKeyNotConfiguredException as e:
        logger.error(f"🔒 API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Claude API key is not configured",
        )

    except UnsupportedFileFormatException as e:
        logger.warning(f"🛑 Unsupported file format: {e}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )

    except FileProcessingException as e:
        logger.error(
            f"📄 File processing error [{getattr(e, 'stage', 'unknown')}]: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File processing error: {str(e)}",
        )

    except AnthropicAPIException as e:
        logger.error(f"🤖 Anthropic API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream AI provider error: {str(e)}",
        )

    except JSONParsingException as e:
        logger.error(f"🧩 JSON parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON returned by extractor: {str(e)}",
        )

    except InvalidInvoiceException as e:
        logger.warning(f"⚠️ Invalid invoice structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid invoice structure: {str(e)}",
        )

    except CustomAppException as e:
        logger.error(f"❌ App error: {e.message}")
        raise HTTPException(
            status_code=getattr(
                e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=e.message,
        )

    except Exception as e:
        logger.exception("❌ Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
