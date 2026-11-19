from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.exemplares.models import Exemplar, SituacaoExemplar
from apps.obras.models import Obra
from apps.usuarios.models import Usuario


def autenticar(client, usuario, plataforma):
    token = AccessToken.for_user(usuario)
    token["plataforma"] = plataforma
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class CatalogoAPITests(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        cls.biblio = Usuario.objects.create(nome="Biblio", email="biblio@example.org", perfil=Usuario.Perfil.BIBLIOTECARIO)
        cls.admin = Usuario.objects.create(nome="Admin", email="admin@example.org", perfil=Usuario.Perfil.ADMINISTRADOR)

    def test_cadastro_local_e_auditoria(self):
        autenticar(self.client, self.biblio, "web")
        resposta = self.client.post("/api/v1/obras", {"titulo": "Livro", "autor": "Autora"}, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        obra = resposta.data
        self.assertEqual(obra["created_by"], self.biblio.pk)
        self.assertEqual(obra["updated_by"], self.biblio.pk)
        self.assertEqual(obra["quantidade_disponivel"], 0)
        self.assertIsNone(obra["id_totvs"])

        resposta = self.client.post(
            "/api/v1/exemplares", {"obra_id": obra["id"], "codigo": "ABC-1"}, format="json"
        )
        self.assertEqual(resposta.status_code, 201, resposta.data)
        exemplar = resposta.data
        self.assertEqual(exemplar["situacao"], SituacaoExemplar.DISPONIVEL)
        self.assertEqual(exemplar["obra_id"], obra["id"])
        self.assertEqual(exemplar["created_by"], self.biblio.pk)
        self.assertIsNone(exemplar["id_totvs"])
        self.assertEqual(self.client.get("/api/v1/exemplares").data[0]["id"], exemplar["id"])

        autenticar(self.client, self.admin, "web")
        for rota, registro, mudanca in (
            ("/api/v1/obras", obra, {"editora": "Editora"}),
            ("/api/v1/exemplares", exemplar, {"codigo": "ABC-2"}),
        ):
            url = f"{rota}/{registro['id']}"
            self.assertEqual(self.client.get(url).status_code, 200)
            resposta = self.client.patch(url, mudanca, format="json")
            self.assertEqual(resposta.status_code, 200, resposta.data)
            self.assertEqual(resposta.data["created_by"], self.biblio.pk)
            self.assertEqual(resposta.data["created_at"], registro["created_at"])
            self.assertEqual(resposta.data["updated_by"], self.admin.pk)

    def test_busca_paginacao_e_disponibilidade(self):
        obra = Obra.objects.create(titulo="Catálogo", autor="Ada", isbn="9781234567890")
        exemplares = (
            (SituacaoExemplar.DISPONIVEL, True),
            (SituacaoExemplar.DISPONIVEL, True),
            (SituacaoExemplar.EMPRESTADO, True),
            (SituacaoExemplar.DISPONIVEL, False),
        )
        for numero, (situacao, ativo) in enumerate(exemplares):
            Exemplar.objects.create(obra=obra, codigo=f"EX-{numero}", situacao=situacao, is_active=ativo)
        inativa = Obra.objects.create(titulo="Catálogo inativo", autor="Ada", is_active=False)
        outras = Obra.objects.bulk_create([Obra(titulo="Zoologia", autor="Outra") for _ in range(20)])

        autenticar(self.client, self.aluno, "mobile")
        for busca in ("catÁlogo", "ada", "978123"):
            resposta = self.client.get("/api/v1/obras", {"search": busca})
            self.assertEqual(resposta.data["count"], 1)
            self.assertEqual(resposta.data["results"][0]["id"], obra.pk)
            self.assertEqual(resposta.data["results"][0]["quantidade_disponivel"], 2)

        detalhe = self.client.get(f"/api/v1/obras/{obra.pk}")
        self.assertEqual(detalhe.data["quantidade_disponivel"], 2)
        self.assertEqual(self.client.get(f"/api/v1/obras/{inativa.pk}").status_code, 404)
        primeira = self.client.get("/api/v1/obras")
        segunda = self.client.get("/api/v1/obras", {"page": 2})
        ids = [registro["id"] for pagina in (primeira, segunda) for registro in pagina.data["results"]]
        self.assertEqual(ids, [obra.pk, *(outra.pk for outra in outras)])
        self.assertEqual(segunda.data["results"][0]["quantidade_disponivel"], 0)

    def test_permissoes_por_perfil(self):
        obra = Obra.objects.create(titulo="Livro", autor="Autora")
        exemplar = Exemplar.objects.create(obra=obra, codigo="ABC-1")
        self.assertEqual(self.client.get("/api/v1/obras").status_code, 401)
        autenticar(self.client, self.aluno, "mobile")
        self.assertEqual(self.client.post("/api/v1/obras", {}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/obras/{obra.pk}", {}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/exemplares").status_code, 403)
        self.assertEqual(self.client.get(f"/api/v1/exemplares/{exemplar.pk}").status_code, 403)

    def test_desativacao_preserva_exemplares_e_impede_novo_vinculo(self):
        obra = Obra.objects.create(titulo="Livro", autor="Autora")
        outra = Obra.objects.create(titulo="Outro livro", autor="Autora")
        exemplar = Exemplar.objects.create(obra=obra, codigo="ABC-1")
        exemplar_outra_obra = Exemplar.objects.create(obra=outra, codigo="ABC-2")
        autenticar(self.client, self.biblio, "web")

        resposta = self.client.patch(
            f"/api/v1/obras/{obra.pk}", {"is_active": False}, format="json"
        )
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertFalse(resposta.data["is_active"])
        self.assertEqual(self.client.get(f"/api/v1/obras/{obra.pk}").status_code, 200)
        exemplar.refresh_from_db()
        self.assertTrue(exemplar.is_active)
        self.assertEqual(exemplar.obra_id, obra.pk)

        novo = self.client.post(
            "/api/v1/exemplares", {"obra_id": obra.pk, "codigo": "ABC-3"}, format="json"
        )
        transferido = self.client.patch(
            f"/api/v1/exemplares/{exemplar_outra_obra.pk}", {"obra_id": obra.pk}, format="json"
        )
        for resposta in (novo, transferido):
            self.assertEqual(resposta.status_code, 400, resposta.data)
            self.assertIn("obra_id", resposta.data["erros"])

    def test_erros_de_validacao(self):
        obra = Obra.objects.create(titulo="Livro", autor="Autora")
        Exemplar.objects.create(obra=obra, codigo="ABC-1")
        autenticar(self.client, self.biblio, "web")

        for rota, dados, campo in (
            ("/api/v1/obras", {"titulo": "", "autor": "Autora"}, "titulo"),
            ("/api/v1/obras", {"titulo": "Livro", "autor": "Autora", "created_by": 1}, "created_by"),
            ("/api/v1/obras", {"titulo": "Livro", "autor": "Autora", "id_totvs": "externo"}, "id_totvs"),
            ("/api/v1/exemplares", {"codigo": "ABC-1", "obra_id": obra.pk}, "codigo"),
            ("/api/v1/exemplares", {"codigo": "ABC-2", "obra_id": obra.pk, "situacao": "EMPRESTADO"}, "situacao"),
        ):
            resposta = self.client.post(rota, dados, format="json")
            self.assertEqual(resposta.status_code, 400, resposta.data)
            self.assertEqual(resposta.data["codigo"], "dados_invalidos")
            self.assertIn(campo, resposta.data["erros"])

        self.assertEqual(self.client.post("/api/v1/obras", [{}], format="json").status_code, 400)

    def test_identificadores_totvs_opcionais_e_unicos_por_modelo(self):
        obra = Obra.objects.create(titulo="Livro", autor="Autora", id_totvs="externo")
        Obra.objects.create(titulo="Outro", autor="Autora")
        Obra.objects.create(titulo="Mais um", autor="Autora")
        Exemplar.objects.create(obra=obra, codigo="ABC-1", id_totvs="externo")
        Exemplar.objects.create(obra=obra, codigo="ABC-2")
        Exemplar.objects.create(obra=obra, codigo="ABC-3")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Obra.objects.create(titulo="Duplicada", autor="Autora", id_totvs="externo")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Exemplar.objects.create(obra=obra, codigo="ABC-4", id_totvs="externo")


class ExemplarConcorrenciaTests(TransactionTestCase):
    def test_cadastros_concorrentes_com_mesmo_codigo(self):
        biblio = Usuario.objects.create(
            nome="Biblio", email="biblio@example.org", perfil=Usuario.Perfil.BIBLIOTECARIO
        )
        obras = Obra.objects.bulk_create([Obra(titulo="Livro", autor="Autora") for _ in range(2)])
        barreira = Barrier(2, timeout=10)

        def cadastrar(obra):
            close_old_connections()
            try:
                client = APIClient()
                autenticar(client, biblio, "web")
                barreira.wait()
                return client.post("/api/v1/exemplares", {"obra_id": obra.pk, "codigo": "ABC-1"}, format="json")
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            respostas = list(executor.map(cadastrar, obras))
        self.assertEqual(sorted(resposta.status_code for resposta in respostas), [201, 400])
        recusada = next(resposta for resposta in respostas if resposta.status_code == 400)
        self.assertIn("codigo", recusada.data["erros"])
        self.assertEqual(Exemplar.objects.filter(codigo="ABC-1").count(), 1)
