from rest_framework import serializers

from core.serializers import CAMPOS_AUDITORIA, CatalogoSerializer

from . import services
from .models import Obra


class ObraSerializer(CatalogoSerializer):
    quantidade_disponivel = serializers.IntegerField(read_only=True)

    class Meta:
        model = Obra
        fields = (
            "id", "titulo", "autor", "isbn", "editora", "ano_publicacao", "id_totvs",
            "is_active", "quantidade_disponivel", *CAMPOS_AUDITORIA,
        )
        read_only_fields = ("id", "id_totvs", "quantidade_disponivel", *CAMPOS_AUDITORIA)

    def create(self, validated_data):
        return services.criar_obra(validated_data, self.context["request"].user)

    def update(self, instance, validated_data):
        return services.atualizar_obra(instance, validated_data, self.context["request"].user)
