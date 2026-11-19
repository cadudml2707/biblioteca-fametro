from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from apps.usuarios.permissions import ConsultarOuGerenciarObras

from . import services
from .serializers import ObraDetalheSerializer, ObraSerializer


class PaginacaoObras(PageNumberPagination):
    page_size = 20


class ObrasViewMixin:
    permission_classes = [ConsultarOuGerenciarObras]
    serializer_class = ObraSerializer


class ObraListCreateView(ObrasViewMixin, generics.ListCreateAPIView):
    pagination_class = PaginacaoObras

    def get_queryset(self):
        return services.consultar_obras(self.request.user, self.request.query_params.get("search", "").strip())


class ObraDetailView(ObrasViewMixin, generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "patch", "head", "options"]
    serializer_class = ObraDetalheSerializer

    def get_queryset(self):
        return services.consultar_obras(self.request.user)
