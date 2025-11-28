from django.urls import path
from . import views

app_name = 'conexoes'

urlpatterns = [
    # Solicitações de amizade
    path(
        'solicitacoes/',
        views.view_lista_solicitacoes,
        name='solicitacoes'
    ),
    path(
        'enviar-solicitacao/<uuid:uuid_usuario>/',
        views.view_enviar_solicitacao_amizade,
        name='enviar_solicitacao'
    ),
    path(
        'responder-solicitacao/<uuid:uuid_solicitacao>/<str:acao>/',
        views.view_responder_solicitacao,
        name='responder_solicitacao'
    ),
    path(
        'cancelar-solicitacao/<uuid:uuid_solicitacao>/',
        views.view_cancelar_solicitacao,
        name='cancelar_solicitacao'
    ),
    
    # Amizades
    path(
        'amigos/',
        views.view_lista_amigos,
        name='amigos'
    ),
    path(
        'desfazer-amizade/<uuid:uuid_amigo>/',
        views.view_desfazer_amizade,
        name='desfazer_amizade'
    ),
    ]