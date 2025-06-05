# factory.py
from app.core.enums import UploadersEnum
from .base import FileUploader
from .dropbox import DropboxUploader

UPLOADER_REGISTRY = {
    UploadersEnum.DROPBOX: DropboxUploader,
}


def get_uploader(name: UploadersEnum) -> FileUploader:
    uploader_cls = UPLOADER_REGISTRY.get(name)
    if not uploader_cls:
        raise ValueError(f"Unknown uploader: {name}")
    return uploader_cls()
