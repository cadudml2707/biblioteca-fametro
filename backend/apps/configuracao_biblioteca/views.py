from rest_framework import generics
from rest_framework.exceptions import NotFound

from apps.usuarios.permissions import Administrador

from . import services
from .serializers import ConfiguracaoBibliotecaSerializer


class ConfiguracaoBibliotecaView(generics.CreateAPIView, generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [Administrador]
    serializer_class = ConfiguracaoBibliotecaSerializer

    def get_object(self):
        configuracao = services.configuracao_ativa()
        if configuracao is None:
            raise NotFound("A biblioteca ainda não tem parâmetros ativos.")
        return configuracao
