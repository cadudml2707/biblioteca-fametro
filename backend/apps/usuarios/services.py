from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import plataforma_permitida
from .models import Usuario


def validar_senha(password, usuario):
    try:
        validate_password(password, user=usuario)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from exc


def login(email, password, plataforma):
    usuario = authenticate(email=email.strip().lower(), password=password)
    if usuario is None or not usuario.is_active:
        raise AuthenticationFailed("E-mail ou senha inválidos.")
    if not plataforma_permitida(usuario.perfil, plataforma):
        raise PermissionDenied("Perfil não autorizado para esta plataforma.")
    refresh = RefreshToken.for_user(usuario)
    refresh["plataforma"] = plataforma
    return usuario, refresh


def criar_usuario(data, ator):
    password = data.pop("password")
    usuario = Usuario(**data, created_by=ator, updated_by=ator)
    validar_senha(password, usuario)
    usuario.set_password(password)
    try:
        with transaction.atomic():
            usuario.save()
    except IntegrityError as exc:
        raise serializers.ValidationError({"email": ["Já existe um usuário com este e-mail."]}) from exc
    return usuario


def atualizar_usuario(usuario, data, ator):
    if usuario.pk == ator.pk and (data.get("is_active") is False or ("perfil" in data and data["perfil"] != ator.perfil)):
        raise serializers.ValidationError({"perfil": ["Não é permitido alterar o próprio perfil ou desativar a própria conta."]})
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(usuario, field, value)
    if password is not None:
        validar_senha(password, usuario)
        usuario.set_password(password)
    usuario.updated_by = ator
    try:
        with transaction.atomic():
            usuario.save()
    except IntegrityError as exc:
        raise serializers.ValidationError({"email": ["Já existe um usuário com este e-mail."]}) from exc
    return usuario
