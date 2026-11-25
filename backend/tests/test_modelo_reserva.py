from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.obras.models import Obra
from apps.reservas.models import Reserva, SituacaoReserva
from apps.usuarios.models import Usuario


class ModeloReservaTests(TestCase):
    def test_restricao_de_reserva_ativa_e_situacao(self):
        aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        obra = Obra.objects.create(titulo="Livro", autor="Autora")
        reserva = Reserva.objects.create(usuario=aluno, obra=obra)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reserva.objects.create(usuario=aluno, obra=obra, situacao=SituacaoReserva.CONFIRMADA)

        reserva.situacao = SituacaoReserva.CANCELADA
        reserva.save(update_fields=["situacao"])
        Reserva.objects.create(usuario=aluno, obra=obra)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reserva.objects.create(usuario=aluno, obra=obra, situacao=5)
