from rest_framework import serializers

from apps.reservas.services import pode_solicitar_reserva
from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import Obra


class ObraSerializer(AuditedModelSerializer):
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


class ObraDetalheSerializer(ObraSerializer):
    pode_solicitar_reserva = serializers.SerializerMethodField()

    class Meta(ObraSerializer.Meta):
        fields = (*ObraSerializer.Meta.fields, "pode_solicitar_reserva")
        read_only_fields = (*ObraSerializer.Meta.read_only_fields, "pode_solicitar_reserva")

    def get_pode_solicitar_reserva(self, obra):
        return pode_solicitar_reserva(self.context["request"].user, obra)
