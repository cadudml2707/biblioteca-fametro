from rest_framework import serializers

from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import Reserva, SituacaoReserva


class ObraDaReservaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    titulo = serializers.CharField()
    autor = serializers.CharField()


class ReservaSerializer(AuditedModelSerializer):
    obra_id = serializers.IntegerField(min_value=1)
    obra = ObraDaReservaSerializer(read_only=True)
    situacao_descricao = serializers.CharField(source="get_situacao_display", read_only=True)

    class Meta:
        model = Reserva
        read_only_fields = (
            "id", "usuario_id", "obra", "situacao", "situacao_descricao", "is_active",
            "data_reserva", "confirmada_em", "data_limite", "encerrada_em", *CAMPOS_AUDITORIA,
        )
        fields = (*read_only_fields, "obra_id")

    def create(self, validated_data):
        return services.solicitar_reserva(self.context["request"].user, validated_data["obra_id"])


class FiltrosReservaSerializer(serializers.Serializer):
    situacao = serializers.ChoiceField(choices=SituacaoReserva.choices, required=False)
    obra_id = serializers.IntegerField(min_value=1, required=False)
    usuario_id = serializers.IntegerField(min_value=1, required=False)
