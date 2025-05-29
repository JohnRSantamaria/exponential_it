# Seguridad: JWT, OAuth2, scopes
import json


from jwcrypto import jwt, jwk
from fastapi import HTTPException, Header

from app.core.settings import settings


async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")

    try:
        key = jwk.JWK.from_password(settings.JWT_SECRET_KEY)
        verified_token = jwt.JWT(key=key, jwt=token)
        payload = json.loads(verified_token.claims)

    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Token inválido o no firmado correctamente : {e}"
        )

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "active_subscriptions": payload.get("services", []),
    }
