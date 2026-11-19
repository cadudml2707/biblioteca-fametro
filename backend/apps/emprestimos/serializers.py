from rest_framework import serializers

from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import Emprestimo


class EmprestimoSerializer(AuditedModelSerializer):
    usuario_id = serializers.IntegerField(min_value=1)
    exemplar_id = serializers.IntegerField(min_value=1)
    reserva_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    class Meta:
        model = Emprestimo
        read_only_fields = ("id", "is_active", "data_retirada", "data_prevista", "data_devolucao", *CAMPOS_AUDITORIA)
        fields = (*read_only_fields, "usuario_id", "exemplar_id", "reserva_id")

    def create(self, validated_data):
        return services.retirar_exemplar(ator=self.context["request"].user, **validated_data)


class FiltrosEmprestimoSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField(min_value=1, required=False)
    exemplar_id = serializers.IntegerField(min_value=1, required=False)
    situacao = serializers.ChoiceField(choices=("ativo", "devolvido"), required=False)
