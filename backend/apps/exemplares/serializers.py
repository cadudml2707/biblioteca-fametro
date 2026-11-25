from rest_framework import serializers

from apps.obras.models import Obra
from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import Exemplar


class ExemplarSerializer(AuditedModelSerializer):
    obra_id = serializers.PrimaryKeyRelatedField(source="obra", queryset=Obra.objects.all())

    class Meta:
        model = Exemplar
        fields = ("id", "obra_id", "codigo", "situacao", "id_totvs", "is_active", *CAMPOS_AUDITORIA)
        read_only_fields = ("id", "situacao", "id_totvs", *CAMPOS_AUDITORIA)
        extra_kwargs = {"codigo": {"validators": []}}

    def create(self, validated_data):
        return services.criar_exemplar(validated_data, self.context["request"].user)

    def update(self, instance, validated_data):
        return services.atualizar_exemplar(instance, validated_data, self.context["request"].user)
