"""
Middleware para auditoria e segurança da aplicação.
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

from .models import LogAuditoria

logger = logging.getLogger(__name__)


class TratamentoErrosMiddleware:
    """
    Middleware para tratamento centralizado de erros.

    Captura exceções não tratadas e retorna respostas apropriadas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self._tratar_erro(request, e)

    def _tratar_erro(self, request, exception):
        """Trata diferentes tipos de erro de forma apropriada."""

        # Log do erro
        logger.error(
            f"Erro não tratado: {type(exception).__name__}: {str(exception)}",
            exc_info=True,
            extra={
                "path": request.path,
                "method": request.method,
                "user": (
                    request.user.username
                    if request.user.is_authenticated
                    else "anonymous"
                ),
                "ip": self._get_client_ip(request),
            },
        )

        # Se for uma requisição AJAX/API, retorna JSON
        if self._is_ajax_request(request) or request.path.startswith("/api/"):
            return self._resposta_erro_api(exception)

        # Para requisições normais, retorna página de erro
        return self._resposta_erro_html(request, exception)

    def _is_ajax_request(self, request):
        """Verifica se é uma requisição AJAX."""
        return (
            request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
            or request.META.get("HTTP_ACCEPT", "").find("application/json") >= 0
        )

    def _resposta_erro_api(self, exception):
        """Retorna resposta de erro em formato JSON."""

        if isinstance(exception, APIException):
            return JsonResponse(
                {
                    "error": str(exception.detail),
                    "code": exception.get_codes(),
                },
                status=exception.status_code,
            )

        elif isinstance(exception, (ValidationError, ValueError)):
            return JsonResponse(
                {
                    "error": "Dados inválidos.",
                    "details": str(exception),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        elif isinstance(exception, PermissionDenied):
            return JsonResponse(
                {
                    "error": "Acesso negado.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        elif isinstance(exception, (DatabaseError, IntegrityError)):
            return JsonResponse(
                {
                    "error": "Erro interno do servidor.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        else:
            return JsonResponse(
                {
                    "error": "Erro interno do servidor.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _resposta_erro_html(self, request, exception):
        """Retorna página de erro HTML."""

        if isinstance(exception, PermissionDenied):
            return render(request, "erros/403.html", status=403)

        # Para outros erros, retorna página 500
        return render(request, "erros/500.html", status=500)

    def _get_client_ip(self, request):
        """Obtém o IP real do cliente."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class AuditoriaMiddleware:
    """
    Middleware que registra automaticamente ações sensíveis para auditoria.

    Registra:
    - Tentativas de login (sucesso/falha)
    - Acessos negados
    - Alterações de dados sensíveis
    - Atividades suspeitas
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Endpoints que requerem auditoria especial
        self.endpoints_auditoria = [
            "/api/auth/login/",
            "/api/auth/register/",
            "/api/usuarios/me/",
            "/api/usuarios/change-password/",
            "/api/conexoes/solicitacoes/",
            "/api/chat/mensagens/",
            "/admin/",
        ]

    def __call__(self, request):
        # Antes da requisição
        self._registrar_acesso_inicial(request)

        response = self.get_response(request)

        # Depois da requisição
        self._registrar_resultado(request, response)

        return response

    def _registrar_acesso_inicial(self, request):
        """Registra o início de uma requisição sensível."""
        if self._deve_auditar(request):
            # Armazenar informações iniciais no request para uso posterior
            request._audit_start_time = timezone.now()
            request._audit_ip = self._get_client_ip(request)
            request._audit_user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

    def _registrar_resultado(self, request, response):
        """Registra o resultado da requisição."""
        if not hasattr(request, "_audit_start_time"):
            return

        try:
            tipo_acao = self._determinar_tipo_acao(request, response)
            if tipo_acao:
                self._criar_log_auditoria(request, response, tipo_acao)
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {str(e)}")

    def _deve_auditar(self, request):
        """Verifica se a requisição deve ser auditada."""
        path = request.path

        # Auditar endpoints específicos
        for endpoint in self.endpoints_auditoria:
            if path.startswith(endpoint):
                return True

        # Auditar métodos perigosos em qualquer endpoint
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True

        # Auditar acessos não autenticados a recursos protegidos
        if path.startswith("/api/") and not request.user.is_authenticated:
            return True

        return False

    def _determinar_tipo_acao(self, request, response):
        """Determina o tipo de ação baseado na requisição e resposta."""
        path = request.path
        method = request.method
        status = response.status_code

        # Login
        if "login" in path and method == "POST":
            return "login_sucesso" if status == 200 else "login_falha"

        # Registro
        if "register" in path and method == "POST":
            return "registro_novo_usuario" if status in [200, 201] else None

        # Alteração de senha
        if "change-password" in path and method == "POST":
            return "alterar_senha" if status == 200 else None

        # Acesso negado
        if status == 401:
            return "acesso_negado_autenticacao"
        elif status == 403:
            return "acesso_negado_permissao"

        # Outros casos
        if method in ["POST", "PUT", "PATCH", "DELETE"] and status in [200, 201, 204]:
            if "usuarios" in path:
                return "alterar_perfil"
            elif "conexoes" in path:
                return "solicitacao_amizade_enviada"
            elif "chat" in path:
                return "enviar_mensagem"

        return None

    def _criar_log_auditoria(self, request, response, tipo_acao):
        """Cria o registro de auditoria."""
        try:
            dados_alterados = {}

            # Tentar extrair dados alterados do request
            if hasattr(request, "data") and request.data:
                # Para DRF requests
                dados_alterados = dict(request.data)
            elif request.POST:
                dados_alterados = dict(request.POST)

            # Remover campos sensíveis dos dados
            campos_sensiveis = ["password", "password2", "old_password", "token"]
            for campo in campos_sensiveis:
                dados_alterados.pop(campo, None)

            LogAuditoria.objects.create(
                tipo_acao=tipo_acao,
                descricao=f"{request.method} {request.path}",
                usuario=request.user if request.user.is_authenticated else None,
                usuario_email=getattr(request.user, "email", "anonimo"),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                resultado=response.status_code < 400,
                detalhes_erro=(
                    "" if response.status_code < 400 else f"HTTP {response.status_code}"
                ),
                metodo_http=request.method,
                endpoint=request.path[:500],
                codigo_resposta=response.status_code,
                dados_alterados=dados_alterados,
            )
        except Exception as e:
            logger.error(f"Erro ao criar log de auditoria: {str(e)}")

    def _get_client_ip(self, request):
        """Obtém o IP real do cliente considerando proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
