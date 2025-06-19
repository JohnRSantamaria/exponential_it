# Seguridad: JWT, OAuth2, scopes
# app\core\security.py
import json

from jwcrypto import jwt, jwk
from fastapi import HTTPException, Header

from app.core.logger import configure_logging
from app.core.settings import settings
from app.services.admin.schemas import UserDataSchema

logger = configure_logging()


async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")
    logger.info(f"{token}")

    try:
        key = jwk.JWK.from_password(settings.JWT_SECRET_KEY)
        logger.info(f"key:{key}")
        verified_token = jwt.JWT(key=key, jwt=token)
        payload = json.loads(verified_token.claims)
        logger.info(f"payload:{payload}")

    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Token inválido o no firmado correctamente : {e}"
        )

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("user_email"),
        "active_subscriptions": payload.get("services", []),
        "exp": int(payload.get("exp")),
        "account_id": payload.get("account_info", {}).get("id"),
        "account_name": payload.get("account_info", {}).get("name"),
    }
