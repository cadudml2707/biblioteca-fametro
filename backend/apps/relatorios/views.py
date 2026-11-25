from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.permissions import EquipeBiblioteca

from . import services
from .serializers import FiltrosRelatorioSerializer


class RelatorioResumoView(APIView):
    permission_classes = [EquipeBiblioteca]

    def get(self, request):
        filtros = FiltrosRelatorioSerializer(data=request.query_params)
        filtros.is_valid(raise_exception=True)
        return Response(services.gerar_relatorio(**filtros.validated_data))
