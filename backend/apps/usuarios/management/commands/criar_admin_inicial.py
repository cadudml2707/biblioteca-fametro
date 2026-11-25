import getpass

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.usuarios.models import Usuario
from django.contrib.auth.password_validation import validate_password


class Command(BaseCommand):
    help = "Cria o primeiro administrador interativamente."

    def handle(self, *args, **options):
        if Usuario.objects.filter(perfil=Usuario.Perfil.ADMINISTRADOR).exists():
            raise CommandError("Já existe um administrador; use a gestão de usuários.")
        nome = input("Nome: ").strip()
        email = input("E-mail: ").strip().lower()
        if not nome or len(nome) > 255:
            raise CommandError("Informe um nome válido de até 255 caracteres.")
        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError("E-mail inválido.") from exc
        if Usuario.objects.filter(email__iexact=email).exists():
            raise CommandError("Já existe um usuário com este e-mail.")
        password = getpass.getpass("Senha: ")
        if password != getpass.getpass("Confirme a senha: "):
            raise CommandError("As senhas não coincidem.")
        usuario = Usuario(nome=nome, email=email, perfil=Usuario.Perfil.ADMINISTRADOR)
        try:
            validate_password(password, usuario)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        Usuario.objects.create_user(email=email, password=password, nome=nome, perfil=Usuario.Perfil.ADMINISTRADOR)
        self.stdout.write(self.style.SUCCESS("Administrador inicial criado."))
