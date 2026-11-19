from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from .models import ConfiguracaoBiblioteca


class ConfiguracaoJaExiste(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "configuracao_ativa_existente"
    default_detail = "Já existe uma configuração ativa da biblioteca."


class ConfiguracaoAusente(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "configuracao_ausente"
    default_detail = "A biblioteca ainda não tem parâmetros ativos."


def configuracao_ativa():
    return ConfiguracaoBiblioteca.objects.filter(is_active=True).first()


def exigir_configuracao_ativa():
    configuracao = configuracao_ativa()
    if configuracao is None:
        raise ConfiguracaoAusente()
    return configuracao


def criar_configuracao(dados, ator):
    try:
        with transaction.atomic():
            return ConfiguracaoBiblioteca.objects.create(**dados, created_by=ator, updated_by=ator)
    except IntegrityError as exc:
        if exc.__cause__.diag.constraint_name == "configuracao_biblioteca_ativa_unica":
            raise ConfiguracaoJaExiste() from exc
        raise


def atualizar_configuracao(configuracao, dados, ator):
    for campo, valor in dados.items():
        setattr(configuracao, campo, valor)
    configuracao.updated_by = ator
    configuracao.save(update_fields=[*dados, "updated_by", "updated_at"])
    return configuracao
