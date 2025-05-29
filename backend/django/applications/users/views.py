# applications\users\views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from oauth2_provider.models import RefreshToken, AccessToken
from .models import User
from .serializers import UserCreateSerializer
from .utils.token_issuer import create_tokens_for_user, REFRESH_TOKEN_EXPIRATION


class RegisterUserView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Usuario creado correctamente"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
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

        return Response(create_tokens_for_user(user))


class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        refresh_token_str = request.data.get("refresh_token")
        if not refresh_token_str:
            return Response({"error": "No se proporcionó refresh_token"}, status=400)

        try:
            refresh = RefreshToken.objects.select_related(
                "access_token", "user", "application"
            ).get(token=refresh_token_str)
        except RefreshToken.DoesNotExist:
            return Response({"error": "Refresh token inválido"}, status=401)

        if not refresh.user.is_active:
            return Response({"error": "Usuario inactivo"}, status=403)

        created_at = refresh.created or refresh.access_token.created
        if timezone.now() > created_at + REFRESH_TOKEN_EXPIRATION:
            refresh.access_token.delete()
            refresh.delete()
            return Response({"error": "Refresh token expirado"}, status=401)

        # Revocar tokens antiguos
        refresh.access_token.delete()
        refresh.delete()

        return Response(create_tokens_for_user(refresh.user, app=refresh.application))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_str = request.auth.token if hasattr(request.auth, "token") else None
        if not token_str:
            return Response({"detail": "Token no proporcionado o inválido"}, status=400)

        try:
            access_token = AccessToken.objects.select_related("refresh_token").get(
                token=token_str
            )
        except AccessToken.DoesNotExist:
            return Response({"detail": "Token no encontrado"}, status=404)

        RefreshToken.objects.filter(access_token=access_token).delete()
        access_token.delete()

        return Response({"detail": "Sesión cerrada correctamente."})


class UserServicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = request.user.user_services.filter(is_active=True).select_related(
            "service"
        )
        return Response({"services": [us.service.code for us in services]})
