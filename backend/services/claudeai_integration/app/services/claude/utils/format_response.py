def is_supported_file_format(filename: str) -> bool:
    """
    Verifica si el formato de archivo es soportado
    """
    supported_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in supported_extensions)


def get_media_type(filename: str) -> str:
    """
    Determina el media type basado en la extensión del archivo
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return "application/pdf"
    elif filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg"):
        return "image/jpeg"
    elif filename_lower.endswith(".png"):
        return "image/png"
    elif filename_lower.endswith(".webp"):
        return "image/webp"
    else:
        return "application/octet-stream"
