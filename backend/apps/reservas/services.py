from datetime import timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.configuracao_biblioteca.services import ConfiguracaoAusente, exigir_configuracao_ativa
from apps.obras.models import Obra
from apps.usuarios.models import Usuario

from .models import SITUACOES_ATIVAS, Reserva, SituacaoReserva


def consultar_reservas(ator, filtros):
    reservas = Reserva.objects.select_related("obra").order_by("-data_reserva", "-id")
    if ator.perfil == Usuario.Perfil.ALUNO:
        return reservas.filter(usuario=ator)
    return reservas.filter(**filtros)


def validar_solicitacao(aluno, obra):
    if aluno.perfil != Usuario.Perfil.ALUNO or not aluno.is_active:
        raise PermissionDenied("Somente alunos ativos podem solicitar reservas.")
    if obra is None or not obra.is_active:
        raise ValidationError({"obra_id": ["Selecione uma obra ativa."]})

    configuracao = exigir_configuracao_ativa()
    ativas = Reserva.objects.filter(usuario=aluno, is_active=True, situacao__in=SITUACOES_ATIVAS)
    if ativas.filter(obra=obra).exists():
        raise ValidationError({"obra_id": ["Você já tem uma reserva ativa para esta obra."]})
    if ativas.count() >= configuracao.limite_reservas_ativas:
        raise ValidationError({"obra_id": ["Você atingiu o limite de reservas ativas."]})


def pode_solicitar_reserva(aluno, obra):
    try:
        validar_solicitacao(aluno, obra)
    except (PermissionDenied, ValidationError, ConfiguracaoAusente):
        return False
    return True


@transaction.atomic
def solicitar_reserva(ator, obra_id):
    aluno = get_object_or_404(Usuario.objects.select_for_update(), pk=ator.pk)
    obra = Obra.objects.select_for_update().filter(pk=obra_id).first()
    validar_solicitacao(aluno, obra)

    try:
        return Reserva.objects.create(usuario=aluno, obra=obra, created_by=aluno, updated_by=aluno)
    except IntegrityError as exc:
        if exc.__cause__.diag.constraint_name == "reserva_ativa_unica_por_usuario_obra":
            raise ValidationError({"obra_id": ["Você já tem uma reserva ativa para esta obra."]}) from exc
        raise


@transaction.atomic
def confirmar_reserva(reserva_id, ator):
    reserva = get_object_or_404(Reserva.objects.select_for_update(), pk=reserva_id)
    if not reserva.is_active or reserva.situacao != SituacaoReserva.SOLICITADA:
        raise ValidationError({"situacao": ["Somente reservas solicitadas e ativas podem ser confirmadas."]})

    configuracao = exigir_configuracao_ativa()
    agora = timezone.localtime(timezone.now(), timezone.get_default_timezone())
    try:
        prazo = agora + timedelta(days=configuracao.prazo_retirada_reserva_dias)
    except OverflowError as exc:
        raise ValidationError({"prazo_retirada_reserva_dias": ["O prazo excede a data máxima suportada."]}) from exc
    reserva.situacao = SituacaoReserva.CONFIRMADA
    reserva.confirmada_em = agora
    reserva.data_limite = prazo
    reserva.updated_by = ator
    reserva.save(update_fields=["situacao", "confirmada_em", "data_limite", "updated_by", "updated_at"])
    return reserva


@transaction.atomic
def cancelar_reserva(reserva_id, ator):
    reserva = get_object_or_404(Reserva.objects.select_for_update(), pk=reserva_id)
    if not reserva.is_active or reserva.situacao not in SITUACOES_ATIVAS:
        raise ValidationError({"situacao": ["Somente reservas solicitadas ou confirmadas podem ser canceladas."]})

    reserva.situacao = SituacaoReserva.CANCELADA
    reserva.is_active = False
    reserva.encerrada_em = timezone.now()
    reserva.updated_by = ator
    reserva.save(update_fields=["situacao", "is_active", "encerrada_em", "updated_by", "updated_at"])
    return reserva


def atender_reserva_na_retirada(reserva_id, aluno_id, obra_id, agora, ator):
    reserva = Reserva.objects.select_for_update().filter(
        pk=reserva_id,
        usuario_id=aluno_id,
        obra_id=obra_id,
        is_active=True,
        situacao=SituacaoReserva.CONFIRMADA,
    ).first()
    if reserva is None:
        raise ValidationError({"reserva_id": ["Selecione uma reserva ativa e confirmada do aluno para esta obra."]})
    if reserva.data_limite is None or agora > reserva.data_limite:
        raise ValidationError({"reserva_id": ["O prazo de retirada da reserva venceu."]})

    reserva.situacao = SituacaoReserva.ATENDIDA
    reserva.is_active = False
    reserva.encerrada_em = agora
    reserva.updated_by = ator
    reserva.save(update_fields=["situacao", "is_active", "encerrada_em", "updated_by", "updated_at"])
    return reserva
