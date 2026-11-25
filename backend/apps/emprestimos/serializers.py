from rest_framework import serializers

from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import Emprestimo


class EmprestimoSerializer(AuditedModelSerializer):
    usuario_id = serializers.IntegerField(min_value=1)
    exemplar_id = serializers.IntegerField(min_value=1)
    reserva_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def to_representation(self, instance):
        dados = super().to_representation(instance)
        dados["aluno"] = {"id": instance.usuario_id, "nome": instance.usuario.nome, "email": instance.usuario.email, "is_active": instance.usuario.is_active}
        dados["exemplar"] = {"id": instance.exemplar_id, "codigo": instance.exemplar.codigo, "obra_id": instance.exemplar.obra_id, "obra_titulo": instance.exemplar.obra.titulo}
        return dados

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
