from datetime import date

from rest_framework import serializers


class FiltrosRelatorioSerializer(serializers.Serializer):
    data_inicio = serializers.DateField(required=True)
    data_fim = serializers.DateField(required=True)

    def validate(self, attrs):
        if attrs["data_inicio"] > attrs["data_fim"]:
            raise serializers.ValidationError({"data_fim": ["Informe uma data igual ou posterior à data inicial."]})
        if attrs["data_fim"] == date.max:
            raise serializers.ValidationError({"data_fim": ["A data final excede o intervalo suportado."]})
        return attrs
