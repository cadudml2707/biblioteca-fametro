from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UsuariosAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(email="admin@example.org", nome="Admin", perfil=User.Perfil.ADMINISTRADOR, password="strong-pass-827")
        self.aluno = User.objects.create_user(email="aluno@example.org", nome="Aluno", perfil=User.Perfil.ALUNO, password="strong-pass-827")
        self.biblio = User.objects.create_user(email="biblio@example.org", nome="Biblioteca", perfil=User.Perfil.BIBLIOTECARIO, password="strong-pass-827")

    def login(self, user, plataforma):
        return self.client.post("/api/v1/login", {"email": user.email.upper(), "password": "strong-pass-827", "plataforma": plataforma}, format="json")

    def test_login_e_perfis_por_plataforma(self):
        self.assertEqual(self.login(self.aluno, "web").status_code, 403)
        self.assertEqual(self.login(self.biblio, "mobile").status_code, 403)
        self.assertEqual(self.login(self.admin, "web").data["usuario"]["perfil"], 3)
        self.assertEqual(self.login(self.aluno, "mobile").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/login", {"email": self.aluno.email, "password": "errado", "plataforma": "mobile"}, format="json").status_code, 401)
        self.aluno.is_active = False
        self.aluno.save()
        self.assertEqual(self.login(self.aluno, "mobile").status_code, 401)

    def test_refresh_rotacao_logout_e_identidade(self):
        login = self.login(self.aluno, "mobile").data
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login["access"])
        self.assertEqual(self.client.get("/api/v1/me").data["email"], self.aluno.email)
        first = self.client.post("/api/v1/auth/refresh", {"refresh": login["refresh"]}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": login["refresh"]}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/logout", {"refresh": first.data["refresh"]}, format="json").status_code, 204)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": first.data["refresh"]}, format="json").status_code, 401)

    def test_desativacao_e_troca_perfil_bloqueiam_sessao(self):
        tokens = self.login(self.aluno, "mobile").data
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + tokens["access"])
        self.aluno.is_active = False
        self.aluno.save()
        self.assertEqual(self.client.get("/api/v1/me").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": tokens["refresh"]}, format="json").status_code, 401)
        self.aluno.is_active = True
        self.aluno.perfil = User.Perfil.BIBLIOTECARIO
        self.aluno.save()
        self.assertEqual(self.client.get("/api/v1/me").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": tokens["refresh"]}, format="json").status_code, 401)

    def test_administracao_auditoria_e_validacao(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.login(self.biblio, "web").data["access"])
        self.assertEqual(self.client.get("/api/v1/usuarios").status_code, 403)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.login(self.admin, "web").data["access"])
        payload = {"nome": "Nova Pessoa", "email": "NOVA@example.org", "perfil": 1, "password": "outra-senha-817"}
        response = self.client.post("/api/v1/usuarios", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["perfil"], 1)
        self.assertNotIn("password", response.data)
        novo = User.objects.get(pk=response.data["id"])
        self.assertTrue(novo.check_password(payload["password"]))
        self.assertEqual(novo.email, "nova@example.org")
        self.assertEqual(novo.created_by, self.admin)
        self.assertEqual(self.client.post("/api/v1/usuarios", payload, format="json").status_code, 400)
        self.assertEqual(self.client.patch(f"/api/v1/usuarios/{novo.pk}", {"created_by": None}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(f"/api/v1/usuarios/{novo.pk}", {"is_active": False}, format="json").status_code, 200)
        novo.refresh_from_db()
        self.assertEqual(novo.updated_by, self.admin)
        self.assertEqual(self.client.patch(f"/api/v1/usuarios/{self.admin.pk}", {"is_active": False}, format="json").status_code, 400)
        payload.update(email="outra@example.org", perfil=4)
        self.assertEqual(self.client.post("/api/v1/usuarios", payload, format="json").status_code, 400)
        payload.update(perfil=1, password="123")
        self.assertEqual(self.client.post("/api/v1/usuarios", payload, format="json").status_code, 400)

    def test_tokens_invalidos_e_expirados_sao_recusados(self):
        self.assertEqual(self.client.get("/api/v1/me").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": "invalido"}, format="json").status_code, 401)
        token = RefreshToken.for_user(self.aluno)
        token["plataforma"] = "mobile"
        token.set_exp(lifetime=timedelta(seconds=-1))
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": str(token)}, format="json").status_code, 401)

    def test_logout_nao_revoga_token_de_outra_pessoa(self):
        aluno = self.login(self.aluno, "mobile").data
        admin = self.login(self.admin, "web").data
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + admin["access"])
        self.assertEqual(self.client.post("/api/v1/logout", {"refresh": aluno["refresh"]}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", {"refresh": aluno["refresh"]}, format="json").status_code, 200)


class BootstrapTests(TestCase):
    @patch("getpass.getpass", side_effect=["uma-senha-forte-834", "uma-senha-forte-834"])
    @patch("builtins.input", side_effect=["Administrador", "admin@example.org"])
    def test_bootstrap_e_bloqueio_de_segundo_admin(self, mock_input, mock_getpass):
        call_command("criar_admin_inicial")
        user = User.objects.get(email="admin@example.org")
        self.assertEqual(user.perfil, User.Perfil.ADMINISTRADOR)
        self.assertTrue(user.check_password("uma-senha-forte-834"))
        with self.assertRaises(CommandError):
            call_command("criar_admin_inicial")


class RefreshConcorrenteTests(TransactionTestCase):
    def test_refresh_unico_em_requisicoes_concorrentes(self):
        user = User.objects.create_user(email="aluno2@example.org", nome="Aluno", perfil=User.Perfil.ALUNO, password="strong-pass-827")
        token = APIClient().post("/api/v1/login", {"email": user.email, "password": "strong-pass-827", "plataforma": "mobile"}, format="json").data["refresh"]
        barrier = Barrier(2)

        def renovar():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return APIClient().post("/api/v1/auth/refresh", {"refresh": token}, format="json").status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(lambda _: renovar(), range(2)))
        self.assertEqual(sorted(resultados), [200, 401])
