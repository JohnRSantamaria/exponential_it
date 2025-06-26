import asyncio
import os
import tempfile
import time
import hashlib
from pathlib import Path
from fastapi import UploadFile

from app.core.logging import logger

from app.core.schemas.enums import UploadersEnum
from app.services.taggun.schemas.taggun_models import TaggunExtractedInvoice
from app.services.upload.factory import get_uploader
from app.services.upload.secrets import SecretsService
from app.services.upload.utils.path_builder import PathBuilder


def calculate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


async def save_file_dropbox(
    file: UploadFile,
    file_content: bytes,
    taggun_data: TaggunExtractedInvoice,
    company_vat: str,
    max_retries: int = 3,
):
    file_ext = os.path.splitext(file.filename or "")[-1]
    file_hash = calculate_file_hash(file_content)
    remote_filename = f"{file_hash}{file_ext}"
    remote_path = PathBuilder().build(date=taggun_data.date)
    full_remote_path = f"{remote_path}/{remote_filename}"

    uploader_name = UploadersEnum.DROPBOX.value
    logger.debug(f"uploader_name : {uploader_name}")

    secrets_service = await SecretsService(company_vat=company_vat).load()
    credentials = secrets_service.get_dropbox_credentials()

    uploader = get_uploader(name=UploadersEnum.DROPBOX, **credentials)

    if hasattr(uploader, "exists") and await asyncio.to_thread(
        uploader.exists, full_remote_path
    ):
        logger.info(f"Archivo ya existente en {uploader_name}: {full_remote_path}")
        return {
            "status": "duplicate",
            "path_folder": remote_path.strip("/"),
            "filename": remote_filename,
        }

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            file_path = temp_dir_path / remote_filename
            file_path.write_bytes(file_content)

            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(
                        f"Subiendo archivo a {uploader_name} (intento {attempt})..."
                    )
                    await asyncio.to_thread(
                        uploader.upload,
                        str(file_path),
                        full_remote_path,
                    )
                    break
                except Exception as e:
                    logger.warning(f"Error intento {attempt}: {e}")
                    if attempt == max_retries:
                        raise RuntimeError(f"Fallo al subir archivo: {e}")
                    time.sleep(2)

        return {
            "status": "uploaded",
            "path_folder": remote_path.strip("/"),
            "filename": remote_filename,
        }

    except Exception as e:
        logger.exception("Error en el proceso de subida de archivo")
        raise RuntimeError(f"Error saving or uploading file: {e}")
