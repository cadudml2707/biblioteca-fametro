from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from core.base_model import BaseModel


class Usuario(AbstractBaseUser, BaseModel):
    """Identidade mínima para preservar o modelo customizado desde a primeira migração."""

    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"

    class Meta:
        db_table = "usuarios"
