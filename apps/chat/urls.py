from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('conversas/', views.view_lista_conversas, name='conversas'),
    path('conversa/<uuid:uuid_conversa>/', views.view_conversa, name='conversa'),
    path(
        'iniciar/<uuid:uuid_usuario>/',
        views.view_iniciar_conversa,
        name='iniciar_conversa'
    ),
]
