from typing import Any, Dict
import httpx


def _safe_json(resp: httpx.Response) -> Dict[str, Any]:
    """
    Devuelve el JSON como dict. Si no es JSON, encapsula el texto en {"detail": "..."}.
    """
    try:
        j = resp.json()
        return j if isinstance(j, dict) else {"detail": j}
    except Exception:
        return {"detail": resp.text or ""}
