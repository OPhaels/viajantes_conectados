from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('cadastro/', views.view_cadastro_usuario, name='cadastro'),
    path('login/', views.view_login_usuario, name='login'),
    path('logout/', views.view_logout_usuario, name='logout'),
    path('perfil/', views.view_perfil_usuario, name='perfil'),
    path('perfil/<uuid:uuid>/', views.view_perfil_usuario, name='perfil_publico'),
    path('editar-perfil/', views.view_editar_perfil, name='editar_perfil'),
]