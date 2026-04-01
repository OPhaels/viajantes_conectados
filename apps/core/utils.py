"""
apps/core/utils.py
Funções utilitárias comuns para toda a aplicação.
Evita redundância de código entre os apps.
"""

import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
#  E-MAIL
# ──────────────────────────────────────────────────────────────────────────────


def enviar_email_assincrono(
    destino: str, assunto: str, mensagem: str, template: str | None = None
) -> bool:
    """
    Envia e-mail em thread separada para não bloquear a requisição.
    Retorna True imediatamente (o envio ocorre em background).
    """

    def _enviar():
        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destino],
                html_message=template,
                fail_silently=False,
            )
            logger.info(f"E-mail enviado para: {destino}")
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail para {destino}: {e}")

    threading.Thread(target=_enviar, daemon=True).start()
    return True


# ──────────────────────────────────────────────────────────────────────────────
#  TOKENS JWT DE VERIFICAÇÃO
# ──────────────────────────────────────────────────────────────────────────────


def gerar_token_verificacao(usuario) -> str:
    """
    Gera um access token JWT com claim 'email_verificacao: True'.

    Args:
        usuario: instância de Usuario

    Returns:
        Token JWT em string
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(usuario)
    refresh["email_verificacao"] = True
    logger.info(f"Token de verificação gerado para: {usuario.email}")
    return str(refresh.access_token)


def validar_token_verificacao(token: str) -> tuple[bool, object | None, str | None]:
    """
    Valida um token JWT de verificação de e-mail.

    Returns:
        (válido, usuario | None, mensagem_erro | None)
    """
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.exceptions import TokenError

    try:
        auth = JWTAuthentication()
        validated_token = auth.get_validated_token(token)

        if validated_token.get("email_verificacao") is not True:
            return (
                False,
                None,
                "Token inválido: não é um token de verificação de e-mail.",
            )

        usuario_id = validated_token.get("user_id")
        from apps.usuarios.models import Usuario

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            return True, usuario, None
        except Usuario.DoesNotExist:
            return False, None, "Usuário não encontrado."

    except TokenError as e:
        mensagem = (
            "Token expirado. Solicite um novo link de verificação."
            if "expired" in str(e).lower()
            else f"Token inválido: {e}"
        )
        return False, None, mensagem
    except Exception as e:
        logger.error(f"Erro ao validar token de verificação: {e}")
        return False, None, f"Erro ao validar token: {e}"


# ──────────────────────────────────────────────────────────────────────────────
#  AMIZADES
# ──────────────────────────────────────────────────────────────────────────────


@transaction.atomic
def processar_solicitacao_amizade(
    remetente, destinatario, mensagem: str = ""
) -> tuple[bool, str | None]:
    """
    Processa o envio de uma solicitação de amizade com validações.

    Returns:
        (sucesso, mensagem_erro | None)
    """
    from django.db.models import Q

    from apps.conexoes.models import Amizade, SolicitacaoAmizade

    if remetente == destinatario:
        return False, "Você não pode enviar solicitação para si mesmo."

    if not remetente.email_verificado:
        return (
            False,
            "Você precisa verificar seu e-mail antes de conectar-se com outros usuários.",
        )

    if Amizade.sao_amigos(remetente, destinatario):
        return False, "Você já é amigo deste usuário."

    solicitacao_pendente = SolicitacaoAmizade.objects.filter(
        Q(remetente=remetente, destinatario=destinatario)
        | Q(remetente=destinatario, destinatario=remetente),
        status="pendente",
    ).exists()

    if solicitacao_pendente:
        return False, "Já existe uma solicitação pendente entre vocês."

    limite_tempo = timezone.now() - timedelta(hours=1)
    solicitacoes_recentes = SolicitacaoAmizade.objects.filter(
        remetente=remetente, data_criacao__gte=limite_tempo
    ).count()

    if solicitacoes_recentes >= 10:
        return (
            False,
            "Limite de 10 solicitações por hora atingido. Tente novamente mais tarde.",
        )

    try:
        SolicitacaoAmizade.objects.create(
            remetente=remetente,
            destinatario=destinatario,
            mensagem=mensagem[:500] if mensagem else "",
        )
        return True, None
    except Exception as e:
        logger.error(f"Erro ao criar solicitação de amizade: {e}")
        return False, "Erro ao processar solicitação. Tente novamente."


# ──────────────────────────────────────────────────────────────────────────────
#  DADOS PÚBLICOS DO USUÁRIO
# ──────────────────────────────────────────────────────────────────────────────


def obter_dados_publicos_usuario(usuario) -> dict:
    """
    Retorna apenas dados públicos de um usuário de forma consistente.
    Nunca expõe e-mail, senha ou dados sensíveis.
    """
    return {
        "uuid": str(usuario.uuid),
        "nome_completo": usuario.nome_completo,
        "foto_perfil": usuario.foto_perfil.url if usuario.foto_perfil else None,
        "pais_residencia": usuario.pais_residencia,
        "cidade_residencia": usuario.cidade_residencia,
        "biografia": usuario.biografia if usuario.perfil_publico else "",
    }


# ──────────────────────────────────────────────────────────────────────────────
#  USUÁRIOS
# ──────────────────────────────────────────────────────────────────────────────


@transaction.atomic
def desativar_usuario(usuario, motivo: str = "") -> None:
    """Desativa um usuário de forma segura e rastreável."""
    usuario.ativo = False
    usuario.save(update_fields=["ativo"])
    logger.info(
        f"Usuário desativado: {usuario.email} — Motivo: {motivo or 'não informado'}"
    )
