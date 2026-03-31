from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(Q(email__iexact=email))

            # ⚠️ segurança: não revela se o email existe
            if users.exists():
                for user in users:
                    try:
                        subject = "Redefinição de senha - Viajantes Conectados"

                        token = default_token_generator.make_token(user)
                        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                        # ✅ URL correta usando reverse
                        reset_path = reverse(
                            "password_reset_confirm",
                            kwargs={"uidb64": uidb64, "token": token},
                        )

                        reset_url = f"{settings.SITE_URL}{reset_path}"

                        # HTML do e-mail
                        html_content = render_to_string(
                            "registration/password_reset_email.html",
                            {
                                "user": user,
                                "reset_url": reset_url,
                            },
                        )

                        # Texto simples (fallback)
                        text_content = f"""
Olá,

Recebemos uma solicitação para redefinir sua senha.

Acesse o link abaixo:
{reset_url}

Se você não solicitou, ignore este e-mail.
"""

                        email_msg = EmailMultiAlternatives(
                            subject,
                            text_content,
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                        )

                        email_msg.attach_alternative(html_content, "text/html")
                        email_msg.send()

                    except Exception:
                        messages.error(
                            request,
                            "Erro ao enviar o e-mail. Tente novamente mais tarde.",
                        )
                        return redirect("password_reset")

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
