"""
Exceções customizadas para a aplicação.
Centraliza o tratamento de erros de forma consistente.
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _


class BaseAPIException(APIException):
    """Classe base para exceções da API."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'error'
    
    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        
        super().__init__(detail=detail, code=code)


class UsuarioNaoEncontradoException(BaseAPIException):
    """Usuário não encontrado."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('Usuário não encontrado.')
    default_code = 'usuario_nao_encontrado'


class PermissaoNegadaException(BaseAPIException):
    """Usuário não tem permissão para acessar esse recurso."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Você não tem permissão para acessar este recurso.')
    default_code = 'permissao_negada'


class UniqueConstraintException(BaseAPIException):
    """Violação de restrição de unicidade."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Este recurso já existe.')
    default_code = 'unique_constraint'


class RateLimitException(BaseAPIException):
    """Limite de taxa excedido."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('Você excedeu o limite de solicitações. Tente novamente mais tarde.')
    default_code = 'rate_limit'


class ValidacaoDadosException(BaseAPIException):
    """Erro de validação de dados."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = _('Os dados fornecidos são inválidos.')
    default_code = 'validacao_falhou'


class RecursoNaoDisponevelException(BaseAPIException):
    """Recurso não está disponível."""
    status_code = status.HTTP_410_GONE
    default_detail = _('O recurso solicitado não está disponível.')
    default_code = 'recurso_nao_disponivel'
