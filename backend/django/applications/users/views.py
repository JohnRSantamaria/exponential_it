from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import ValidationError, APIException

from core.views import BaseAPIView
from core.utils.set_cookies import set_jwt_cookies
from users.authentication import User
from users.serializers import (
    EmailSerializer,
    UserAccountSerializer,
    ScanningSerializer,
    UserAccountSerializerBackend,
    UserRegisterSerializer,
)
from accounts.models import Account


MAX_INACTIVITY = timedelta(minutes=settings.MAX_INACTIVITY_MINUTES)


class LoginView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            user = authenticate(request, username=email, password=password)
            if not user:
                raise ValidationError({"detail": "Credenciales inválidas"})

            if not user.is_active:
                raise APIException("Cuenta desactivada. Contacte al administrador.")

            response = Response({"detail": "Login exitoso"}, status=status.HTTP_200_OK)
            set_jwt_cookies(response, user)

            user.last_activity = timezone.now()
            user.save(update_fields=["last_activity"])
            return response

        except Exception as e:
            import traceback

            print("🔥 ERROR LOGIN:", e)
            print(traceback.format_exc())
            raise APIException(f"Error inesperado: {str(e)}")


class LogoutView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        response = Response({"detail": "Logout exitoso"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class RefreshTokenView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        old_refresh = request.COOKIES.get("refresh_token")
        if not old_refresh:
            raise ValidationError({"detail": "No hay refresh token"})

        try:
            refresh = RefreshToken(old_refresh)
            user = User.objects.get(id=refresh["user_id"])

            if timezone.now() - user.last_activity > MAX_INACTIVITY:
                raise APIException("Sesión expirada por inactividad")

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
            raise ValidationError({"detail": "Refresh token inválido"})


class RegisterUserView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        user = serializer.save(is_active=False)
        return Response(
            {"detail": "Usuario creado exitosamente", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class MeView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IdentifyView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = EmailSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        input_email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=input_email)
        except User.DoesNotExist:
            raise ValidationError({"detail": "Usuario no encontrado"})

        serializer = UserAccountSerializerBackend(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IdentifyEmailView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = EmailSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        input_email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=input_email)
        except User.DoesNotExist:
            raise ValidationError({"detail": "Usuario no encontrado"})

        email_to_return = user.secondary_email or user.email
        return Response({"email": email_to_return}, status=status.HTTP_200_OK)


class ScanningView(BaseAPIView):
    permission_classes = []

    def post(self, request):
        serializer = ScanningSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        account_id = serializer.validated_data["account_id"]
        user_id = serializer.validated_data["user_id"]

        user = User.objects.get(id=user_id)

        if not user:
            raise ValidationError({"detail": "Usuario no encontrado"})

        if user.total_invoices_scanned >= user.maximum_scanned_invoices:
            raise APIException(
                f"Se alcanzó el número máximo de escaneos permitidos ({user.maximum_scanned_invoices})"
            )

        try:
            account = Account.objects.get(id=account_id, user=user)
        except Account.DoesNotExist:
            raise ValidationError(
                {"detail": "Cuenta no encontrada o no pertenece al usuario"}
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
