from django.db import models

from core.base_model import BaseModel


class Obra(BaseModel):
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    isbn = models.CharField(max_length=32, null=True, blank=True)
    editora = models.CharField(max_length=255, null=True, blank=True)
    ano_publicacao = models.PositiveIntegerField(null=True, blank=True)
    id_totvs = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "obras"
        constraints = [
            models.UniqueConstraint(fields=["id_totvs"], name="obras_id_totvs_unico"),
        ]

    def __str__(self):
        return self.titulo
