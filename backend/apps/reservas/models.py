from django.conf import settings
from django.db import models
from django.utils import timezone

from core.base_model import BaseModel


class SituacaoReserva(models.IntegerChoices):
    SOLICITADA = 1, "Solicitada"
    CONFIRMADA = 2, "Confirmada"
    ATENDIDA = 3, "Atendida"
    CANCELADA = 4, "Cancelada"


SITUACOES_ATIVAS = (SituacaoReserva.SOLICITADA, SituacaoReserva.CONFIRMADA)


class Reserva(BaseModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas")
    obra = models.ForeignKey("obras.Obra", on_delete=models.PROTECT, related_name="reservas")
    situacao = models.PositiveSmallIntegerField(choices=SituacaoReserva.choices, default=SituacaoReserva.SOLICITADA)
    data_reserva = models.DateTimeField(default=timezone.now, editable=False)
    confirmada_em = models.DateTimeField(null=True, blank=True)
    data_limite = models.DateTimeField(null=True, blank=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reservas"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "obra"],
                condition=models.Q(is_active=True, situacao__in=SITUACOES_ATIVAS),
                name="reserva_ativa_unica_por_usuario_obra",
            ),
            models.CheckConstraint(
                condition=models.Q(situacao__in=SituacaoReserva.values),
                name="reservas_situacao_valida",
            ),
        ]
