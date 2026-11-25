from collections.abc import Mapping

from rest_framework import serializers


CAMPOS_AUDITORIA = ("created_at", "created_by", "updated_at", "updated_by")


class AuditedModelSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            return super().to_internal_value(data)
        protegidos = set(self.Meta.read_only_fields).intersection(data)
        if protegidos:
            raise serializers.ValidationError({
                campo: ["Este campo é somente leitura."] for campo in sorted(protegidos)
            })
        return super().to_internal_value(data)
