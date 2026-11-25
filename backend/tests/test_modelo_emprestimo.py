from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.emprestimos.models import Emprestimo
from apps.exemplares.models import Exemplar
from apps.obras.models import Obra
from apps.reservas.models import Reserva
from apps.usuarios.models import Usuario


class ModeloEmprestimoTests(TestCase):
    def test_restricoes_de_exemplar_reserva_e_encerramento(self):
        aluno = Usuario.objects.create(nome="Aluno", email="aluno@example.org", perfil=Usuario.Perfil.ALUNO)
        obra = Obra.objects.create(titulo="Livro", autor="Autora")
        exemplar = Exemplar.objects.create(obra=obra, codigo="A-1")
        outro = Exemplar.objects.create(obra=obra, codigo="A-2")
        reserva = Reserva.objects.create(usuario=aluno, obra=obra)
        instante = timezone.now()
        dados = {"usuario": aluno, "data_retirada": instante, "data_prevista": date(2026, 12, 1)}
        emprestimo = Emprestimo.objects.create(exemplar=exemplar, reserva=reserva, **dados)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Emprestimo.objects.create(exemplar=exemplar, **dados)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Emprestimo.objects.create(exemplar=outro, reserva=reserva, **dados)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Emprestimo.objects.filter(pk=emprestimo.pk).update(is_active=False)

        Emprestimo.objects.filter(pk=emprestimo.pk).update(is_active=False, data_devolucao=instante)
        Emprestimo.objects.create(exemplar=exemplar, **dados)
        Emprestimo.objects.create(exemplar=outro, **dados)
