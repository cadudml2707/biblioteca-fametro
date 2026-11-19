from django.db import models

from core.base_model import BaseModel


class SituacaoExemplar(models.TextChoices):
    DISPONIVEL = "DISPONIVEL", "Disponível"
    EMPRESTADO = "EMPRESTADO", "Emprestado"


class Exemplar(BaseModel):
    obra = models.ForeignKey("obras.Obra", on_delete=models.PROTECT, related_name="exemplares")
    codigo = models.CharField(max_length=100)
    situacao = models.CharField(
        max_length=10,
        choices=SituacaoExemplar.choices,
        default=SituacaoExemplar.DISPONIVEL,
    )
    id_totvs = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "exemplares"
        constraints = [
            models.UniqueConstraint(fields=["codigo"], name="exemplares_codigo_unico"),
            models.UniqueConstraint(fields=["id_totvs"], name="exemplares_id_totvs_unico"),
            models.CheckConstraint(
                condition=models.Q(situacao__in=SituacaoExemplar.values),
                name="exemplares_situacao_valida",
            ),
        ]

    def __str__(self):
        return self.codigo
