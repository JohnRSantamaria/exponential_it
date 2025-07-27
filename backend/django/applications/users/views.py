from config import settings
from datetime import timedelta

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate

from accounts.models import Account

from core.utils.set_cookies import set_jwt_cookies

from users.authentication import User
from users.serializers import (
    EmailSerializer,
    MeSerializer,
    ScanningSerializer,
    UserRegisterSerializer,
)


MAX_INACTIVITY = timedelta(minutes=settings.MAX_INACTIVITY_MINUTES)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # 🔹 Autenticación estándar de Django
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 🔹 Si el usuario está inactivo, puedes validar aquí (opcional)
        if not user.is_active:
            return Response(
                {"detail": "Cuenta desactivada. Contacte al administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🔹 Respuesta con cookies HttpOnly para JWT
        response = Response({"detail": "Login exitoso"}, status=status.HTTP_200_OK)
        set_jwt_cookies(response, user)

        # 🔹 Actualizamos última actividad inmediatamente
        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])

        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response({"detail": "Logout exitoso"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        old_refresh = request.COOKIES.get("refresh_token")
        if not old_refresh:
            return Response(
                {"detail": "No hay refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh = RefreshToken(old_refresh)
            user = User.objects.get(id=refresh["user_id"])

            # ✅ Verificar inactividad
            if timezone.now() - user.last_activity > MAX_INACTIVITY:
                return Response(
                    {"detail": "Sesión expirada por inactividad"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # ✅ Renovar el token
            new_refresh = str(refresh)
            response = Response(
                {"detail": "Refresh token renovado"}, status=status.HTTP_200_OK
            )
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="None" if not settings.DEBUG else "Lax",
                path="/",
            )
            return response

        except (InvalidToken, User.DoesNotExist):
            return Response(
                {"detail": "Refresh token inválido"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            return Response(
                {"detail": "Usuario creado exitosamente", "email": user.email},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=200)


class IdentifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        input_email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=input_email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        email_to_return = user.secondary_email if user.secondary_email else user.email

        return Response(
            {
                "email": email_to_return,
            },
            status=status.HTTP_200_OK,
        )


class ScanningView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScanningSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        account_id = serializer.validated_data["account_id"]
        user = request.user

        if user.total_invoices_scanned >= user.maximum_scanned_invoices:
            return Response(
                {
                    "detail": f"Se alcanzó el número máximo de escaneos permitidos para este usuario",
                    "maximum_scanned_invoices": user.maximum_scanned_invoices,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            account = Account.objects.get(id=account_id, user=user)
        except Account.DoesNotExist:
            return Response(
                {"detail": "Cuenta no encontrada o no pertenece al usuario"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.total_invoices_scanned += 1
        user.save(update_fields=["total_invoices_scanned"])

        account.total_invoices_scanned += 1
        account.save(update_fields=["total_invoices_scanned"])

        return Response(
            {
                "detail": "Escaneo registrado correctamente",
                "user_total_invoices_scanned": user.total_invoices_scanned,
                "account_total_invoices_scanned": account.total_invoices_scanned,
                "maximum_scanned_invoices": user.maximum_scanned_invoices,
            },
            status=status.HTTP_200_OK,
        )
