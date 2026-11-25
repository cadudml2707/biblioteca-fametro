from django.urls import path

from .views import RelatorioResumoView


urlpatterns = [
    path("relatorios", RelatorioResumoView.as_view(), name="relatorio-resumo"),
]
