from django.urls import path

from .views import ExemplarDetailView, ExemplarListCreateView


urlpatterns = [
    path("exemplares", ExemplarListCreateView.as_view(), name="exemplares"),
    path("exemplares/<int:pk>", ExemplarDetailView.as_view(), name="exemplar-detail"),
]
