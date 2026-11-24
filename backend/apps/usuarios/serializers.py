from django.db.models.functions import Lower
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import AuthenticationFailed

from .authentication import plataforma_permitida
from .models import Usuario
from . import services


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    plataforma = serializers.ChoiceField(choices=("web", "mobile"))


class RefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = self.token_class(attrs["refresh"])
        usuario = Usuario.objects.filter(pk=token.get("user_id"), is_active=True).first()
        if not usuario or not plataforma_permitida(usuario.perfil, token.get("plataforma")):
            raise AuthenticationFailed("Usuário ou plataforma não autorizados.")
        return super().validate(attrs)


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = Usuario
        fields = ("id", "nome", "email", "perfil", "is_active", "password", "created_at", "created_by", "updated_at", "updated_by")
        read_only_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")
        extra_kwargs = {"email": {"validators": []}}

    def to_internal_value(self, data):
        protected = set(data) & set(self.Meta.read_only_fields)
        if protected:
            raise serializers.ValidationError({field: ["Este campo é somente leitura."] for field in protected})
        return super().to_internal_value(data)

    def validate_email(self, value):
        email = value.strip().lower()
        queryset = Usuario.objects.annotate(email_normalizado=Lower("email")).filter(email_normalizado=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def validate(self, attrs):
        if self.instance is None and "password" not in attrs:
            raise serializers.ValidationError({"password": ["Este campo é obrigatório."]})
        return attrs

    def create(self, validated_data):
        return services.criar_usuario(validated_data, self.context["request"].user)

    def update(self, instance, validated_data):
        return services.atualizar_usuario(instance, validated_data, self.context["request"].user)


class IdentidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "nome", "email", "perfil")


class AlunoConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "nome", "email", "is_active")
        read_only_fields = fields
