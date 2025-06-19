import re

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.utils.authentication import AppTokenAuthentication
from services.serializers import ServiceCredentialSerializer, ServiceSerializer
from .models import AccountService, Service, ServiceCredential


class ServicesAccountsView(APIView):
    permission_classes = []

    def get(self, request):
        services = Service.objects.all()

        serializer = ServiceSerializer(services, many=True)

        return Response(serializer.data)


class ServiceCredentialsView(APIView):
    authentication_classes = [AppTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account_info = getattr(request, "jwt_payload", {}).get("account_info", {})
        account_id = account_info.get("id")
        raw_key = request.query_params.get("search", "").strip()

        if not account_id:
            return Response(
                {"detail": "No se encontró una cuenta válida en el token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_key = re.sub(r"\s+", "", raw_key.lower()) if raw_key else None

        account_services = AccountService.objects.filter(
            account_id=account_id,
            is_active=True,
        ).select_related("service")

        if not account_services.exists():
            return Response(
                {"detail": "No se encontraron servicios activos."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = []

        for account_service in account_services:
            all_credentials = ServiceCredential.objects.filter(
                account_service=account_service
            )

            if normalized_key:
                filtered = [
                    cred
                    for cred in all_credentials
                    if re.sub(r"\s+", "", cred.key.lower()) == normalized_key
                ]
            else:
                filtered = all_credentials

            serializer = ServiceCredentialSerializer(filtered, many=True)
            result.append(
                {
                    "service": account_service.service.code,
                    "service_name": account_service.service.name,
                    "credentials": serializer.data,
                }
            )

        return Response(result, status=status.HTTP_200_OK)


class ServiceCredentialsByServiceIdView(APIView):
    authentication_classes = [AppTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, service_id):
        account_info = getattr(request, "jwt_payload", {}).get("account_info", {})
        account_id = account_info.get("id")
        raw_key = request.query_params.get("search", "").strip()

        if not account_id:
            return Response(
                {"detail": "No se encontró una cuenta válida en el token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account_service = AccountService.objects.select_related("service").get(
                account_id=account_id,
                service_id=service_id,
                is_active=True,
            )
        except AccountService.DoesNotExist:
            return Response(
                {"detail": "Servicio no asociado a esta cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        normalized_key = re.sub(r"\s+", "", raw_key.lower()) if raw_key else None

        all_credentials = ServiceCredential.objects.filter(
            account_service=account_service
        )

        if normalized_key:
            filtered = [
                cred
                for cred in all_credentials
                if re.sub(r"\s+", "", cred.key.lower()) == normalized_key
            ]
        else:
            filtered = all_credentials

        serializer = ServiceCredentialSerializer(filtered, many=True)

        return Response(
            {
                "service": account_service.service.code,
                "service_name": account_service.service.name,
                "credentials": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
