from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.configuracao_biblioteca.models import ConfiguracaoBiblioteca
from apps.exemplares.models import Exemplar
from apps.obras.models import Obra
from apps.reservas.models import Reserva, SituacaoReserva
from apps.usuarios.models import Usuario

from .test_configuracao_biblioteca import PARAMETROS, autenticar


RESERVAS_URL = "/api/v1/reservas"


class ReservasAPITests(TestCase):
    client_class = APIClient

    @classmethod
    def setUpTestData(cls):
        cls.configuracao = ConfiguracaoBiblioteca.objects.create(**PARAMETROS)
        cls.aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        cls.colega = Usuario.objects.create(nome="Colega", email="colega@example.org", perfil=Usuario.Perfil.ALUNO)
        cls.biblio = Usuario.objects.create(nome="Biblio", email="biblio@example.org", perfil=Usuario.Perfil.BIBLIOTECARIO)
        cls.obra = Obra.objects.create(titulo="Obra sem exemplares", autor="Autor")
        cls.outra = Obra.objects.create(titulo="Outra", autor="Autor")

    def solicitar(self, obra):
        return self.client.post(RESERVAS_URL, {"obra_id": obra.pk}, format="json")

    def transicao(self, reserva_id, acao):
        return self.client.post(f"{RESERVAS_URL}/{reserva_id}/{acao}")

    def test_solicitacao_e_consulta_propria(self):
        Reserva.objects.create(usuario=self.colega, obra=self.obra)
        self.assertEqual(self.client.get(RESERVAS_URL).status_code, 401)
        autenticar(self.client, self.aluno, "mobile")
        forjada = self.client.post(
            RESERVAS_URL, {"obra_id": self.obra.pk, "usuario_id": self.colega.pk}, format="json"
        )
        self.assertEqual(forjada.status_code, 400)
        self.assertIn("usuario_id", forjada.data["erros"])

        resposta = self.solicitar(self.obra)
        self.assertEqual(resposta.status_code, 201, resposta.data)
        dados = resposta.json()
        self.assertEqual(dados["usuario_id"], self.aluno.pk)
        self.assertEqual(dados["obra"]["titulo"], self.obra.titulo)
        self.assertEqual(dados["situacao"], 1)
        self.assertEqual(dados["situacao_descricao"], "Solicitada")
        self.assertEqual(dados["created_by"], self.aluno.pk)
        self.assertIsNone(dados["confirmada_em"])
        self.assertEqual(self.client.get(RESERVAS_URL, {"usuario_id": self.colega.pk}).json(), [dados])
        self.assertEqual(self.transicao(dados["id"], "confirmar").status_code, 403)
        self.assertEqual(self.transicao(dados["id"], "cancelar").status_code, 403)
        self.assertEqual(self.solicitar(self.obra).status_code, 400)

    def test_limite_obra_inativa_e_configuracao_ausente(self):
        self.configuracao.limite_reservas_ativas = 1
        self.configuracao.save(update_fields=["limite_reservas_ativas"])
        bloqueada = Obra.objects.create(titulo="Inativa", autor="Autor", is_active=False)
        autenticar(self.client, self.aluno, "mobile")
        self.assertEqual(self.solicitar(bloqueada).status_code, 400)
        self.assertEqual(self.solicitar(self.obra).status_code, 201)
        self.assertEqual(self.solicitar(self.outra).status_code, 400)

        self.configuracao.delete()
        resposta = self.solicitar(self.outra)
        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(resposta.json()["codigo"], "configuracao_ausente")

    def test_equipe_consulta_e_filtra(self):
        primeira = Reserva.objects.create(usuario=self.aluno, obra=self.obra)
        segunda = Reserva.objects.create(usuario=self.colega, obra=self.outra, situacao=SituacaoReserva.CANCELADA)
        autenticar(self.client, self.biblio, "web")
        self.assertEqual(len(self.client.get(RESERVAS_URL).json()), 2)
        for filtros, reserva in (
            ({"situacao": 4}, segunda),
            ({"obra_id": self.obra.pk}, primeira),
            ({"usuario_id": self.colega.pk}, segunda),
        ):
            resposta = self.client.get(RESERVAS_URL, filtros)
            self.assertEqual(resposta.status_code, 200, resposta.data)
            self.assertEqual([item["id"] for item in resposta.json()], [reserva.pk])
        self.assertEqual(self.client.get(RESERVAS_URL, {"situacao": 9}).status_code, 400)
        self.assertEqual(self.solicitar(self.obra).status_code, 403)

    def test_confirmacao_fixa_prazo_e_cancelamento_libera_vaga(self):
        reserva = Reserva.objects.create(usuario=self.aluno, obra=self.obra, created_by=self.aluno)
        autenticar(self.client, self.biblio, "web")
        instante = datetime(2026, 11, 18, 23, 30, tzinfo=ZoneInfo("America/Manaus"))
        with patch("apps.reservas.services.timezone.now", return_value=instante):
            confirmada = self.transicao(reserva.pk, "confirmar")
        self.assertEqual(confirmada.status_code, 200, confirmada.data)
        self.assertEqual(confirmada.json()["situacao"], 2)
        self.assertEqual(confirmada.json()["confirmada_em"], "2026-11-18T23:30:00-04:00")
        self.assertEqual(confirmada.json()["data_limite"], "2026-11-21T23:30:00-04:00")
        self.assertEqual(confirmada.json()["updated_by"], self.biblio.pk)
        self.assertEqual(self.transicao(reserva.pk, "confirmar").status_code, 400)

        self.configuracao.prazo_retirada_reserva_dias = 5
        self.configuracao.save(update_fields=["prazo_retirada_reserva_dias"])
        cancelada = self.transicao(reserva.pk, "cancelar")
        self.assertEqual(cancelada.status_code, 200, cancelada.data)
        self.assertEqual(cancelada.json()["situacao"], 4)
        self.assertEqual(cancelada.json()["created_by"], self.aluno.pk)
        self.assertIsNotNone(cancelada.json()["encerrada_em"])
        self.assertFalse(cancelada.json()["is_active"])
        self.assertEqual(cancelada.json()["data_limite"], confirmada.json()["data_limite"])
        self.assertEqual(self.transicao(reserva.pk, "cancelar").status_code, 400)

        autenticar(self.client, self.aluno, "mobile")
        self.assertEqual(self.solicitar(self.obra).status_code, 201)
        self.assertEqual(len(self.client.get(RESERVAS_URL).json()), 2)

    def test_transicoes_sem_configuracao_e_reserva_atendida(self):
        reserva = Reserva.objects.create(usuario=self.aluno, obra=self.obra)
        atendida = Reserva.objects.create(usuario=self.aluno, obra=self.outra, situacao=SituacaoReserva.ATENDIDA)
        self.configuracao.delete()
        autenticar(self.client, self.biblio, "web")
        self.assertEqual(self.transicao(reserva.pk, "confirmar").status_code, 409)
        self.assertEqual(self.transicao(reserva.pk, "cancelar").status_code, 200)
        self.assertEqual(self.transicao(atendida.pk, "cancelar").status_code, 400)

    def test_reserva_preserva_disponibilidade_do_exemplar(self):
        Exemplar.objects.create(obra=self.obra, codigo="ABC-1")
        autenticar(self.client, self.aluno, "mobile")
        resposta = self.solicitar(self.obra)
        autenticar(self.client, self.biblio, "web")
        self.assertEqual(self.transicao(resposta.json()["id"], "confirmar").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/obras/{self.obra.pk}").json()["quantidade_disponivel"], 1)

    def test_elegibilidade_no_detalhe_da_obra(self):
        self.configuracao.limite_reservas_ativas = 1
        self.configuracao.save(update_fields=["limite_reservas_ativas"])
        detalhe = f"/api/v1/obras/{self.obra.pk}"
        outra_obra = f"/api/v1/obras/{self.outra.pk}"

        autenticar(self.client, self.aluno, "mobile")
        dados = self.client.get(detalhe).json()
        self.assertEqual(dados["quantidade_disponivel"], 0)
        self.assertTrue(dados["pode_solicitar_reserva"])
        solicitada = self.solicitar(self.obra).json()
        self.assertFalse(self.client.get(detalhe).json()["pode_solicitar_reserva"])
        self.assertFalse(self.client.get(outra_obra).json()["pode_solicitar_reserva"])

        autenticar(self.client, self.biblio, "web")
        self.assertFalse(self.client.get(detalhe).json()["pode_solicitar_reserva"])
        self.assertEqual(self.transicao(solicitada["id"], "cancelar").status_code, 200)
        autenticar(self.client, self.aluno, "mobile")
        self.assertTrue(self.client.get(detalhe).json()["pode_solicitar_reserva"])
        self.configuracao.delete()
        self.assertFalse(self.client.get(detalhe).json()["pode_solicitar_reserva"])


class ReservasConcorrenciaTests(TransactionTestCase):
    def test_solicitacoes_concorrentes_respeitam_limite_e_duplicidade(self):
        aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        primeira = Obra.objects.create(titulo="Primeira", autor="Autor")
        segunda = Obra.objects.create(titulo="Segunda", autor="Autor")
        configuracao = ConfiguracaoBiblioteca.objects.create(**PARAMETROS)

        for limite, obras, mensagem in (
            (1, (primeira, segunda), "limite"),
            (2, (primeira, primeira), "já tem"),
        ):
            Reserva.objects.all().delete()
            configuracao.limite_reservas_ativas = limite
            configuracao.save(update_fields=["limite_reservas_ativas"])
            barreira = Barrier(2, timeout=10)

            def solicitar(obra):
                close_old_connections()
                try:
                    client = APIClient()
                    autenticar(client, aluno, "mobile")
                    barreira.wait()
                    return client.post(RESERVAS_URL, {"obra_id": obra.pk}, format="json")
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                respostas = list(executor.map(solicitar, obras))
            self.assertEqual(sorted(resposta.status_code for resposta in respostas), [201, 400])
            erro = next(resposta.json() for resposta in respostas if resposta.status_code == 400)
            self.assertIn(mensagem, erro["erros"]["obra_id"][0])
            self.assertEqual(Reserva.objects.filter(usuario=aluno).count(), 1)
