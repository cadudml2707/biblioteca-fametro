from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.configuracao_biblioteca.models import ConfiguracaoBiblioteca
from apps.usuarios.models import Usuario


CONFIGURACAO_URL = "/api/v1/configuracao-biblioteca"
PARAMETROS = {
    "limite_reservas_ativas": 2,
    "limite_emprestimos_ativos": 4,
    "prazo_emprestimo_dias": 14,
    "prazo_retirada_reserva_dias": 3,
}


def autenticar(client, usuario, plataforma):
    token = AccessToken.for_user(usuario)
    token["plataforma"] = plataforma
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class ConfiguracaoBibliotecaTests(TestCase):
    client_class = APIClient

    def test_administrador_configura_parametros_com_auditoria(self):
        admin = Usuario.objects.create(nome="Admin", email="admin@example.org", perfil=Usuario.Perfil.ADMINISTRADOR)
        autenticar(self.client, admin, "web")
        self.assertEqual(self.client.get(CONFIGURACAO_URL).status_code, 404)
        invalida = self.client.post(CONFIGURACAO_URL, {**PARAMETROS, "prazo_emprestimo_dias": 0}, format="json")
        self.assertEqual(invalida.status_code, 400)
        self.assertIn("prazo_emprestimo_dias", invalida.json()["erros"])

        criada = self.client.post(CONFIGURACAO_URL, PARAMETROS, format="json")
        self.assertEqual(criada.status_code, 201, criada.data)
        self.assertEqual(criada.json()["created_by"], admin.pk)
        duplicada = self.client.post(CONFIGURACAO_URL, PARAMETROS, format="json")
        self.assertEqual(duplicada.status_code, 409, duplicada.data)
        self.assertEqual(duplicada.json()["codigo"], "configuracao_ativa_existente")

        editada = self.client.patch(CONFIGURACAO_URL, {"prazo_emprestimo_dias": 7}, format="json")
        self.assertEqual(editada.status_code, 200)
        self.assertEqual(editada.json()["prazo_emprestimo_dias"], 7)
        self.assertEqual(editada.json()["updated_by"], admin.pk)
        self.assertEqual(self.client.get(CONFIGURACAO_URL).json(), editada.json())
        self.assertEqual(self.client.patch(CONFIGURACAO_URL, {"is_active": False}, format="json").status_code, 400)

    def test_bibliotecario_e_aluno_nao_gerenciam_parametros(self):
        for perfil, plataforma in ((Usuario.Perfil.BIBLIOTECARIO, "web"), (Usuario.Perfil.ALUNO, "mobile")):
            usuario = Usuario.objects.create(nome="Usuário", email=f"{perfil}@example.org", perfil=perfil)
            autenticar(self.client, usuario, plataforma)
            self.assertEqual(self.client.get(CONFIGURACAO_URL).status_code, 403)
            self.assertEqual(self.client.post(CONFIGURACAO_URL, PARAMETROS, format="json").status_code, 403)
            self.assertEqual(self.client.patch(CONFIGURACAO_URL, PARAMETROS, format="json").status_code, 403)

    def test_integridade_dos_parametros_no_banco(self):
        ConfiguracaoBiblioteca.objects.create(**PARAMETROS)
        ConfiguracaoBiblioteca.objects.create(**PARAMETROS, is_active=False)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfiguracaoBiblioteca.objects.create(**PARAMETROS)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfiguracaoBiblioteca.objects.create(**{**PARAMETROS, "limite_reservas_ativas": 0}, is_active=False)
