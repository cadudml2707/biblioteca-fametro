from core.serializers import CAMPOS_AUDITORIA, AuditedModelSerializer

from . import services
from .models import ConfiguracaoBiblioteca


class ConfiguracaoBibliotecaSerializer(AuditedModelSerializer):
    class Meta:
        model = ConfiguracaoBiblioteca
        fields = (
            "id", "limite_reservas_ativas", "limite_emprestimos_ativos",
            "prazo_emprestimo_dias", "prazo_retirada_reserva_dias", "is_active", *CAMPOS_AUDITORIA,
        )
        read_only_fields = ("id", "is_active", *CAMPOS_AUDITORIA)

    def create(self, validated_data):
        return services.criar_configuracao(validated_data, self.context["request"].user)

    def update(self, instance, validated_data):
        return services.atualizar_configuracao(instance, validated_data, self.context["request"].user)
