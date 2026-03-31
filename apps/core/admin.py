from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import LogAuditoria, TentativaLoginFalhado


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    """Admin para logs de auditoria."""

    list_display = (
        "timestamp",
        "tipo_acao",
        "usuario_email",
        "ip_address",
        "resultado",
        "requer_investigacao",
    )
    list_filter = ("tipo_acao", "resultado", "requer_investigacao", "timestamp")
    search_fields = ("usuario_email", "ip_address", "endpoint")
    readonly_fields = (
        "id",
        "timestamp",
        "usuario_email",
        "ip_address",
        "user_agent",
        "metodo_http",
        "codigo_resposta",
        "endpoint",
        "dados_alterados",
    )
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    fieldsets = (
        (
            _("Informações Básicas"),
            {"fields": ("id", "timestamp", "tipo_acao", "descricao", "resultado")},
        ),
        (_("Usuário"), {"fields": ("usuario", "usuario_email")}),
        (
            _("Requisição"),
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "metodo_http",
                    "endpoint",
                    "codigo_resposta",
                )
            },
        ),
        (
            _("Dados Adicionais"),
            {
                "fields": ("dados_alterados", "detalhes_erro", "requer_investigacao"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Não permitir adicionar logs manualmente (são auto-registrados)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Não permitir deletar logs de auditoria."""
        return False

    def has_change_permission(self, request, obj=None):
        """Permitir marcar como 'requer investigação' apenas."""
        return True if obj is None else False


@admin.register(TentativaLoginFalhado)
class TentativaLoginFalhadoAdmin(admin.ModelAdmin):
    """Admin para tentativas de login falhadas."""

    list_display = ("timestamp", "email_tentativa", "ip_address", "motivo", "usuario")
    list_filter = ("motivo", "timestamp")
    search_fields = ("email_tentativa", "ip_address", "usuario__email")
    readonly_fields = (
        "id",
        "timestamp",
        "email_tentativa",
        "ip_address",
        "user_agent",
        "motivo",
        "usuario",
    )
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    fieldsets = (
        (
            _("Informações Básicas"),
            {"fields": ("id", "timestamp", "email_tentativa", "motivo")},
        ),
        (_("Requisição"), {"fields": ("ip_address", "user_agent")}),
        (_("Usuário"), {"fields": ("usuario",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        """Não permitir adicionar registros manualmente."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Não permitir deletar tentativas de login."""
        return False


# Configuração do site admin
admin.site.site_header = _("Administração - Viajantes Conectados")
admin.site.site_title = _("Viajantes Conectados Admin")
admin.site.index_title = _("Bem-vindo ao Painel Administrativo")
