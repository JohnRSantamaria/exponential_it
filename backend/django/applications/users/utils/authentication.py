from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from users.models import User
from jwcrypto import jwt, jwk
from jwcrypto.common import JWException
import json


class AppTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith(f"{self.keyword} "):
            return None  # No intentar autenticar si no es Bearer

        token_str = auth_header[len(f"{self.keyword} ") :].strip()

        try:
            key = jwk.JWK.from_password(settings.SECRET_KEY)
            token = jwt.JWT(key=key, jwt=token_str)
            claims = json.loads(token.claims)
        except JWException:
            raise AuthenticationFailed("Token inválido o no firmado correctamente")
        except json.JSONDecodeError:
            raise AuthenticationFailed("Token malformado")

        user_id = claims.get("user_id")
        if not user_id:
            raise AuthenticationFailed("El token no contiene user_id")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("Usuario no encontrado")

        # Puedes guardar payload completo si deseas usarlo luego
        request.jwt_payload = claims

        return (user, None)
