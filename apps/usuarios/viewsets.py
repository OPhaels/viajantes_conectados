from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Usuario
from .serializers import (
    UsuarioDetailSerializer,
    UsuarioEditarSerializer,
    UsuarioListaSerializer,
    UsuarioPerfilSerializer,
    UsuarioRegistroSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para API REST."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar usuários.

    Endpoints:
    - GET /api/usuarios/ - Listar usuários públicos
    - POST /api/usuarios/ - Registrar novo usuário
    - GET /api/usuarios/{uuid}/ - Perfil público do usuário
    - GET /api/usuarios/me/ - Dados do usuário autenticado
    - PUT /api/usuarios/me/ - Atualizar perfil próprio
    - GET /api/usuarios/buscar/ - Buscar usuários (sem o próprio usuário)
    """

    queryset = Usuario.objects.filter(ativo=True, perfil_publico=True)
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome_completo", "cidade_residencia", "pais_residencia"]
    ordering_fields = ["data_criacao", "nome_completo"]
    ordering = ["-data_criacao"]

    lookup_field = "uuid"

    def get_permissions(self):
        """Define permissões por ação."""
        if self.action in ["create", "register"]:
            permission_classes = [permissions.AllowAny]
        elif self.action in ["me", "update_perfil"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Retorna serializer baseado na ação."""
        if self.action == "create":
            return UsuarioRegistroSerializer
        elif self.action == "me":
            return UsuarioDetailSerializer
        elif self.action == "update_perfil":
            return UsuarioEditarSerializer
        elif self.action in ["retrieve"]:
            return UsuarioPerfilSerializer
        return UsuarioListaSerializer

    def get_queryset(self):
        """Retorna queryset baseado na ação."""
        if self.action == "list":
            # Listar apenas usuários públicos (ativos e com perfil público)
            user = self.request.user
            if user.is_authenticated:
                # Excluir o próprio usuário
                return (
                    Usuario.objects.filter(ativo=True, perfil_publico=True)
                    .exclude(uuid=user.uuid)
                    .order_by("-data_criacao")
                )
            return Usuario.objects.filter(ativo=True, perfil_publico=True).order_by(
                "-data_criacao"
            )

        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        """Cria um novo usuário (registro)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "mensagem": _("Usuário registrado com sucesso!"),
                "usuario": {
                    "uuid": str(serializer.instance.uuid),
                    "email": serializer.instance.email,
                    "nome_completo": serializer.instance.nome_completo,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Atualiza apenas o próprio perfil."""
        instance = self.get_object()

        if instance.uuid != request.user.uuid:
            raise permissions.PermissionDenied(
                _("Você não pode editar perfis de outros usuários.")
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "mensagem": _("Perfil atualizado com sucesso!"),
                "usuario": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Retorna os dados do usuário autenticado.
        Endpoint: GET /api/usuarios/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put", "patch"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def update_perfil(self, request):
        """
        Atualiza o perfil do usuário autenticado.
        Endpoint: PUT/PATCH /api/usuarios/update_perfil/
        """
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "mensagem": _("Perfil atualizado com sucesso!"),
                "usuario": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def buscar(self, request):
        """
        Busca usuários excluindo o próprio usuário.
        Suporta filtros: q=termo (nome, cidade, país), limit=20
        Endpoint: GET /api/usuarios/buscar/?q=termo&limit=20
        """
        user = request.user

        # Queryset base: apenas usuários públicos e ativos
        queryset = Usuario.objects.filter(ativo=True, perfil_publico=True)

        # Excluir o próprio usuário
        if user.is_authenticated:
            queryset = queryset.exclude(uuid=user.uuid)

        # Filtro de busca
        termo = request.query_params.get("q", "").strip()
        if termo:
            queryset = queryset.filter(
                Q(nome_completo__icontains=termo)
                | Q(pais_residencia__icontains=termo)
                | Q(cidade_residencia__icontains=termo)
                | Q(biografia__icontains=termo)
            )

        # Ordenação
        queryset = queryset.order_by("-data_criacao")

        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
