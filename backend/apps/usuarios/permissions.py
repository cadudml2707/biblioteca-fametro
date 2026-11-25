from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Usuario


class Administrador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.perfil == Usuario.Perfil.ADMINISTRADOR


class EquipeBiblioteca(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.perfil in {
            Usuario.Perfil.BIBLIOTECARIO,
            Usuario.Perfil.ADMINISTRADOR,
        }


class ConsultarOuGerenciarObras(EquipeBiblioteca):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return super().has_permission(request, view)
