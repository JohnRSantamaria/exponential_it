# factory.py

from .base import FileUploader
from .dropbox import DropboxUploader
from app.core.schemas.enums import UploadersEnum

UPLOADER_REGISTRY = {
    UploadersEnum.DROPBOX: DropboxUploader,
}


def get_uploader(name: UploadersEnum, **kwargs) -> FileUploader:
    uploader_cls = UPLOADER_REGISTRY.get(name)
    if not uploader_cls:
        raise ValueError(f"Unknown uploader: {name}")
    return uploader_cls(**kwargs)
