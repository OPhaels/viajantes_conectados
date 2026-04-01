from django.urls import path

from apps.core.views import politica_privacidade, termos_de_uso

from .views import get_cookie_view, set_cookie_view

urlpatterns = [
    path("set-cookie/", set_cookie_view, name="set_cookie"),
    path("get-cookie/", get_cookie_view, name="get_cookie"),
    path("legal/termos/", termos_de_uso, name="termos_de_uso"),
    path("legal/privacidade/", politica_privacidade, name="politica_privacidade"),
]
