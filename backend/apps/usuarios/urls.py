from django.urls import path

from .views import LoginView, LogoutView, MeView, RefreshView, UsuarioDetailView, UsuarioListCreateView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="refresh"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("usuarios", UsuarioListCreateView.as_view(), name="usuarios"),
    path("usuarios/<int:pk>", UsuarioDetailView.as_view(), name="usuario-detail"),
]
