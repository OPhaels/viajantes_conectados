from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.static import serve  

def view_home(request):
    contexto = {}

    if request.user.is_authenticated:
        from apps.destinos.models import PlanoViagem
        from apps.conexoes.models import SolicitacaoAmizade, Amizade
        from apps.usuarios.models import Usuario

        usuario = request.user

        # Planos recentes do usuário (até 6)
        planos_recentes = PlanoViagem.objects.filter(
            usuario=usuario
        ).select_related('pais_destino').order_by('-data_criacao')[:6]

        # Contagem total de planos
        planos_count = PlanoViagem.objects.filter(usuario=usuario).count()

        # Contagem de amigos
        amigos_count = Amizade.objects.filter(
            usuario1=usuario
        ).count() + Amizade.objects.filter(
            usuario2=usuario
        ).count()

        # Solicitações pendentes recebidas
        solicitacoes_pendentes = SolicitacaoAmizade.objects.filter(
            destinatario=usuario,
            status='pendente'
        ).count()

        # Viajantes com destinos similares (excluindo o próprio usuário e amigos)
        destinos_usuario = PlanoViagem.objects.filter(
            usuario=usuario
        ).values_list('pais_destino', flat=True)

        amigos_ids = list(Amizade.objects.filter(
            usuario1=usuario
        ).values_list('usuario2', flat=True)) + list(
            Amizade.objects.filter(
                usuario2=usuario
            ).values_list('usuario1', flat=True)
        )

        viajantes_sugeridos = Usuario.objects.filter(
            planos_viagem__pais_destino__in=destinos_usuario, 
            perfil_publico=True,
            ativo=True
        ).exclude(
            id=usuario.id
        ).exclude(
            id__in=amigos_ids
        ).distinct()[:8]

        contexto = {
            'planos_recentes':        planos_recentes,
            'planos_count':           planos_count,
            'amigos_count':           amigos_count,
            'solicitacoes_pendentes': solicitacoes_pendentes,
            'viajantes_sugeridos':    viajantes_sugeridos,
        }

    return render(request, 'home.html', contexto)


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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# Handlers de erro
handler404 = view_pagina_404
handler500 = view_pagina_500
handler403 = view_pagina_403