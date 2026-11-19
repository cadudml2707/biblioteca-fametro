from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as datetime_timezone
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.configuracao_biblioteca.models import ConfiguracaoBiblioteca
from apps.emprestimos.models import Emprestimo
from apps.exemplares.models import Exemplar, SituacaoExemplar
from apps.obras.models import Obra
from apps.reservas.models import Reserva, SituacaoReserva
from apps.usuarios.models import Usuario

from .test_configuracao_biblioteca import PARAMETROS, autenticar


EMPRESTIMOS_URL = "/api/v1/emprestimos"


class EmprestimosAPITests(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.configuracao = ConfiguracaoBiblioteca.objects.create(**PARAMETROS)
        cls.aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        cls.colega = Usuario.objects.create(nome="Colega", email="colega@example.org", perfil=Usuario.Perfil.ALUNO)
        cls.biblio = Usuario.objects.create(nome="Biblio", email="biblio@example.org", perfil=Usuario.Perfil.BIBLIOTECARIO)
        cls.admin = Usuario.objects.create(nome="Admin", email="admin@example.org", perfil=Usuario.Perfil.ADMINISTRADOR)
        cls.obra = Obra.objects.create(titulo="Livro", autor="Autor")
        cls.outra_obra = Obra.objects.create(titulo="Outro livro", autor="Autor")
        cls.exemplar = Exemplar.objects.create(obra=cls.obra, codigo="EX-1")
        cls.outro_exemplar = Exemplar.objects.create(obra=cls.obra, codigo="EX-2")

    def setUp(self):
        autenticar(self.client, self.biblio, "web")

    def retirar(self, exemplar=None, **dados):
        payload = {"usuario_id": self.aluno.pk, "exemplar_id": (exemplar or self.exemplar).pk, **dados}
        return self.client.post(EMPRESTIMOS_URL, payload, format="json")

    def devolver(self, pk):
        return self.client.post(f"{EMPRESTIMOS_URL}/{pk}/devolver")

    def confirmar_reserva(self, usuario=None, obra=None, prazo=None):
        return Reserva.objects.create(
            usuario=usuario or self.aluno,
            obra=obra or self.obra,
            situacao=SituacaoReserva.CONFIRMADA,
            confirmada_em=timezone.now(),
            data_limite=prazo or timezone.now() + timedelta(days=1),
        )

    def test_retirada_e_devolucao_atualizam_catalogo_preservando_auditoria(self):
        detalhe_obra = f"/api/v1/obras/{self.obra.pk}"
        self.assertEqual(self.client.get(detalhe_obra).json()["quantidade_disponivel"], 2)
        instante = datetime(2026, 11, 19, 2, 30, tzinfo=datetime_timezone.utc)
        with patch("apps.emprestimos.services.timezone.now", return_value=instante):
            retirada = self.retirar()
        self.assertEqual(retirada.status_code, 201, retirada.data)
        dados = retirada.json()
        self.assertEqual(dados["data_retirada"], "2026-11-18T22:30:00-04:00")
        self.assertEqual(dados["data_prevista"], "2026-12-02")
        self.assertEqual(dados["created_by"], self.biblio.pk)
        self.assertIsNone(dados["reserva_id"])
        self.assertIsNone(dados["data_devolucao"])
        self.assertEqual(self.client.get(detalhe_obra).json()["quantidade_disponivel"], 1)

        self.configuracao.prazo_emprestimo_dias = 30
        self.configuracao.save(update_fields=["prazo_emprestimo_dias"])
        detalhe = self.client.get(f"{EMPRESTIMOS_URL}/{dados['id']}").json()
        self.assertEqual(detalhe["data_prevista"], dados["data_prevista"])
        self.configuracao.delete()
        self.aluno.is_active = False
        self.aluno.save(update_fields=["is_active"])

        autenticar(self.client, self.admin, "web")
        devolvida = self.devolver(dados["id"])
        self.assertEqual(devolvida.status_code, 200, devolvida.data)
        encerrado = devolvida.json()
        self.assertFalse(encerrado["is_active"])
        self.assertIsNotNone(encerrado["data_devolucao"])
        self.assertEqual(encerrado["created_by"], self.biblio.pk)
        self.assertEqual(encerrado["updated_by"], self.admin.pk)
        self.assertEqual(self.client.get(detalhe_obra).json()["quantidade_disponivel"], 2)

        autenticar(self.client, self.biblio, "web")
        self.assertEqual(self.devolver(dados["id"]).json(), encerrado)
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.updated_by, self.admin)

    def test_atendimento_de_reserva_libera_vaga(self):
        self.configuracao.limite_reservas_ativas = 1
        self.configuracao.save(update_fields=["limite_reservas_ativas"])
        reserva = self.confirmar_reserva()
        retirada = self.retirar(reserva_id=reserva.pk)
        self.assertEqual(retirada.status_code, 201, retirada.data)
        self.assertEqual(retirada.json()["reserva_id"], reserva.pk)
        reserva.refresh_from_db()
        self.assertEqual(reserva.situacao, SituacaoReserva.ATENDIDA)
        self.assertFalse(reserva.is_active)
        self.assertEqual(reserva.encerrada_em, Emprestimo.objects.get(pk=retirada.json()["id"]).data_retirada)
        self.assertEqual(reserva.updated_by, self.biblio)
        recusada = self.retirar(self.outro_exemplar, reserva_id=reserva.pk)
        self.assertEqual(recusada.status_code, 400)
        self.assertIn("reserva_id", recusada.json()["erros"])

        autenticar(self.client, self.aluno, "mobile")
        detalhe = self.client.get(f"/api/v1/obras/{self.obra.pk}").json()
        self.assertTrue(detalhe["pode_solicitar_reserva"])

    def test_repetir_devolucao_preserva_novo_emprestimo_do_exemplar(self):
        anterior = self.retirar().json()
        devolvido = self.devolver(anterior["id"]).json()
        atual = self.retirar(usuario_id=self.colega.pk)
        self.assertEqual(atual.status_code, 201, atual.data)
        self.assertEqual(self.devolver(anterior["id"]).json(), devolvido)
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, SituacaoExemplar.EMPRESTADO)
        self.assertTrue(Emprestimo.objects.get(pk=atual.json()["id"]).is_active)

    def test_reservas_invalidas_preservam_disponibilidade(self):
        colega = self.confirmar_reserva(usuario=self.colega)
        outra_obra = self.confirmar_reserva(obra=self.outra_obra)
        vencida = self.confirmar_reserva(prazo=timezone.now() - timedelta(seconds=1))
        for reserva in (colega, outra_obra, vencida):
            resposta = self.retirar(reserva_id=reserva.pk)
            self.assertEqual(resposta.status_code, 400, resposta.data)
            self.assertIn("reserva_id", resposta.json()["erros"])
            reserva.refresh_from_db()
            self.assertEqual(reserva.situacao, SituacaoReserva.CONFIRMADA)

        vencida.situacao = SituacaoReserva.SOLICITADA
        vencida.save(update_fields=["situacao"])
        resposta = self.retirar(reserva_id=vencida.pk)
        self.assertEqual(resposta.status_code, 400, resposta.data)
        self.assertFalse(Emprestimo.objects.exists())
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, SituacaoExemplar.DISPONIVEL)

    def test_retirada_valida_configuracao_limite_e_registros_ativos(self):
        self.configuracao.limite_emprestimos_ativos = 1
        self.configuracao.save(update_fields=["limite_emprestimos_ativos"])
        self.assertEqual(self.retirar(usuario_id=self.admin.pk).status_code, 400)

        self.outra_obra.is_active = False
        self.outra_obra.save(update_fields=["is_active"])
        de_obra_inativa = Exemplar.objects.create(obra=self.outra_obra, codigo="IN-1")
        inativo = Exemplar.objects.create(obra=self.obra, codigo="IN-2", is_active=False)
        self.assertEqual(self.retirar(de_obra_inativa).status_code, 400)
        self.assertEqual(self.retirar(inativo).status_code, 400)
        self.assertEqual(self.retirar().status_code, 201)
        self.assertEqual(self.retirar().status_code, 400)
        limite = self.retirar(self.outro_exemplar)
        self.assertEqual(limite.status_code, 400)
        self.assertIn("usuario_id", limite.json()["erros"])
        self.configuracao.delete()
        ausente = self.retirar(self.outro_exemplar)
        self.assertEqual(ausente.status_code, 409)
        self.assertEqual(ausente.json()["codigo"], "configuracao_ausente")

    def test_protecao_do_exemplar_emprestado(self):
        emprestimo = self.retirar().json()
        url = f"/api/v1/exemplares/{self.exemplar.pk}"
        for campo, valor in (("obra_id", self.outra_obra.pk), ("is_active", False)):
            resposta = self.client.patch(url, {campo: valor}, format="json")
            self.assertEqual(resposta.status_code, 400, resposta.data)
            self.assertIn(campo, resposta.json()["erros"])
        self.assertEqual(self.client.patch(url, {"codigo": "NOVO"}, format="json").status_code, 200)
        self.assertEqual(self.devolver(emprestimo["id"]).status_code, 200)
        alteracao = self.client.patch(url, {"obra_id": self.outra_obra.pk, "is_active": False}, format="json")
        self.assertEqual(alteracao.status_code, 200, alteracao.data)

    def test_consulta_filtros_e_permissoes(self):
        primeiro = self.retirar().json()
        segundo = self.retirar(self.outro_exemplar, usuario_id=self.colega.pk).json()
        self.devolver(primeiro["id"])

        for filtros, emprestimo in (
            ({"usuario_id": self.aluno.pk}, primeiro),
            ({"exemplar_id": self.outro_exemplar.pk}, segundo),
            ({"situacao": "devolvido"}, primeiro),
            ({"situacao": "ativo"}, segundo),
        ):
            consulta = self.client.get(EMPRESTIMOS_URL, filtros)
            self.assertEqual(consulta.status_code, 200, consulta.data)
            self.assertEqual([item["id"] for item in consulta.json()], [emprestimo["id"]])
        self.assertEqual(self.client.get(EMPRESTIMOS_URL, {"situacao": "invalida"}).status_code, 400)
        self.assertEqual(self.devolver(9999).status_code, 404)
        self.assertEqual(
            self.client.patch(f"{EMPRESTIMOS_URL}/{segundo['id']}", {"is_active": False}, format="json").status_code,
            405,
        )

        autenticar(self.client, self.aluno, "mobile")
        self.assertEqual(self.client.get(EMPRESTIMOS_URL).status_code, 403)
        self.assertEqual(self.client.get(f"{EMPRESTIMOS_URL}/{primeiro['id']}").status_code, 403)
        self.assertEqual(self.retirar().status_code, 403)
        self.assertEqual(self.devolver(segundo["id"]).status_code, 403)

    def test_falha_ao_atualizar_exemplar_reverte_retirada_e_reserva(self):
        reserva = self.confirmar_reserva()
        with patch.object(Exemplar, "save", side_effect=RuntimeError("falha")):
            with self.assertRaisesMessage(RuntimeError, "falha"):
                self.retirar(reserva_id=reserva.pk)
        self.assertFalse(Emprestimo.objects.exists())
        reserva.refresh_from_db()
        self.exemplar.refresh_from_db()
        self.assertEqual(reserva.situacao, SituacaoReserva.CONFIRMADA)
        self.assertTrue(reserva.is_active)
        self.assertIsNone(reserva.encerrada_em)
        self.assertEqual(self.exemplar.situacao, SituacaoExemplar.DISPONIVEL)

    def test_falha_ao_atualizar_exemplar_reverte_devolucao(self):
        emprestimo = self.retirar().json()
        with patch.object(Exemplar, "save", side_effect=RuntimeError("falha")):
            with self.assertRaisesMessage(RuntimeError, "falha"):
                self.devolver(emprestimo["id"])
        registro = Emprestimo.objects.get(pk=emprestimo["id"])
        self.exemplar.refresh_from_db()
        self.assertTrue(registro.is_active)
        self.assertIsNone(registro.data_devolucao)
        self.assertEqual(self.exemplar.situacao, SituacaoExemplar.EMPRESTADO)


