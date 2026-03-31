from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Pais, PlanoViagem
from .serializers import (
    PaisSerializer,
    PlanoViagemListaSerializer,
    PlanoViagemSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para API REST."""

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar e pesquisar países.

    Endpoints:
    - GET /api/paises/ - Listar todos os países
    - GET /api/paises/{id}/ - Detalhes de um país
    - GET /api/paises/search/?q=termo - Buscar países
    """

    queryset = Pais.objects.filter(ativo=True).order_by("nome")
    serializer_class = PaisSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "nome_completo", "codigo_iso"]
    ordering_fields = ["nome"]
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Busca países com autocomplete.
        Query: ?q=termo&limit=10
        """
        termo = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))

        if len(termo) < 2:
            return Response(
                {"resultados": [], "mensagem": _("Digite pelo menos 2 caracteres")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paises = Pais.objects.filter(
            Q(nome__icontains=termo)
            | Q(nome_completo__icontains=termo)
            | Q(codigo_iso__icontains=termo),
            ativo=True,
        )[:limit]

        serializer = self.get_serializer(paises, many=True)
        return Response({"resultados": serializer.data})


class PlanoViagemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar planos de viagem.

    Endpoints:
    - GET /api/planos/ - Listar planos (filtros disponíveis)
    - POST /api/planos/ - Criar novo plano
    - GET /api/planos/{uuid}/ - Detalhes do plano
    - PUT /api/planos/{uuid}/ - Atualizar plano
    - DELETE /api/planos/{uuid}/ - Deletar plano
    - GET /api/planos/meus/ - Listar meus planos
    - GET /api/planos/buscar/ - Buscar planos (sem o próprio usuário)
    """

    queryset = PlanoViagem.objects.select_related("usuario", "pais_destino")
    serializer_class = PlanoViagemSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["pais_destino__nome", "cidade_destino", "motivo_viagem"]
    ordering_fields = ["data_inicio", "data_criacao"]
    ordering = ["-data_inicio"]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    lookup_field = "uuid"

    def get_queryset(self):
        """Retorna queryset baseado na ação com queries otimizadas."""
        user = self.request.user

        if not user.is_authenticated:
            # Usuários anônimos veem apenas planos públicos
            return PlanoViagem.objects.filter(
                ativo=True, viagem_concluida=False, nivel_privacidade="publico"
            ).select_related("usuario", "pais_destino")

        if self.action == "list":
            # Otimizar query de amigos: usar uma query única com subquery
            from django.db.models import Q

            from apps.conexoes.models import Amizade

            # Subquery para obter IDs dos amigos
            amigos_subquery = Amizade.objects.filter(
                Q(usuario1=user, ativa=True) | Q(usuario2=user, ativa=True)
            ).values_list("usuario1_id", "usuario2_id")

            amigos_ids = set()
            for u1, u2 in amigos_subquery:
                if u1 != user.id:
                    amigos_ids.add(u1)
                if u2 != user.id:
                    amigos_ids.add(u2)

            # Query única com otimização
            return (
                PlanoViagem.objects.filter(
                    Q(nivel_privacidade="publico")
                    | Q(usuario=user)  # Públicos
                    | Q(  # Seus próprios
                        nivel_privacidade="amigos", usuario_id__in=amigos_ids
                    )  # Amigos
                )
                .select_related("usuario", "pais_destino")
                .distinct()
            )

        # Para outras ações, filtrar apenas planos próprios
        return PlanoViagem.objects.filter(usuario=user).select_related(
            "usuario", "pais_destino"
        )

    def get_serializer_class(self):
        """Retorna serializer baseado na ação."""
        if self.action == "list":
            return PlanoViagemListaSerializer
        return PlanoViagemSerializer

    def perform_create(self, serializer):
        """Cria plano associando ao usuário logado."""
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        """Atualiza apenas o próprio plano."""
        if serializer.instance.usuario != self.request.user:
            raise permissions.PermissionDenied(
                _("Você não pode editar planos de outros usuários.")
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Deleta apenas o próprio plano."""
        if instance.usuario != self.request.user:
            raise permissions.PermissionDenied(
                _("Você não pode deletar planos de outros usuários.")
            )
        instance.delete()

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def meus(self, request):
        """
        Retorna todos os planos do usuário autenticado.
        Endpoint: GET /api/planos/meus/
        """
        planos = (
            PlanoViagem.objects.filter(usuario=request.user)
            .select_related("pais_destino")
            .order_by("-data_inicio")
        )

        page = self.paginate_queryset(planos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(planos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def buscar(self, request):
        """
        Busca planos de viagem excluindo o próprio usuário.
        Suporta filtros: pais, data_inicio, data_fim, motivo_viagem, etc.
        Endpoint: GET /api/planos/buscar/?pais=brasil&data_inicio=2024-01-01
        """
        user = request.user

        # Queryset base: excluir o próprio usuário
        queryset = (
            PlanoViagem.objects.filter(
                ativo=True, viagem_concluida=False, nivel_privacidade="publico"
            )
            .exclude(usuario=user)
            .select_related("usuario", "pais_destino")
        )

        # Filtro: país
        pais = request.query_params.get("pais")
        if pais:
            queryset = queryset.filter(
                Q(pais_destino__nome__icontains=pais)
                | Q(pais_destino__codigo_iso__icontains=pais)
            )

        # Filtro: período
        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")

        if data_inicio and data_fim:
            from datetime import datetime

            try:
                data_inicio = datetime.fromisoformat(data_inicio).date()
                data_fim = datetime.fromisoformat(data_fim).date()
                queryset = queryset.filter(
                    Q(data_inicio__lte=data_fim) & Q(data_fim__gte=data_inicio)
                )
            except ValueError:
                return Response(
                    {"erro": _("Formato de data inválido. Use YYYY-MM-DD")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Filtro: motivo
        motivo = request.query_params.get("motivo_viagem")
        if motivo:
            queryset = queryset.filter(motivo_viagem=motivo)

        # Ordenação
        queryset = queryset.order_by("-data_inicio")

        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def marcar_concluida(self, request, uuid=None):
        """
        Marca a viagem como concluída.
        Endpoint: POST /api/planos/{uuid}/marcar_concluida/
        """
        plano = self.get_object()

        if plano.usuario != request.user:
            raise permissions.PermissionDenied(
                _("Você não pode marcar viagens de outros usuários.")
            )

        plano.viagem_concluida = True
        plano.save()

        serializer = self.get_serializer(plano)
        return Response(
            {"mensagem": _("Viagem marcada como concluída"), "plano": serializer.data},
            status=status.HTTP_200_OK,
        )
