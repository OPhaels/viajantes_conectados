from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.static import serve  

def view_home(request):
    return render(request, 'home.html')

def view_pagina_404(request, exception):
    return render(request, 'erros/404.html', status=404)

def view_pagina_500(request):
    return render(request, 'erros/500.html', status=500)

def view_pagina_403(request, exception):
    return render(request, 'erros/403.html', status=403)

# URLs principais
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view_home, name='home'),

    # JWT
    path('api-token-auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api-token-auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Apps
    path('usuarios/', include('apps.usuarios.urls')),
    path('destinos/', include('apps.destinos.urls')),
    path('conexoes/', include('apps.conexoes.urls')),
    path('chat/', include('apps.chat.urls')),
]

# Servir arquivos estáticos e mídia
if settings.DEBUG:
    # Desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    # Produção: serve mídia manualmente via Django (Railway não serve automaticamente)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# Handlers de erro
handler404 = view_pagina_404
handler500 = view_pagina_500
handler403 = view_pagina_403