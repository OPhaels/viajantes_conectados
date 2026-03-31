from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    # ── Conversas ───────────────────────────────────────────────────────────
    path("conversas/", views.view_lista_conversas, name="conversas"),
    path("conversa/<uuid:uuid_conversa>/", views.view_conversa, name="conversa"),
    path(
        "iniciar/<uuid:uuid_usuario>/",
        views.view_iniciar_conversa,
        name="iniciar_conversa",
    ),
    path(
        "iniciar/<uuid:uuid_usuario>/viagem/<uuid:uuid_plano>/",
        views.view_iniciar_conversa_viagem,
        name="iniciar_conversa_viagem",
    ),
    # ── Mensagens ───────────────────────────────────────────────────────────
    path(
        "conversa/<uuid:uuid_conversa>/enviar/",
        views.view_enviar_mensagem,
        name="enviar_mensagem",
    ),
    path(
        "conversa/<uuid:uuid_conversa>/mensagens/",
        views.view_mensagens_json,
        name="mensagens_json",
    ),
    path(
        "conversa/<uuid:uuid_conversa>/apagar/",
        views.view_apagar_conversa,
        name="apagar_conversa",
    ),
    path(
        "mensagem/<int:mensagem_id>/apagar/",
        views.view_apagar_mensagem,
        name="apagar_mensagem",
    ),
    # ── Polling e status ────────────────────────────────────────────────────
    path("nao-lidas/", views.view_nao_lidas_json, name="nao_lidas_json"),
    path(
        "nao-lidas/detalhes/",
        views.view_nao_lidas_detalhes_json,
        name="nao_lidas_detalhes",
    ),
    path(
        "conversa/<uuid:uuid_conversa>/digitando/",
        views.view_digitando,
        name="digitando",
    ),
    path(
        "conversa/<uuid:uuid_conversa>/parou-digitar/",
        views.view_parou_digitar,
        name="parou_digitar",
    ),
    # ── Amizade / Bloqueio ──────────────────────────────────────────────────
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
    path(
        "desfazer-amizade/<uuid:uuid_amigo>/",
        views.view_desfazer_amizade_ajax,
        name="desfazer_amizade_ajax",
    ),
]
