from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower

from core.base_model import BaseModel


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=self.normalize_email(email).strip().lower(), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario


class Usuario(AbstractBaseUser, BaseModel):
    class Perfil(models.IntegerChoices):
        ALUNO = 1, "Aluno"
        BIBLIOTECARIO = 2, "Bibliotecário"
        ADMINISTRADOR = 3, "Administrador"

    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    perfil = models.PositiveSmallIntegerField(choices=Perfil.choices)
    objects = UsuarioManager()
    USERNAME_FIELD = "email"

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = "usuarios"
        constraints = [models.UniqueConstraint(Lower("email"), name="usuarios_email_ci_unico")]
