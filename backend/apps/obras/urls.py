from django.urls import path

from .views import ObraDetailView, ObraListCreateView


urlpatterns = [
    path("obras", ObraListCreateView.as_view(), name="obras"),
    path("obras/<int:pk>", ObraDetailView.as_view(), name="obra-detail"),
]
