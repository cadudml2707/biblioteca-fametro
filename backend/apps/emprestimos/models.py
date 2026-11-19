from django.conf import settings
from django.db import models

from core.base_model import BaseModel


class Emprestimo(BaseModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="emprestimos")
    exemplar = models.ForeignKey("exemplares.Exemplar", on_delete=models.PROTECT, related_name="emprestimos")
    reserva = models.OneToOneField(
        "reservas.Reserva", on_delete=models.PROTECT, null=True, blank=True, related_name="emprestimo"
    )
    data_retirada = models.DateTimeField()
    data_prevista = models.DateField()
    data_devolucao = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "emprestimos"
        constraints = [
            models.UniqueConstraint(
                fields=["exemplar"],
                condition=models.Q(is_active=True),
                name="emprestimo_ativo_unico_por_exemplar",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_active=True, data_devolucao__isnull=True)
                    | models.Q(is_active=False, data_devolucao__isnull=False)
                ),
                name="emprestimo_atividade_coerente",
            ),
        ]
