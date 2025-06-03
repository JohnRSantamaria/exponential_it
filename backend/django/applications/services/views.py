from rest_framework.response import Response
from rest_framework.views import APIView

from services.serializers import ServiceSerializer
from .models import Service


class ServicesAccounts(APIView):
    permission_classes = []

    def get(self, request):
        services = Service.objects.all()

        serializer = ServiceSerializer(services, many=True)

        return Response(serializer.data)
