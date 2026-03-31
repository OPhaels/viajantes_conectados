from django.urls import path

from .views import get_cookie_view, set_cookie_view

urlpatterns = [
    path("set-cookie/", set_cookie_view, name="set_cookie"),
    path("get-cookie/", get_cookie_view, name="get_cookie"),
]