class EmprestimosConcorrenciaTests(TransactionTestCase):
    def test_retiradas_simultaneas_respeitam_limite_e_exclusividade(self):
        biblio = Usuario.objects.create(nome="Biblio", email="biblio@example.org", perfil=Usuario.Perfil.BIBLIOTECARIO)
        alunos = [
            Usuario.objects.create(nome=f"Aluno {numero}", email=f"aluno-{numero}@example.org", perfil=Usuario.Perfil.ALUNO)
            for numero in range(2)
        ]
        obras = [Obra.objects.create(titulo=f"Livro {numero}", autor="Autor") for numero in range(2)]
        exemplares = [Exemplar.objects.create(obra=obra, codigo=f"A-{i}") for i, obra in enumerate(obras)]
        ConfiguracaoBiblioteca.objects.create(**{**PARAMETROS, "limite_emprestimos_ativos": 1})

        for pares, campo in (
            (((alunos[0], exemplares[0]), (alunos[0], exemplares[1])), "usuario_id"),
            (((alunos[0], exemplares[0]), (alunos[1], exemplares[0])), "exemplar_id"),
        ):
            barreira = Barrier(2, timeout=10)

            def retirar(par):
                aluno, exemplar = par
                close_old_connections()
                try:
                    client = APIClient()
                    autenticar(client, biblio, "web")
                    barreira.wait()
                    return client.post(
                        EMPRESTIMOS_URL, {"usuario_id": aluno.pk, "exemplar_id": exemplar.pk}, format="json"
                    )
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                respostas = list(executor.map(retirar, pares))
            self.assertEqual(sorted(resposta.status_code for resposta in respostas), [201, 400])
            erro = next(resposta for resposta in respostas if resposta.status_code == 400)
            self.assertIn(campo, erro.json()["erros"])
            emprestimo = Emprestimo.objects.get(is_active=True)
            client = APIClient()
            autenticar(client, biblio, "web")
            self.assertEqual(client.post(f"{EMPRESTIMOS_URL}/{emprestimo.pk}/devolver").status_code, 200)
