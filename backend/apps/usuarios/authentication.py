from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Usuario


def plataforma_permitida(perfil, plataforma):
    return (plataforma == "mobile" and perfil == Usuario.Perfil.ALUNO) or (
        plataforma == "web" and perfil in {Usuario.Perfil.ALUNO, Usuario.Perfil.BIBLIOTECARIO, Usuario.Perfil.ADMINISTRADOR}
    )


class PlatformJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not plataforma_permitida(user.perfil, validated_token.get("plataforma")):
            raise AuthenticationFailed("Perfil não autorizado para esta plataforma.")
        return user
