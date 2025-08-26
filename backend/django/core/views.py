# core/views.py
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class BaseAPIView(APIView):
    """
    Vista base que asegura que cualquier error no capturado por DRF
    también devuelva el formato estándar.
    """

    def handle_exception(self, exc):
        """
        Sobrescribe el manejo de excepciones en vistas.
        Si DRF no lo maneja, aún devolvemos el formato estándar.
        """
        response = super().handle_exception(exc)

        if response is not None:
            return Response(
                {
                    "detail": response.data.get("detail", str(exc)),
                    "error_type": exc.__class__.__name__,
                    "status_code": response.status_code,
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                },
                status=response.status_code,
            )

        return Response(
            {
                "detail": str(exc),
                "error_type": exc.__class__.__name__,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
