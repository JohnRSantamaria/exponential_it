# applications/services/api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserService


class ActiveServiceCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, service_code):
        user = request.user
        keys_requested = request.query_params.get("keys")

        try:
            user_service = UserService.objects.get(
                user=user, service__code=service_code, is_active=True
            )
        except UserService.DoesNotExist:
            return Response(
                {"detail": "Servicio no activo o no encontrado."}, status=404
            )

        credentials_qs = user_service.credentials.all()

        if keys_requested:
            requested_keys = [k.strip() for k in keys_requested.split(",")]
            credentials_qs = credentials_qs.filter(key__in=requested_keys)

        data = {cred.key: cred.value for cred in credentials_qs}
        return Response(data)
