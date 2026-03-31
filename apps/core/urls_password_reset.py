from django.urls import path

from .views_password_reset import password_reset_confirm, password_reset_request

urlpatterns = [
    path("password-reset/", password_reset_request, name="password_reset"),
    path(
        "reset-password/<uidb64>/<token>/",
        password_reset_confirm,
        name="password_reset_confirm",
    ),
]
