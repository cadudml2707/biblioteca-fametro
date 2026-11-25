from django.urls import path

from .views import ConfiguracaoBibliotecaView


urlpatterns = [
    path("configuracao-biblioteca", ConfiguracaoBibliotecaView.as_view(), name="configuracao-biblioteca"),
]
