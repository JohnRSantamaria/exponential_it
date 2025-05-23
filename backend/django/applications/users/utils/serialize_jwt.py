from jwcrypto import jwt, jwk
from django.conf import settings


def sign_jwt(payload: dict) -> str:
    key = jwk.JWK.from_password(settings.SECRET_KEY)
    token = jwt.JWT(header={"alg": "HS256"}, claims=payload)
    token.make_signed_token(key)
    return token.serialize()
