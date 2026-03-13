from django.urls import path
from . import views
 
app_name = 'chat'
 
urlpatterns = [
    # ── Existentes ──────────────────────────────────────────────────────────
    path('conversas/', views.view_lista_conversas, name='conversas'),
    path('conversa/<uuid:uuid_conversa>/', views.view_conversa, name='conversa'),
    path('iniciar/<uuid:uuid_usuario>/', views.view_iniciar_conversa, name='iniciar_conversa'),
 
    # ── Mensagens ───────────────────────────────────────────────────────────
    path('conversa/<uuid:uuid_conversa>/enviar/', views.view_enviar_mensagem, name='enviar_mensagem'),
    path('conversa/<uuid:uuid_conversa>/mensagens/', views.view_mensagens_json, name='mensagens_json'),
    path('mensagem/<int:mensagem_id>/apagar/', views.view_apagar_mensagem, name='apagar_mensagem'),
 
    # ── Polling e status ────────────────────────────────────────────────────
    path('nao-lidas/', views.view_nao_lidas_json, name='nao_lidas_json'),
    path('conversa/<uuid:uuid_conversa>/digitando/', views.view_digitando, name='digitando'),
    path('conversa/<uuid:uuid_conversa>/parou-digitar/', views.view_parou_digitar, name='parou_digitar'),
]
 