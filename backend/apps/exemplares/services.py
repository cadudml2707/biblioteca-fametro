from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.obras.models import Obra

from .models import Exemplar


def consultar_exemplares():
    return Exemplar.objects.order_by("codigo", "id")


def validar_novo_vinculo(obra_id):
    if not Obra.objects.select_for_update().filter(pk=obra_id, is_active=True).exists():
        raise ValidationError({"obra_id": ["Selecione uma obra ativa."]})


def salvar_exemplar(exemplar, campos_atualizados=None):
    try:
        with transaction.atomic():
            exemplar.save(update_fields=campos_atualizados)
    except IntegrityError as exc:
        if exc.__cause__.diag.constraint_name == "exemplares_codigo_unico":
            raise ValidationError({"codigo": ["Já existe um exemplar com este código."]}) from exc
        raise
    return exemplar


@transaction.atomic
def criar_exemplar(dados, ator):
    validar_novo_vinculo(dados["obra"].pk)
    return salvar_exemplar(Exemplar(**dados, created_by=ator, updated_by=ator))


@transaction.atomic
def atualizar_exemplar(exemplar, dados, ator):
    try:
        exemplar = Exemplar.objects.select_for_update().get(pk=exemplar.pk)
    except Exemplar.DoesNotExist as exc:
        raise NotFound() from exc

    if "obra" in dados and dados["obra"].pk != exemplar.obra_id:
        validar_novo_vinculo(dados["obra"].pk)

    for campo, valor in dados.items():
        setattr(exemplar, campo, valor)
    exemplar.updated_by = ator
    return salvar_exemplar(exemplar, [*dados, "updated_by", "updated_at"])
