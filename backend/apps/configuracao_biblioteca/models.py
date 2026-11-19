from django.core.validators import MinValueValidator
from django.db import models

from core.base_model import BaseModel


class ConfiguracaoBiblioteca(BaseModel):
    limite_reservas_ativas = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    limite_emprestimos_ativos = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prazo_emprestimo_dias = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prazo_retirada_reserva_dias = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "configuracao_biblioteca"
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True),
                name="configuracao_biblioteca_ativa_unica",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    limite_reservas_ativas__gte=1,
                    limite_emprestimos_ativos__gte=1,
                    prazo_emprestimo_dias__gte=1,
                    prazo_retirada_reserva_dias__gte=1,
                ),
                name="configuracao_biblioteca_parametros_positivos",
            ),
        ]
