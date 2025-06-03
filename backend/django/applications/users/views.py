# applications\users\views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from oauth2_provider.models import RefreshToken, AccessToken

from accounts.models import Account
from .models import User
from .serializers import UserCreateSerializer, UserSerializer
from .utils.token_issuer import create_tokens_for_user, REFRESH_TOKEN_EXPIRATION
from core.log_utils import format_error_response


class RegisterUserView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Usuario creado correctamente"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            format_error_response(
                message="Datos inválidos",
                error_type="ValidationError",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            | {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        account_id = request.data.get("account_id")

        if not account_id:
            return Response(
                format_error_response(
                    message="No se proporcionó el account id",
                    error_type="UnporcessableEntity",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                ),
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                format_error_response(
                    message="Credenciales inválidas",
                    error_type="InvalidCredentials",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                format_error_response(
                    message="Credenciales inválidas",
                    error_type="InvalidCredentials",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                format_error_response(
                    message="Usuario inactivo",
                    error_type="UserInactive",
                    status_code=status.HTTP_403_FORBIDDEN,
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(create_tokens_for_user(user=user, account_id=account_id))


class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        refresh_token_str = request.data.get("refresh_token")
        account_id = request.data.get("account_id")

        if not refresh_token_str:
            return Response(
                format_error_response(
                    message="No se proporcionó refresh_token",
                    error_type="MissingToken",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_id:
            return Response(
                format_error_response(
                    message="No se proporcionó el account id",
                    error_type="UnporcessableEntity",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                ),
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            refresh = RefreshToken.objects.select_related(
                "access_token", "user", "application"
            ).get(token=refresh_token_str)
        except RefreshToken.DoesNotExist:
            return Response(
                format_error_response(
                    message="Refresh token inválido",
                    error_type="RefreshTokenError",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not refresh.user.is_active:
            return Response(
                format_error_response(
                    message="Usuario inactivo",
                    error_type="UserInactive",
                    status_code=status.HTTP_403_FORBIDDEN,
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        created_at = refresh.created or refresh.access_token.created
        if timezone.now() > created_at + REFRESH_TOKEN_EXPIRATION:
            refresh.access_token.delete()
            refresh.delete()
            return Response(
                format_error_response(
                    message="Refresh token expirado",
                    error_type="TokenExpired",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Revocar tokens antiguos
        refresh.access_token.delete()
        refresh.delete()

        return Response(
            create_tokens_for_user(
                user=refresh.user,
                app=refresh.application,
                account_id=account_id,
            )
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        token_str = request.auth.token if hasattr(request.auth, "token") else None
        if not token_str:
            return Response(
                format_error_response(
                    message="Token no proporcionado o inválido",
                    error_type="TokenMissing",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = AccessToken.objects.select_related("refresh_token").get(
                token=token_str
            )
        except AccessToken.DoesNotExist:
            return Response(
                format_error_response(
                    message="Token no encontrado",
                    error_type="AccessTokenNotFound",
                    status_code=status.HTTP_404_NOT_FOUND,
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

        RefreshToken.objects.filter(access_token=access_token).delete()
        access_token.delete()

        return Response({"detail": "Sesión cerrada correctamente."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class IdentifyUserAccountsView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                format_error_response(
                    message="Credenciales inválidas",
                    error_type="InvalidCredentials",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                format_error_response(
                    message="Credenciales inválidas",
                    error_type="InvalidCredentials",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                format_error_response(
                    message="Usuario inactivo",
                    error_type="UserInactive",
                    status_code=status.HTTP_403_FORBIDDEN,
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        accounts = Account.objects.filter(user=user).values("id", "name")
        return Response({"accounts": list(accounts)})
