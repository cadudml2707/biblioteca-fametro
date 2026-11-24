from django.db import transaction
from django.db.models import Q
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from . import services
from .models import Usuario
from .permissions import Administrador, EquipeBiblioteca
from .serializers import AlunoConsultaSerializer, IdentidadeSerializer, LoginSerializer, RefreshSerializer, UsuarioSerializer


class PublicTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return "Bearer"


class LoginView(PublicTokenView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, refresh = services.login(**serializer.validated_data)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "usuario": IdentidadeSerializer(user).data})


class RefreshView(PublicTokenView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.data.get("refresh")
        if not isinstance(raw, str) or not raw:
            raise serializers.ValidationError({"refresh": ["Este campo é obrigatório."]})
        try:
            token = RefreshToken(raw)
            with transaction.atomic():
                OutstandingToken.objects.select_for_update().get(jti=token["jti"])
                serializer = RefreshSerializer(data={"refresh": raw})
                serializer.is_valid(raise_exception=True)
                return Response(serializer.validated_data)
        except (TokenError, OutstandingToken.DoesNotExist) as exc:
            raise InvalidToken("Token inválido ou expirado.") from exc


class LogoutView(APIView):
    def post(self, request):
        raw = request.data.get("refresh")
        if not isinstance(raw, str) or not raw:
            raise serializers.ValidationError({"refresh": ["Este campo é obrigatório."]})
        try:
            token = RefreshToken(raw)
            with transaction.atomic():
                OutstandingToken.objects.select_for_update().get(jti=token["jti"])
                token = RefreshToken(raw)
                if str(token.get("user_id")) != str(request.user.pk):
                    raise PermissionDenied("O token não pertence ao usuário autenticado.")
                token.blacklist()
        except (TokenError, OutstandingToken.DoesNotExist) as exc:
            raise InvalidToken("Token inválido ou expirado.") from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(IdentidadeSerializer(request.user).data)


class UsuarioListCreateView(generics.ListCreateAPIView):
    queryset = Usuario.objects.order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [Administrador]


class PaginacaoAlunos(PageNumberPagination):
    page_size = 20


class AlunoConsultaView(generics.ListAPIView):
    serializer_class = AlunoConsultaSerializer
    permission_classes = [EquipeBiblioteca]
    pagination_class = PaginacaoAlunos

    def get_queryset(self):
        termo = self.request.query_params.get("search", "").strip()
        return Usuario.objects.filter(perfil=Usuario.Perfil.ALUNO).filter(
            Q(nome__icontains=termo) | Q(email__icontains=termo)
        ).order_by("nome", "id")


class UsuarioDetailView(generics.RetrieveUpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [Administrador]
    http_method_names = ["get", "patch", "head", "options"]
