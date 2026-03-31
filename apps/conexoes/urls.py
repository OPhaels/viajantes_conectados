from django.urls import path

from . import views

app_name = "conexoes"

urlpatterns = [
    path("solicitacoes/", views.view_lista_solicitacoes, name="solicitacoes"),
    path(
        "enviar-solicitacao/<uuid:uuid_destinatario>/",
        views.enviar_solicitacao,
        name="enviar_solicitacao",
    ),
    path(
        "responder-solicitacao/<uuid:uuid_solicitacao>/<str:acao>/",
        views.view_responder_solicitacao,
        name="responder_solicitacao",
    ),
    path(
        "cancelar-solicitacao/<uuid:uuid_solicitacao>/",
        views.view_cancelar_solicitacao,
        name="cancelar_solicitacao",
    ),
    path("amigos/", views.view_lista_amigos, name="amigos"),
    path(
        "desfazer-amizade/<uuid:uuid_amigo>/",
        views.view_desfazer_amizade,
        name="desfazer_amizade",
    ),
    path(
        "desfazer-amizade-ajax/<uuid:uuid_amigo>/",
        views.view_desfazer_amizade_ajax,
        name="desfazer_amizade_ajax",
    ),
    path(
        "bloquear/<uuid:uuid_usuario>/",
        views.view_bloquear_usuario,
        name="bloquear_usuario",
    ),
    path(
        "desbloquear/<uuid:uuid_usuario>/",
        views.view_desbloquear_usuario,
        name="desbloquear_usuario",
    ),
]
