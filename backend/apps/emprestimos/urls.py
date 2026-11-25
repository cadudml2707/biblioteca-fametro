from django.urls import path

from .views import DevolverEmprestimoView, EmprestimoDetailView, EmprestimoListCreateView


urlpatterns = [
    path("emprestimos", EmprestimoListCreateView.as_view(), name="emprestimos"),
    path("emprestimos/<int:pk>", EmprestimoDetailView.as_view(), name="emprestimo-detail"),
    path("emprestimos/<int:pk>/devolver", DevolverEmprestimoView.as_view(), name="devolver-emprestimo"),
]
