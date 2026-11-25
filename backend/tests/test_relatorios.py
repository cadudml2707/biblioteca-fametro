from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.emprestimos.models import Emprestimo
from apps.exemplares.models import Exemplar, SituacaoExemplar
from apps.obras.models import Obra
from apps.reservas.models import Reserva, SituacaoReserva
from apps.usuarios.models import Usuario


RELATORIOS_URL = "/api/v1/relatorios"
PERIODO = {"data_inicio": "2026-11-01", "data_fim": "2026-11-30"}


def instante_local(dia, horario=time.min):
    return timezone.make_aware(datetime.combine(dia, horario), ZoneInfo("America/Manaus"))


class RelatoriosAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.equipe = Usuario.objects.create(nome="Bibliotecária", email="equipe@example.org", perfil=2)
        self.aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=1)
        self.obra = Obra.objects.create(titulo="Livro", autor="Autora")

    def test_resumo_agrupa_acervo_circulacao_e_reservas_no_periodo_local(self):
        outra_obra = Obra.objects.create(titulo="Outro livro", autor="Autor")
        obra_inativa = Obra.objects.create(titulo="Obra inativa", autor="Autor", is_active=False)
        disponivel = Exemplar.objects.create(obra=self.obra, codigo="DISP")
        emprestado = Exemplar.objects.create(obra=self.obra, codigo="EMP", situacao=SituacaoExemplar.EMPRESTADO)
        Exemplar.objects.create(obra=self.obra, codigo="EX-INATIVO", is_active=False)
        Exemplar.objects.create(obra=obra_inativa, codigo="OBRA-INATIVA")

        ativo_atrasado = Emprestimo.objects.create(
            usuario=self.aluno,
            exemplar=emprestado,
            data_retirada=instante_local(date(2026, 11, 1)),
            data_prevista=date(2026, 11, 14),
        )
        ativo_no_prazo = Emprestimo.objects.create(
            usuario=self.aluno,
            exemplar=Exemplar.objects.create(obra=outra_obra, codigo="EMP-2", situacao=SituacaoExemplar.EMPRESTADO),
            data_retirada=instante_local(date(2026, 11, 30), time(23, 59, 59)),
            data_prevista=date(2026, 11, 15),
        )
        devolvido = Emprestimo.objects.create(
            usuario=self.aluno,
            exemplar=Exemplar.objects.create(obra=outra_obra, codigo="DEV"),
            data_retirada=instante_local(date(2026, 10, 31), time(23, 59, 59)),
            data_prevista=date(2026, 11, 10),
            data_devolucao=instante_local(date(2026, 11, 30), time(23, 59, 59)),
            is_active=False,
        )
        Emprestimo.objects.create(
            usuario=self.aluno,
            exemplar=Exemplar.objects.create(obra=outra_obra, codigo="FORA"),
            data_retirada=instante_local(date(2026, 12, 1)),
            data_prevista=date(2026, 12, 20),
        )
        self.assertTrue(ativo_atrasado.is_active)
        self.assertTrue(ativo_no_prazo.is_active)
        self.assertFalse(devolvido.is_active)

        for numero, situacao in enumerate(SituacaoReserva.values):
            obra = Obra.objects.create(titulo=f"Reserva {numero}", autor="Autora")
            Reserva.objects.create(
                usuario=self.aluno,
                obra=obra,
                situacao=situacao,
                is_active=situacao in (SituacaoReserva.SOLICITADA, SituacaoReserva.CONFIRMADA),
                data_reserva=instante_local(date(2026, 11, numero + 1)),
            )
        Reserva.objects.create(
            usuario=self.aluno,
            obra=Obra.objects.create(titulo="Fora do período", autor="Autora"),
            situacao=SituacaoReserva.SOLICITADA,
            data_reserva=instante_local(date(2026, 12, 1)),
        )

        self.client.force_authenticate(user=self.equipe)
        with patch("apps.relatorios.services.timezone.localdate", return_value=date(2026, 11, 15)):
            resposta = self.client.get(RELATORIOS_URL, PERIODO)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        dados = resposta.json()
        self.assertEqual(dados["periodo"], PERIODO)
        self.assertEqual(dados["acervo"], {
            "obras_ativas": 7,
            "exemplares_ativos": 5,
            "exemplares_disponiveis": 3,
            "exemplares_emprestados": 2,
        })
        self.assertEqual(dados["emprestimos"], {
            "ativos": 3,
            "atrasados": 1,
            "retiradas_periodo": 2,
            "devolucoes_periodo": 1,
        })
        self.assertEqual(dados["reservas"]["total_periodo"], 4)
        self.assertEqual([item["total"] for item in dados["reservas"]["por_situacao"]], [1, 1, 1, 1])
        self.assertEqual([item["descricao"] for item in dados["reservas"]["por_situacao"]], [label for _, label in SituacaoReserva.choices])
        self.assertNotIn("aluno", str(dados).lower())

    def test_relatorio_vazio_retorna_agregados_zero(self):
        self.client.force_authenticate(user=self.equipe)
        resposta = self.client.get(RELATORIOS_URL, PERIODO)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.json()["acervo"], {
            "obras_ativas": 1,
            "exemplares_ativos": 0,
            "exemplares_disponiveis": 0,
            "exemplares_emprestados": 0,
        })
        self.assertEqual(resposta.json()["emprestimos"], {
            "ativos": 0,
            "atrasados": 0,
            "retiradas_periodo": 0,
            "devolucoes_periodo": 0,
        })
        self.assertEqual(resposta.json()["reservas"]["total_periodo"], 0)
        self.assertEqual([item["total"] for item in resposta.json()["reservas"]["por_situacao"]], [0, 0, 0, 0])

    def test_relatorios_exigem_equipe_e_intervalo_valido(self):
        self.assertEqual(self.client.get(RELATORIOS_URL, PERIODO).status_code, 401)
        self.client.force_authenticate(user=self.aluno)
        self.assertEqual(self.client.get(RELATORIOS_URL, PERIODO).status_code, 403)
        self.client.force_authenticate(user=self.equipe)

        self.assertEqual(self.client.get(RELATORIOS_URL).status_code, 400)
        self.assertEqual(self.client.get(RELATORIOS_URL, {"data_inicio": PERIODO["data_inicio"]}).status_code, 400)
        invertido = self.client.get(RELATORIOS_URL, {"data_inicio": "2026-12-01", "data_fim": "2026-11-30"})
        self.assertEqual(invertido.status_code, 400)
        self.assertIn("data_fim", invertido.json()["erros"])
