from django.urls import path
from . import views

app_name = 'destinos'

urlpatterns = [
    # Criar plano
    path('criar-plano/', views.view_criar_plano_viagem, name='criar_plano'),
    # Buscar viajantes
    path('viajantes/', views.view_buscar_viajantes, name='buscar_viajantes'),
    path('buscar/', views.view_buscar_viajantes, name='buscar'),
    
    # Detalhes do plano
    path('<uuid:uuid>/', views.view_detalhes_plano, name='detalhes_plano'),
    
    # APIs
    path('api/paises/autocomplete/', views.api_paises_autocomplete, name='api_paises'),
    path('api/estatisticas/<int:pais_id>/', views.api_estatisticas_destino, name='api_estatisticas'),
]
