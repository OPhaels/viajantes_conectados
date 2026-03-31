"""
Validadores customizados para toda a aplicação.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SenhaForteValidator:
    """
    Valida se a senha atende aos critérios de segurança.

    Critérios:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial (!@#$%^&*)
    """

    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("A senha deve ter pelo menos 8 caracteres."),
                code="password_too_short",
            )

        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("A senha deve conter pelo menos uma letra maiúscula."),
                code="password_no_upper",
            )

        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("A senha deve conter pelo menos uma letra minúscula."),
                code="password_no_lower",
            )

        if not re.search(r"\d", password):
            raise ValidationError(
                _("A senha deve conter pelo menos um número."),
                code="password_no_digit",
            )

        if not re.search(r"[!@#$%^&*]", password):
            raise ValidationError(
                _("A senha deve conter pelo menos um caractere especial (!@#$%^&*)."),
                code="password_no_special",
            )

    def get_help_text(self):
        return _(
            "Sua senha deve ter pelo menos 8 caracteres e conter pelo menos "
            "uma letra maiúscula, uma letra minúscula, um número e um "
            "caractere especial (!@#$%^&*)."
        )
