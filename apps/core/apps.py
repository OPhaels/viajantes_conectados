from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core - Utilities e Configurações Centralizadas'
    
    def ready(self):
        """Executado quando a aplicação está pronta."""
        # Importar signals ou outras configurações de inicialização aqui se necessário
        pass
