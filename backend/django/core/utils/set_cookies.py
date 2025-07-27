from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user):
    """
    Genera un refresh token JWT para el usuario autenticado y lo
    guarda en una cookie HttpOnly para mayor seguridad.

    Configuración de la cookie:
        key="refresh_token"
            Nombre de la cookie donde se almacena el token.

        value=str(refresh)
            Valor de la cookie, el token JWT en formato string.

        httponly=True
            Impide que el token sea accesible desde JavaScript (previene XSS).

        secure=False
            - False en entorno local para permitir cookies sobre HTTP.
            - Debe cambiarse a True en producción para que solo se envíe por HTTPS.

        samesite="Lax"
            - Lax: permite que la cookie se envíe en peticiones desde tu frontend (localhost:3000) durante desarrollo.
            - Strict: bloquea cookies en peticiones cruzadas (más seguro, usar en prod si frontend y backend comparten dominio).
            - None: permite cookies en entornos cross-domain en producción, pero requiere secure=True.

        path="/"
            Hace que la cookie esté disponible para todas las rutas de la API.

    Retorna:
        HttpResponse: La respuesta con la cookie agregada.
    """

    refresh = RefreshToken.for_user(user)
    is_prod = not settings.DEBUG

    print(f"\nProducción : {is_prod}\n")

    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=is_prod,  # ✅ usar True en producción
        samesite="Lax",  # ✅ usar "None" en prod si frontend y backend son dominios distintos
        path="/",  # Disponible en todas las rutas
    )
    return response
