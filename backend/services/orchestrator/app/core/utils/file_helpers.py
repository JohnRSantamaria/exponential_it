from starlette.datastructures import UploadFile as StarletteUploadFile
from io import BytesIO


def recreate_upload_file(
    file_content: bytes, filename: str, content_type: str
) -> StarletteUploadFile:
    """
    Reconstruye un UploadFile a partir de contenido binario, nombre y tipo MIME.
    """
    stream = BytesIO(file_content)
    return StarletteUploadFile(
        filename=filename, file=stream, content_type=content_type
    )
