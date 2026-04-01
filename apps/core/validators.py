"""
apps/core/validators.py
Validadores reutilizáveis para todo o projeto.
Cobre: idade mínima (18 anos), e-mail (formato, DNS, descartáveis), senha forte.
"""

import re
import socket
from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# ──────────────────────────────────────────────────────────────────────────────
#  DOMÍNIOS DE E-MAIL TEMPORÁRIOS / DESCARTÁVEIS
# ──────────────────────────────────────────────────────────────────────────────

_DOMINIOS_TEMPORARIOS: frozenset[str] = frozenset(
    {
        "mailinator.com",
        "guerrillamail.com",
        "guerrillamail.net",
        "guerrillamail.org",
        "guerrillamail.biz",
        "guerrillamail.de",
        "guerrillamail.info",
        "throwam.com",
        "tempmail.com",
        "temp-mail.org",
        "10minutemail.com",
        "10minutemail.net",
        "10minutemail.org",
        "sharklasers.com",
        "guerrillamailblock.com",
        "grr.la",
        "spam4.me",
        "yopmail.com",
        "yopmail.fr",
        "cool.fr.nf",
        "jetable.fr.nf",
        "nospam.ze.tc",
        "nomail.xl.cx",
        "mega.zik.dj",
        "speed.1s.fr",
        "trashmail.at",
        "trashmail.com",
        "trashmail.io",
        "trashmail.me",
        "trashmail.net",
        "trashmail.org",
        "trashmail.xyz",
        "dispostable.com",
        "fakeinbox.com",
        "maildrop.cc",
        "mailnull.com",
        "mailnesia.com",
        "spamgourmet.com",
        "spamgourmet.net",
        "spamgourmet.org",
        "discard.email",
        "spamspot.com",
        "spam.la",
        "spamfree24.org",
        "spamfree24.de",
        "spamfree24.eu",
        "getairmail.com",
        "filzmail.com",
        "wegwerfmail.de",
        "wegwerfmail.net",
        "wegwerfmail.org",
        "mohmal.com",
        "getnada.com",
    }
)


# ──────────────────────────────────────────────────────────────────────────────
#  VALIDADOR DE IDADE MÍNIMA
# ──────────────────────────────────────────────────────────────────────────────


class IdadeMinimaValidator:
    """
    Garante que o usuário tem no mínimo `idade_minima` anos completos.

    Uso no model:
        data_nascimento = models.DateField(
            validators=[IdadeMinimaValidator(18)]
        )

    Uso em serializer / form:
        def validate_data_nascimento(self, value):
            IdadeMinimaValidator(18)(value)
            return value
    """

    def __init__(self, idade_minima: int = 18):
        self.idade_minima = idade_minima

    def __call__(self, data_nascimento: date) -> None:
        if not isinstance(data_nascimento, date):
            raise ValidationError(_("Data de nascimento inválida."))

        hoje = date.today()
        try:
            aniversario_este_ano = data_nascimento.replace(year=hoje.year)
        except ValueError:
            # 29/02 em ano não bissexto -> trata como 28/02
            aniversario_este_ano = data_nascimento.replace(year=hoje.year, day=28)

        idade = hoje.year - data_nascimento.year
        if aniversario_este_ano > hoje:
            idade -= 1

        if idade < self.idade_minima:
            raise ValidationError(
                _("E necessario ter pelo menos %(idade)s anos para se cadastrar."),
                code="idade_minima",
                params={"idade": self.idade_minima},
            )

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [self.idade_minima],
            {},
        )


# ──────────────────────────────────────────────────────────────────────────────
#  VALIDADOR DE E-MAIL
# ──────────────────────────────────────────────────────────────────────────────

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def _dominio_existe_no_dns(dominio: str) -> bool:
    """Verifica se o dominio possui registro A/AAAA. Timeout de 5s."""
    try:
        socket.setdefaulttimeout(5)
        socket.getaddrinfo(dominio, None)
        return True
    except (socket.gaierror, socket.timeout):
        return False


class EmailValidator:
    """
    Validacao completa de e-mail em tres etapas:
    1. Formato via regex (RFC 5322 simplificado)
    2. Bloqueia dominios temporarios/descartaveis conhecidos
    3. Verifica existencia do dominio no DNS

    Uso em serializer:
        email = serializers.EmailField(validators=[EmailValidator()])

    Uso standalone:
        EmailValidator()("usuario@exemplo.com")
    """

    def __call__(self, email: str) -> None:
        email = (email or "").strip().lower()

        if not _EMAIL_REGEX.match(email):
            raise ValidationError(
                _("Endereco de e-mail invalido."),
                code="email_formato_invalido",
            )

        dominio = email.split("@", 1)[1]

        if dominio in _DOMINIOS_TEMPORARIOS:
            raise ValidationError(
                _("E-mails temporarios ou descartaveis nao sao permitidos."),
                code="email_temporario",
            )

        if not _dominio_existe_no_dns(dominio):
            raise ValidationError(
                _(
                    "O dominio deste e-mail nao pude ser verificado. "
                    "Verifique se o endereco esta correto."
                ),
                code="email_dominio_invalido",
            )


# ──────────────────────────────────────────────────────────────────────────────
#  VALIDADOR DE SENHA FORTE
# ──────────────────────────────────────────────────────────────────────────────


class SenhaForteValidator:
    """
    Compativel com AUTH_PASSWORD_VALIDATORS do Django.
    Exige: maiuscula, minuscula, digito e caractere especial.
    """

    _ESPECIAIS = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>?/\\|`~]")

    def validate(self, password: str, user=None) -> None:
        erros = []
        if not re.search(r"[A-Z]", password):
            erros.append(_("A senha deve conter pelo menos uma letra maiuscula."))
        if not re.search(r"[a-z]", password):
            erros.append(_("A senha deve conter pelo menos uma letra minuscula."))
        if not re.search(r"\d", password):
            erros.append(_("A senha deve conter pelo menos um numero."))
        if not self._ESPECIAIS.search(password):
            erros.append(_("A senha deve conter pelo menos um caractere especial."))
        if erros:
            raise ValidationError(erros)

    def get_help_text(self) -> str:
        return _(
            "Sua senha deve conter letras maiusculas, minusculas, "
            "numeros e pelo menos um caractere especial."
        )


def validar_senha_segura(senha: str) -> tuple[bool, list[str]]:
    """
    Versao funcional do SenhaForteValidator — usada em utils e testes.

    Returns:
        (e_valida, lista_de_erros)
    """
    erros: list[str] = []

    if len(senha) < 8:
        erros.append("Senha deve ter no minimo 8 caracteres.")
    if not any(c.isupper() for c in senha):
        erros.append("Senha deve conter pelo menos uma letra maiuscula.")
    if not any(c.islower() for c in senha):
        erros.append("Senha deve conter pelo menos uma letra minuscula.")
    if not any(c.isdigit() for c in senha):
        erros.append("Senha deve conter pelo menos um numero.")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>?/\\|`~]", senha):
        erros.append("Senha deve conter pelo menos um caractere especial.")

    return len(erros) == 0, erros
