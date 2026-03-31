"""
Permissões customizadas para a API REST.
Centraliza a lógica de autorização da aplicação.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import permissions


class EhProprietarioOuLeitura(permissions.BasePermission):
    """
    Permite acesso de leitura para qualquer um e escrita apenas ao proprietário.
    """

    message = _("Você não tem permissão para modificar este recurso.")

    def has_object_permission(self, request, view, obj):
        # Leitura é permitida para qualquer um
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita é permitida apenas ao proprietário
        return obj.usuario == request.user


class EhProprietario(permissions.BasePermission):
    """
    Permite acesso apenas ao proprietário do recurso.
    """

    message = _("Você não tem permissão para acessar este recurso.")

    def has_object_permission(self, request, view, obj):
        return obj.usuario == request.user


class EmailVerificado(permissions.BasePermission):
    """
    Permite acesso apenas a usuários que verificaram seu email.
    """

    message = _("Você precisa verificar seu email para acessar este recurso.")

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email_verificado


class ContaAtiva(permissions.BasePermission):
    """
    Permite acesso apenas a usuários com conta ativa.
    """

    message = _("Sua conta não está ativa.")

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.ativo


class NaoEstaBloqueado(permissions.BasePermission):
    """
    Permite acesso apenas a usuários que não estão bloqueados.
    """

    message = _("Sua conta está temporariamente bloqueada.")

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return not request.user.esta_bloqueado()


class EhAdminOuReadOnly(permissions.BasePermission):
    """
    Permite escrita apenas para administradores, leitura para todos.
    """

    message = _("Apenas administradores podem modificar este recurso.")

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
