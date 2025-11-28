from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.shortcuts import render


def view_home(request):
    """View para a página inicial."""
    return render(request, 'home.html')


def view_pagina_404(request, exception):
    """View customizada para erro 404."""
    return render(request, 'erros/404.html', status=404)


def view_pagina_500(request):
    """View customizada para erro 500."""
    return render(request, 'erros/500.html', status=500)


def view_pagina_403(request, exception):
    """View customizada para erro 403."""
    return render(request, 'erros/403.html', status=403)


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Página inicial
    path('', view_home, name='home'),
    
    # Apps
    path('usuarios/', include('apps.usuarios.urls')),
    path('destinos/', include('apps.destinos.urls')),
    path('conexoes/', include('apps.conexoes.urls')),
    path('chat/', include('apps.chat.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Adicionar Django Debug Toolbar se instalado
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Handlers de erro customizados
handler404 = view_pagina_404
handler500 = view_pagina_500
handler403 = view_pagina_403