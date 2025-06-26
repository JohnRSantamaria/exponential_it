from typing import Dict
from fastapi import UploadFile
from app.services.taggun.client import TaggunService
from app.services.taggun.exceptions import FileProcessingError


class TaggunProcess:
    def __init__(
        self,
        file: UploadFile,
        data_file: bytes,
        taggun_service: TaggunService,
    ):
        self.file = file
        self.data_file = data_file
        self.taggun_service = taggun_service

    @classmethod
    async def create(
        cls,
        file: UploadFile,
        file_content: bytes,
        taggun_service: TaggunService,
    ):
        if not file_content:
            raise FileProcessingError()

        return cls(
            file=file,
            data_file=file_content,
            taggun_service=taggun_service,
        )

    async def run_orc(self) -> Dict:
        payload = await self.taggun_service.ocr_taggun(
            content_type=self.file.content_type,
            file_content=self.data_file,
            file_name=self.file.filename,
        )

        return payload
