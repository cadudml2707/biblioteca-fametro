from datetime import datetime, time, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.emprestimos.models import Emprestimo
from apps.exemplares.models import Exemplar, SituacaoExemplar
from apps.obras.models import Obra
from apps.reservas.models import Reserva, SituacaoReserva


def _limites_locais(data_inicio, data_fim):
    fuso = timezone.get_default_timezone()
    inicio = timezone.make_aware(datetime.combine(data_inicio, time.min), fuso)
    fim_exclusivo = timezone.make_aware(datetime.combine(data_fim + timedelta(days=1), time.min), fuso)
    return inicio, fim_exclusivo


def gerar_relatorio(data_inicio, data_fim):
    inicio, fim_exclusivo = _limites_locais(data_inicio, data_fim)
    hoje = timezone.localdate()

    acervo = Exemplar.objects.filter(is_active=True, obra__is_active=True).aggregate(
        exemplares_ativos=Count("id"),
        exemplares_disponiveis=Count("id", filter=Q(situacao=SituacaoExemplar.DISPONIVEL)),
        exemplares_emprestados=Count("id", filter=Q(situacao=SituacaoExemplar.EMPRESTADO)),
    )

    emprestimos = Emprestimo.objects.aggregate(
        ativos=Count("id", filter=Q(is_active=True)),
        atrasados=Count("id", filter=Q(is_active=True, data_prevista__lt=hoje)),
        retiradas_periodo=Count("id", filter=Q(data_retirada__gte=inicio, data_retirada__lt=fim_exclusivo)),
        devolucoes_periodo=Count("id", filter=Q(data_devolucao__gte=inicio, data_devolucao__lt=fim_exclusivo)),
    )

    reservas_por_situacao = {
        linha["situacao"]: linha["total"]
        for linha in Reserva.objects.filter(
            data_reserva__gte=inicio,
            data_reserva__lt=fim_exclusivo,
        ).values("situacao").annotate(total=Count("id"))
    }
    situacoes = [
        {"situacao": valor, "descricao": descricao, "total": reservas_por_situacao.get(valor, 0)}
        for valor, descricao in SituacaoReserva.choices
    ]

    return {
        "periodo": {"data_inicio": data_inicio, "data_fim": data_fim},
        "acervo": {"obras_ativas": Obra.objects.filter(is_active=True).count(), **acervo},
        "emprestimos": emprestimos,
        "reservas": {
            "total_periodo": sum(reservas_por_situacao.values()),
            "por_situacao": situacoes,
        },
    }
