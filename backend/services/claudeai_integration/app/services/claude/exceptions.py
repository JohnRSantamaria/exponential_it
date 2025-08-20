# exceptions/invoice_exceptions.py
from exponential_core.exceptions import CustomAppException


class APIKeyNotConfiguredException(CustomAppException):
    """Excepción cuando la API key de Anthropic no está configurada"""

    def __init__(
        self, message: str = "API Key de ClaudeAI no configurada correctamente"
    ):
        super().__init__(
            message=message, data={"error_type": "api_key_missing"}, status_code=500
        )


class UnsupportedFileFormatException(CustomAppException):
    """Excepción cuando el formato de archivo no es soportado"""

    def __init__(self, filename: str):
        supported_formats = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
        message = f"El archivo '{filename}' no es compatible. Formatos soportados: {', '.join(supported_formats)}"
        super().__init__(
            message=message,
            data={
                "error_type": "unsupported_format",
                "filename": filename,
                "supported_formats": supported_formats,
            },
            status_code=400,
        )


class FileProcessingException(CustomAppException):
    """Excepción general para errores de procesamiento de archivos"""

    def __init__(self, filename: str, stage: str, original_error: str = None):
        message = f"Error procesando '{filename}' en etapa '{stage}'"
        if original_error:
            message += f": {original_error}"

        super().__init__(
            message=message,
            data={
                "error_type": "file_processing_error",
                "filename": filename,
                "stage": stage,
                "original_error": original_error,
            },
            status_code=500,
        )


class AnthropicAPIException(CustomAppException):
    """Excepción para errores de la API de Anthropic"""

    def __init__(self, error_message: str, filename: str = None):
        # Mapear errores comunes a mensajes user-friendly
        if "max_tokens" in error_message and "maximum allowed" in error_message:
            user_message = "El documento es muy extenso para procesar. Intente con un archivo más pequeño."
            error_type = "document_too_large"
        elif "rate_limit" in error_message:
            user_message = "Se ha excedido el límite de solicitudes. Intente nuevamente en unos momentos."
            error_type = "rate_limit_exceeded"
        else:
            user_message = f"Error de la API de Claude: {error_message}"
            error_type = "api_error"

        super().__init__(
            message=user_message,
            data={
                "error_type": error_type,
                "original_error": error_message,
                "filename": filename,
            },
            status_code=500,
        )


class JSONParsingException(CustomAppException):
    """Excepción cuando hay error al parsear la respuesta JSON"""

    def __init__(self, filename: str, json_error: str):
        message = f"Error al procesar la respuesta para '{filename}': {json_error}"

        super().__init__(
            message=message,
            data={
                "error_type": "json_parsing_error",
                "filename": filename,
                "json_error": json_error,
            },
            status_code=500,
        )


class InvalidInvoiceException(CustomAppException):
    """Excepción cuando la factura extraída es inválida o incompleta"""

    def __init__(self, filename: str, reason: str, items_count: int = 0):
        message = f"Factura '{filename}' inválida: {reason}"

        super().__init__(
            message=message,
            data={
                "error_type": "invalid_invoice",
                "filename": filename,
                "reason": reason,
                "items_extracted": items_count,
            },
            status_code=422,
        )
