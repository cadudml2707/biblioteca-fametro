from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EquipeBiblioteca

from . import services
from .serializers import FiltrosReservaSerializer, ReservaSerializer


class ReservaListCreateView(generics.ListCreateAPIView):
    serializer_class = ReservaSerializer

    def get_queryset(self):
        ator = self.request.user
        filtros = {}
        if ator.perfil != Usuario.Perfil.ALUNO:
            serializer = FiltrosReservaSerializer(data=self.request.query_params)
            serializer.is_valid(raise_exception=True)
            filtros = serializer.validated_data
        return services.consultar_reservas(ator, filtros)

    def post(self, request, *args, **kwargs):
        if request.user.perfil != Usuario.Perfil.ALUNO:
            raise PermissionDenied("Somente alunos podem solicitar reservas.")
        return super().post(request, *args, **kwargs)


class ConfirmarReservaView(APIView):
    permission_classes = [EquipeBiblioteca]

    def post(self, request, pk):
        reserva = services.confirmar_reserva(pk, request.user)
        return Response(ReservaSerializer(reserva).data)


class CancelarReservaView(APIView):
    permission_classes = [EquipeBiblioteca]

    def post(self, request, pk):
        reserva = services.cancelar_reserva(pk, request.user)
        return Response(ReservaSerializer(reserva).data)
