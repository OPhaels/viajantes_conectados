from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .viewsets import PaisViewSet, PlanoViagemViewSet

app_name = 'destinos'

# Router para APIs REST
router = DefaultRouter()
router.register(r'api/paises', PaisViewSet, basename='pais')
router.register(r'api/planos', PlanoViagemViewSet, basename='plano')

urlpatterns = [
    # Views principais
    path('criar-plano/', views.view_criar_plano_viagem, name='criar_plano'),
    path('meus-planos/', views.view_meus_planos, name='meus_planos'),
    path('viajantes/', views.view_buscar_viajantes, name='buscar_viajantes'),
    path('buscar-viajantes/', views.view_listar_viajantes, name='listar_viajantes'),
    path('buscar/', views.view_buscar_viajantes, name='buscar'),
    
    # Detalhes e Ações
    path('<uuid:uuid>/', views.view_detalhes_plano, name='detalhes_plano'),
    path('<uuid:uuid>/deletar/', views.view_deletar_plano, name='deletar_plano'),
    
    # APIs Legacy (será descontinuado)
    path('api/paises/autocomplete/', views.api_paises_autocomplete, name='api_paises'),
    path('api/estatisticas/<int:pais_id>/', views.api_estatisticas_destino, name='api_estatisticas'),
    
    # API REST Router
    path('', include(router.urls)),
]
