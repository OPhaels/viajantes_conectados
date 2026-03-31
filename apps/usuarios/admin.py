from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("email", "nome_completo", "is_staff", "email_verificado", "ativo")
    search_fields = ("email", "nome_completo")
