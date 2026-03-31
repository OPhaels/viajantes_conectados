from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .viewsets import UsuarioViewSet

app_name = "usuarios"

# Router para APIs REST
router = DefaultRouter()
router.register(r"api/usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    # Views principais
    path("cadastro/", views.view_cadastro_usuario, name="cadastro"),
    path("login/", views.view_login_usuario, name="login"),
    path("logout/", views.view_logout_usuario, name="logout"),
    path("perfil/", views.view_perfil_usuario, name="perfil"),
    path("perfil/<uuid:uuid>/", views.view_perfil_usuario, name="perfil_publico"),
    path("editar-perfil/", views.view_editar_perfil, name="editar_perfil"),
    # API REST Router
    path("", include(router.urls)),
]
