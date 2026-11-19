from datetime import timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.configuracao_biblioteca.services import exigir_configuracao_ativa
from apps.exemplares.models import Exemplar, SituacaoExemplar
from apps.obras.models import Obra
from apps.reservas.services import atender_reserva_na_retirada
from apps.usuarios.models import Usuario

from .models import Emprestimo


def consultar_emprestimos():
    return Emprestimo.objects.order_by("-data_retirada", "-id")


def atualizar_situacao_exemplar(exemplar, situacao, ator):
    exemplar.situacao = situacao
    exemplar.updated_by = ator
    exemplar.save(update_fields=["situacao", "updated_by", "updated_at"])


def data_prevista_devolucao(agora, prazo_dias):
    data_local = timezone.localdate(agora, timezone.get_default_timezone())
    try:
        return data_local + timedelta(days=prazo_dias)
    except OverflowError as exc:
        raise ValidationError({"prazo_emprestimo_dias": ["O prazo excede a data máxima suportada."]}) from exc


@transaction.atomic
def retirar_exemplar(usuario_id, exemplar_id, ator, reserva_id=None):
    aluno = Usuario.objects.select_for_update().filter(
        pk=usuario_id, is_active=True, perfil=Usuario.Perfil.ALUNO,
    ).first()
    if aluno is None:
        raise ValidationError({"usuario_id": ["Selecione um aluno ativo."]})

    exemplar = Exemplar.objects.select_for_update().filter(pk=exemplar_id).first()
    if exemplar is None or not exemplar.is_active or exemplar.situacao != SituacaoExemplar.DISPONIVEL:
        raise ValidationError({"exemplar_id": ["Selecione um exemplar ativo e disponível."]})
    if not Obra.objects.select_for_update().filter(pk=exemplar.obra_id, is_active=True).exists():
        raise ValidationError({"exemplar_id": ["O exemplar deve pertencer a uma obra ativa."]})

    configuracao = exigir_configuracao_ativa()
    if Emprestimo.objects.filter(usuario=aluno, is_active=True).count() >= configuracao.limite_emprestimos_ativos:
        raise ValidationError({"usuario_id": ["O aluno atingiu o limite de empréstimos ativos."]})

    agora = timezone.now()
    data_prevista = data_prevista_devolucao(agora, configuracao.prazo_emprestimo_dias)
    reserva = None
    if reserva_id is not None:
        reserva = atender_reserva_na_retirada(reserva_id, aluno.pk, exemplar.obra_id, agora, ator)

    try:
        emprestimo = Emprestimo.objects.create(
            usuario=aluno,
            exemplar=exemplar,
            reserva=reserva,
            data_retirada=agora,
            data_prevista=data_prevista,
            created_by=ator,
            updated_by=ator,
        )
    except IntegrityError as exc:
        if exc.__cause__.diag.constraint_name == "emprestimo_ativo_unico_por_exemplar":
            raise ValidationError({"exemplar_id": ["Este exemplar já tem um empréstimo ativo."]}) from exc
        raise

    atualizar_situacao_exemplar(exemplar, SituacaoExemplar.EMPRESTADO, ator)
    return emprestimo


@transaction.atomic
def devolver_exemplar(emprestimo_id, ator):
    exemplar_id = get_object_or_404(
        Emprestimo.objects.values_list("exemplar_id", flat=True), pk=emprestimo_id,
    )
    exemplar = Exemplar.objects.select_for_update().get(pk=exemplar_id)
    emprestimo = Emprestimo.objects.select_for_update().get(pk=emprestimo_id)
    if not emprestimo.is_active:
        return emprestimo

    emprestimo.is_active = False
    emprestimo.data_devolucao = timezone.now()
    emprestimo.updated_by = ator
    emprestimo.save(update_fields=["is_active", "data_devolucao", "updated_by", "updated_at"])
    atualizar_situacao_exemplar(exemplar, SituacaoExemplar.DISPONIVEL, ator)
    return emprestimo
