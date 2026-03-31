import logging
import threading

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

logger = logging.getLogger(__name__)

User = get_user_model()


def _enviar_email_reset(html_content, text_content, user_email):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [user_email],
                "subject": "Redefinição de senha - Viajantes Conectados",
                "html": html_content,
                "text": text_content,
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Email de reset enviado para: {user_email}")
    except Exception as e:
        logger.error(f"Erro ao enviar email de reset para {user_email}: {str(e)}")


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(Q(email__iexact=email))

            if users.exists():
                for user in users:
                    token = default_token_generator.make_token(user)
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                    reset_path = reverse(
                        "password_reset_confirm",
                        kwargs={"uidb64": uidb64, "token": token},
                    )
                    reset_url = f"{settings.SITE_URL.rstrip('/')}{reset_path}"

                    html_content = render_to_string(
                        "registration/password_reset_email.html",
                        {"user": user, "reset_url": reset_url},
                    )

                    text_content = (
                        f"Olá,\n\n"
                        f"Recebemos uma solicitação para redefinir sua senha.\n\n"
                        f"Acesse o link abaixo:\n{reset_url}\n\n"
                        f"Se você não solicitou, ignore este e-mail."
                    )

                    threading.Thread(
                        target=_enviar_email_reset,
                        args=(html_content, text_content, user.email),
                        daemon=True,
                    ).start()

            messages.info(
                request,
                "Se o e-mail existir, você receberá instruções para redefinir sua senha.",
            )
            return redirect("usuarios:login")

        else:
            messages.error(request, "Formulário inválido.")

    else:
        form = PasswordResetForm()

    return render(request, "registration/password_reset_form.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    user = None

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)

            if form.is_valid():
                form.save()
                logger.info(f"Senha redefinida com sucesso: {user.email}")
                messages.success(request, "Senha redefinida com sucesso!")
                return redirect("usuarios:login")
            else:
                messages.error(request, "Corrija os erros abaixo.")
        else:
            form = SetPasswordForm(user)

        return render(
            request, "registration/password_reset_confirm.html", {"form": form}
        )

    else:
        messages.error(request, "Link inválido ou expirado.")
        return redirect("usuarios:login")
