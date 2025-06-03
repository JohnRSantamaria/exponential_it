# applications/accounts/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from applications.core.log_utils import format_error_response
from services.models import AccountService

from .models import Account
from .serializers import AccountSerializer


class UserAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        accounts = Account.objects.filter(user=user)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)


class IsServiceActiveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id, service_id):
        try:
            account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response(
                format_error_response(
                    message="Cuenta no encontrada o no pertenece al usuario.",
                    error_type="AccountNotFound",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
                | {"is_active": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_active = AccountService.objects.filter(
            account=account,
            service__id=service_id,
            is_active=True,
        ).exists()

        return Response({"is_active": is_active})
