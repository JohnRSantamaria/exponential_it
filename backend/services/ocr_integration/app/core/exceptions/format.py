from datetime import datetime, timezone


def format_error_response(
    message: str,
    error_type: str,
    status_code: int,
):
    return {
        "detail": message,
        "error_type": error_type,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
