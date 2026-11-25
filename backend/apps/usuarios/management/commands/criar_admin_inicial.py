import getpass
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import connection, transaction

from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Cria o primeiro administrador interativamente ou por variáveis de ambiente."

    def add_arguments(self, parser):
        parser.add_argument("--ambiente", action="store_true", help="Usa as variáveis ADMIN_INICIAL_NOME, ADMIN_INICIAL_EMAIL e ADMIN_INICIAL_SENHA.")

    def handle(self, *args, **options):
        if options["ambiente"]:
            with transaction.atomic():
                if connection.vendor == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [429766312])
                self.criar_por_ambiente()
            return
        if Usuario.objects.filter(perfil=Usuario.Perfil.ADMINISTRADOR).exists():
            raise CommandError("Já existe um administrador; use a gestão de usuários.")
        nome = input("Nome: ").strip()
        email = input("E-mail: ").strip().lower()
        password = getpass.getpass("Senha: ")
        if password != getpass.getpass("Confirme a senha: "):
            raise CommandError("As senhas não coincidem.")
        self.criar(nome, email, password)

    def criar_por_ambiente(self):
        if Usuario.objects.filter(perfil=Usuario.Perfil.ADMINISTRADOR).exists():
            self.stdout.write("Já existe um administrador; nenhuma conta foi criada.")
            return
        nome = os.environ.get("ADMIN_INICIAL_NOME", "").strip()
        email = os.environ.get("ADMIN_INICIAL_EMAIL", "").strip().lower()
        password = os.environ.get("ADMIN_INICIAL_SENHA", "")
        if not any((nome, email, password)):
            self.stdout.write("Administrador inicial não configurado; nenhuma conta foi criada.")
            return
        if not all((nome, email, password)):
            raise CommandError("Defina ADMIN_INICIAL_NOME, ADMIN_INICIAL_EMAIL e ADMIN_INICIAL_SENHA.")
        self.criar(nome, email, password)

    def criar(self, nome, email, password):
        if not nome or len(nome) > 255:
            raise CommandError("Informe um nome válido de até 255 caracteres.")
        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError("E-mail inválido.") from exc
        if Usuario.objects.filter(email__iexact=email).exists():
            raise CommandError("Já existe um usuário com este e-mail.")
        usuario = Usuario(nome=nome, email=email, perfil=Usuario.Perfil.ADMINISTRADOR)
        try:
            validate_password(password, usuario)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        Usuario.objects.create_user(email=email, password=password, nome=nome, perfil=Usuario.Perfil.ADMINISTRADOR)
        self.stdout.write(self.style.SUCCESS("Administrador inicial criado."))
