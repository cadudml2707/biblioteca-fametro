from django.test import TestCase
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from apps.usuarios.models import Usuario
from apps.obras.models import Obra
from apps.exemplares.models import Exemplar
from apps.reservas.models import Reserva
from apps.emprestimos.models import Emprestimo
from apps.configuracao_biblioteca.models import ConfiguracaoBiblioteca


class CirculacaoWebTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.equipe = Usuario.objects.create(nome="Bibliotecária", email="equipe@example.org", perfil=2)
        self.aluno = Usuario.objects.create(nome="Maria Silva", email="maria@example.org", perfil=1, is_active=False)
        self.obra = Obra.objects.create(titulo="Livro", autor="Autor")
        self.exemplar = Exemplar.objects.create(obra=self.obra, codigo="EX-1")

    def test_busca_de_alunos_exige_equipe_e_preserva_privacidade(self):
        self.client.force_authenticate(user=self.aluno)
        self.assertEqual(self.client.get("/api/v1/alunos").status_code, 403)
        self.client.force_authenticate(user=self.equipe)
        dados = self.client.get("/api/v1/alunos", {"search": "MARIA"}).json()
        self.assertEqual(dados["count"], 1)
        self.assertEqual(dados["results"], [{"id": self.aluno.id, "nome": "Maria Silva", "email": "maria@example.org", "is_active": False}])
        self.assertEqual(self.client.get("/api/v1/usuarios").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/alunos", {"search": "inexistente"}).json()["count"], 0)

    def test_identificacao_e_restrita_a_equipe_e_preserva_ids(self):
        reserva = Reserva.objects.create(usuario=self.aluno, obra=self.obra)
        Emprestimo.objects.create(usuario=self.aluno, exemplar=self.exemplar, data_retirada=timezone.now(), data_prevista="2027-01-01")
        self.client.force_authenticate(user=self.equipe)
        registro = self.client.get("/api/v1/reservas").json()[0]
        self.assertEqual(registro["usuario_id"], self.aluno.id)
        self.assertEqual(registro["aluno"]["nome"], self.aluno.nome)
        emprestimo = self.client.get("/api/v1/emprestimos").json()[0]
        self.assertEqual(emprestimo["exemplar"]["obra_titulo"], self.obra.titulo)
        self.assertEqual(emprestimo["exemplar_id"], self.exemplar.id)
        self.client.force_authenticate(user=self.aluno)
        registro = self.client.get("/api/v1/reservas").json()[0]
        self.assertEqual(registro["id"], reserva.id)
        self.assertNotIn("aluno", registro)

    def test_consulta_de_alunos_e_paginada(self):
        Usuario.objects.bulk_create([
            Usuario(nome=f"Aluno {numero:02}", email=f"aluno{numero}@example.org", perfil=1)
            for numero in range(25)
        ])
        self.client.force_authenticate(user=self.equipe)
        primeira = self.client.get("/api/v1/alunos").json()
        segunda = self.client.get("/api/v1/alunos", {"page": 2}).json()
        self.assertEqual(primeira["count"], 26)
        self.assertEqual(len(primeira["results"]), 20)
        self.assertEqual(len(segunda["results"]), 6)
        self.assertIsNotNone(primeira["next"])

    def test_fluxo_completo_reserva_retirada_e_devolucao(self):
        ConfiguracaoBiblioteca.objects.create(limite_reservas_ativas=2, limite_emprestimos_ativos=2, prazo_emprestimo_dias=7, prazo_retirada_reserva_dias=2)
        self.aluno.is_active = True
        self.aluno.save(update_fields=["is_active"])
        self.client.force_authenticate(user=self.aluno)
        resposta = self.client.post("/api/v1/reservas", {"obra_id": self.obra.id}, format="json")
        self.assertEqual(resposta.status_code, 201)
        reserva_id = resposta.json()["id"]
        self.client.force_authenticate(user=self.equipe)
        self.assertEqual(self.client.post(f"/api/v1/reservas/{reserva_id}/confirmar").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/reservas/{reserva_id}/confirmar").status_code, 400)
        resposta = self.client.post("/api/v1/emprestimos", {"usuario_id": self.aluno.id, "exemplar_id": self.exemplar.id, "reserva_id": reserva_id}, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.json()["aluno"]["nome"], self.aluno.nome)
        emprestimo_id = resposta.json()["id"]
        self.assertEqual(self.client.get("/api/v1/reservas").json()[0]["situacao"], 3)
        self.assertEqual(self.client.post(f"/api/v1/emprestimos/{emprestimo_id}/devolver").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/emprestimos/{emprestimo_id}/devolver").status_code, 200)
        self.assertFalse(self.client.get("/api/v1/emprestimos").json()[0]["is_active"])
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.situacao, 1)

    def ativar_aluno(self):
        self.aluno.is_active = True
        self.aluno.save(update_fields=["is_active"])

    def configurar_biblioteca(self):
        return ConfiguracaoBiblioteca.objects.create(
            limite_reservas_ativas=2,
            limite_emprestimos_ativos=2,
            prazo_emprestimo_dias=7,
            prazo_retirada_reserva_dias=2,
        )

    def test_retirada_sem_reserva(self):
        self.ativar_aluno()
        self.configurar_biblioteca()
        self.client.force_authenticate(user=self.equipe)

        resposta = self.client.post(
            "/api/v1/emprestimos",
            {"usuario_id": self.aluno.id, "exemplar_id": self.exemplar.id},
            format="json",
        )

        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertIsNone(resposta.data["reserva_id"])

    def test_retirada_rejeita_aluno_inativo_e_exemplar_indisponivel(self):
        self.configurar_biblioteca()
        self.client.force_authenticate(user=self.equipe)
        dados = {"usuario_id": self.aluno.id, "exemplar_id": self.exemplar.id}

        resposta_aluno = self.client.post("/api/v1/emprestimos", dados, format="json")
        self.assertEqual(resposta_aluno.status_code, 400)
        self.assertIn("usuario_id", resposta_aluno.data["erros"])

        self.ativar_aluno()
        self.exemplar.situacao = 2
        self.exemplar.save(update_fields=["situacao"])
        resposta_exemplar = self.client.post("/api/v1/emprestimos", dados, format="json")
        self.assertEqual(resposta_exemplar.status_code, 400)
        self.assertIn("exemplar_id", resposta_exemplar.data["erros"])

    def test_retirada_rejeita_reserva_vencida(self):
        self.ativar_aluno()
        self.configurar_biblioteca()
        reserva = Reserva.objects.create(
            usuario=self.aluno,
            obra=self.obra,
            situacao=2,
            confirmada_em=timezone.now() - timedelta(days=3),
            data_limite=timezone.now() - timedelta(days=1),
        )
        self.client.force_authenticate(user=self.equipe)

        resposta = self.client.post(
            "/api/v1/emprestimos",
            {"usuario_id": self.aluno.id, "exemplar_id": self.exemplar.id, "reserva_id": reserva.id},
            format="json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("reserva_id", resposta.data["erros"])

    def test_retirada_sem_configuracao_retorna_conflito(self):
        self.ativar_aluno()
        self.client.force_authenticate(user=self.equipe)

        resposta = self.client.post(
            "/api/v1/emprestimos",
            {"usuario_id": self.aluno.id, "exemplar_id": self.exemplar.id},
            format="json",
        )

        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(resposta.data["codigo"], "configuracao_ausente")
