from django.urls import path
from . import views

app_name = 'destinos'

urlpatterns = [
    path('buscar/', views.view_buscar_viajantes, name='buscar'),
    path('criar-plano/', views.view_criar_plano_viagem, name='criar_plano'),
    path('plano/<uuid:uuid>/', views.view_detalhes_plano, name='detalhes_plano'),
    
    # APIs
    path('api/paises/', views.api_paises_autocomplete, name='api_paises'),
    path(
        'api/estatisticas/<int:pais_id>/',
        views.api_estatisticas_destino,
        name='api_estatisticas'
    ),
]

