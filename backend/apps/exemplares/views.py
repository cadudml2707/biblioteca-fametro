from rest_framework import generics

from apps.usuarios.permissions import GerenciarCatalogo

from . import services
from .serializers import ExemplarSerializer


class ExemplaresViewMixin:
    permission_classes = [GerenciarCatalogo]
    serializer_class = ExemplarSerializer

    def get_queryset(self):
        return services.consultar_exemplares()


class ExemplarListCreateView(ExemplaresViewMixin, generics.ListCreateAPIView):
    pass


class ExemplarDetailView(ExemplaresViewMixin, generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch", "head", "options"]
