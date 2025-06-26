import functools
import traceback
from dropbox.exceptions import ApiError, AuthError, HttpError, BadInputError


from app.core.logging import logger
from app.services.upload.expections import (
    DropboxConnectionError,
    DropboxServiceError,
    DropboxUploadError,
)


def dropbox_error_interceptor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except AuthError as e:
            logger.error(f"[DropboxAuthError] {str(e)}")
            raise DropboxConnectionError(detail="Token inválido o expirado") from e

        except BadInputError as e:
            logger.error(f"[DropboxBadInput] {str(e)}")
            raise DropboxUploadError(
                path=kwargs.get("remote_path", "desconocido"),
                detail="Parámetros inválidos",
            ) from e

        except ApiError as e:
            logger.error(f"[DropboxApiError] {str(e)}")
            raise DropboxServiceError(
                message="Error en la API de Dropbox", data={"detail": str(e)}
            ) from e

        except HttpError as e:
            logger.error(f"[DropboxHttpError] {str(e)}")
            raise DropboxConnectionError(
                detail="Error HTTP en conexión con Dropbox"
            ) from e

        except Exception as e:
            logger.error(f"[UnhandledDropboxError] {str(e)}\n{traceback.format_exc()}")
            raise DropboxServiceError(
                message="Error inesperado en Dropbox", data={"detail": str(e)}
            ) from e

    return wrapper
