from django.db.models import Count, Q

from apps.exemplares.models import SituacaoExemplar
from apps.usuarios.models import Usuario

from .models import Obra


def obras_com_disponibilidade():
    return Obra.objects.annotate(
        quantidade_disponivel=Count(
            "exemplares",
            filter=Q(
                exemplares__is_active=True,
                exemplares__situacao=SituacaoExemplar.DISPONIVEL,
            ),
        ),
    )


def consultar_obras(ator, busca=""):
    obras = obras_com_disponibilidade()
    if ator.perfil == Usuario.Perfil.ALUNO:
        obras = obras.filter(is_active=True)
    if busca:
        obras = obras.filter(
            Q(titulo__icontains=busca) | Q(autor__icontains=busca) | Q(isbn__icontains=busca)
        )
    return obras.order_by("titulo", "id")


def criar_obra(dados, ator):
    obra = Obra.objects.create(**dados, created_by=ator, updated_by=ator)
    return obras_com_disponibilidade().get(pk=obra.pk)


def atualizar_obra(obra, dados, ator):
    for campo, valor in dados.items():
        setattr(obra, campo, valor)
    obra.updated_by = ator
    obra.save(update_fields=[*dados, "updated_by", "updated_at"])
    return obras_com_disponibilidade().get(pk=obra.pk)
