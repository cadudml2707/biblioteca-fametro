from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.permissions import EquipeBiblioteca

from . import services
from .serializers import EmprestimoSerializer, FiltrosEmprestimoSerializer


class EmprestimosViewMixin:
    permission_classes = [EquipeBiblioteca]
    serializer_class = EmprestimoSerializer

    def get_queryset(self):
        return services.consultar_emprestimos()


class EmprestimoListCreateView(EmprestimosViewMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        serializer = FiltrosEmprestimoSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        filtros = serializer.validated_data.copy()
        situacao = filtros.pop("situacao", None)
        if situacao is not None:
            filtros["is_active"] = situacao == "ativo"
        return super().get_queryset().filter(**filtros)


class EmprestimoDetailView(EmprestimosViewMixin, generics.RetrieveAPIView):
    pass


class DevolverEmprestimoView(APIView):
    permission_classes = [EquipeBiblioteca]

    def post(self, request, pk):
        emprestimo = services.devolver_exemplar(pk, request.user)
        return Response(EmprestimoSerializer(emprestimo).data)
