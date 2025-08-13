from decimal import Decimal
import io
from typing import Any, Optional, Set
from PIL import Image
from exponential_core.exceptions import CustomAppException
from app.services.taggun.exceptions import ImageTooSmall, UnsupportedImageFormatError


def validate_image_dimensions(
    filename: str, file_bytes: bytes, min_width=100, min_height=100
):
    """Valida que el archivo sea una imagen con dimensiones mínimas. Si es PDF, no valida."""
    ext = filename.lower().split(".")[-1]
    supported_extension = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]

    # Si es PDF, no valida dimensiones
    if ext == "pdf":
        return

    # Si el formato no está soportado, lanza excepción
    if ext not in supported_extension:
        raise UnsupportedImageFormatError(ext, supported_extension)

    # Intentar abrir la imagen
    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise CustomAppException(f"No se pudo procesar la imagen: {str(e)}")

    # Validar dimensiones
    if img.width < min_width or img.height < min_height:
        raise ImageTooSmall(img.width, img.height, min_width, min_height)


def to_tax_candidates(value: Any) -> Optional[Set[float]]:
    """
    Convierte:
      - None -> None
      - número (int/float/Decimal) -> {float(valor)}
      - iterable (set/list/tuple) de números -> {float(...), ...}
    """
    if value is None:
        return None

    # Valor único
    if isinstance(value, (int, float, Decimal)):
        return {float(value)}

    # Colección
    if isinstance(value, (set, list, tuple)):
        if not value:  # colección vacía -> None o set() si prefieres
            return None
        return {float(v) for v in value}

    # Si llega otro tipo inesperado, mejor None (o lanza error si prefieres)
    return None
