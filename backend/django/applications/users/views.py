from datetime import timedelta

from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from oauthlib.common import generate_token
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.models import AccessToken, Application


from .utils.serialize_jwt import sign_jwt
from .models import User
from .serializers import UserCreateSerializer
from django.contrib.auth import get_user_model


class RegisterUserView(APIView):
    permission_classes = []  # Permitir acceso sin autenticación

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Usuario creado correctamente"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()


class CustomTokenView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "Usuario inactivo"}, status=status.HTTP_403_FORBIDDEN
            )

        # Crear o recuperar aplicación
        app, _ = Application.objects.get_or_create(
            name="default",
            defaults={
                "client_type": Application.CLIENT_CONFIDENTIAL,
                "authorization_grant_type": Application.GRANT_PASSWORD,
                "user": user,
            },
        )

        token = AccessToken.objects.create(
            user=user,
            application=app,
            token=generate_token(),
            expires=timezone.now()
            + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            scope="read write",
        )

        # Obtener servicios activos
        services = user.user_services.filter(is_active=True).select_related("service")
        service_codes = [s.service.code for s in services]

        # Crear JWT
        jwt_token = sign_jwt(
            {
                "sub": str(user.id),
                "email": user.email,
                "services": service_codes,
                "exp": int(
                    (
                        timezone.now()
                        + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
                    ).timestamp()
                ),
            }
        )

        return Response(
            {
                "access_token": token.token,
                "token_type": "Bearer",
                "expires_in": oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
                "scope": token.scope,
                "jwt": jwt_token,
            }
        )


class UserServicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = request.user.user_services.filter(is_active=True).select_related(
            "service"
        )
        return Response({"services": [us.service.code for us in services]})
