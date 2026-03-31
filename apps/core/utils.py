"""
Funções utilitárias comuns para toda a aplicação.
Evita redundância de código entre os apps.
"""

import logging
import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def enviar_email_assincrono(destino, assunto, mensagem, template=None):
    """
    Envia email de forma segura (pode ser adaptado para usar Celery).

    Args:
        destino: Email do destinatário
        assunto: Assunto do email
        mensagem: Conteúdo do email
        template: Template HTML (opcional)
    """
    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destino],
            html_message=template,
            fail_silently=False,
        )
        logger.info(f"Email enviado para: {destino}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email para {destino}: {str(e)}")
        return False


def gerar_token_verificacao(usuario):
    """
    Gera um token de verificação seguro usando JWT.

    Args:
        usuario: Objeto Usuario

    Returns:
        Token JWT em string
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(usuario)
    # Adicionar claim customizado para verificação
    refresh["email_verificacao"] = True

    logger.info(f"Token de verificação gerado para: {usuario.email}")
    return str(refresh.access_token)


def validar_token_verificacao(token):
    """
    Valida um token de verificação JWT com expiração automática.

    Args:
        token: Token JWT a verificar

    Returns:
        Tupla (válido: bool, usuario: Usuario ou None, mensagem_erro: str ou None)
    """
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.tokens import TokenError

    try:
        pass

        # Decodificar token manualmente com validação
        auth = JWTAuthentication()
        validated_token = auth.get_validated_token(token)

        # Verificar se tem marcação de email_verificacao
        if validated_token.get("email_verificacao") is not True:
            return (
                False,
                None,
                "Token inválido: não é um token de verificação de email.",
            )

        # Extrair usuário
        usuario_id = validated_token.get("user_id")
        from apps.usuarios.models import Usuario

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            return True, usuario, None
        except Usuario.DoesNotExist:
            return False, None, "Usuário não encontrado."

    except TokenError as e:
        # Token expirado, inválido ou com erro de decodificação
        mensagem_erro = (
            "Token expirado. Solicite um novo."
            if "expired" in str(e)
            else f"Token inválido: {str(e)}"
        )
        return False, None, mensagem_erro
    except Exception as e:
        logger.error(f"Erro ao validar token de verificação: {str(e)}")
        return False, None, f"Erro ao validar token: {str(e)}"


@transaction.atomic
def processar_solicitacao_amizade(remetente, destinatario, mensagem=""):
    """
    Processa o envio de uma solicitação de amizade com validações.
    Garante atomicidade da operação.

    Args:
        remetente: Usuário que envia
        destinatario: Usuário que recebe
        mensagem: Mensagem opcional

    Returns:
        Tupla (sucesso, mensagem_erro)
    """
    from apps.conexoes.models import Amizade, SolicitacaoAmizade

    # Validação 1: Não pode enviar para si mesmo
    if remetente == destinatario:
        return False, "Você não pode enviar solicitação para si mesmo."

    # Validação 2: Já são amigos?
    if Amizade.sao_amigos(remetente, destinatario):
        return False, "Você já é amigo deste usuário."

    # Validação 3: Solicitação pendente?
    from django.db.models import Q

    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=remetente, destinatario=destinatario)
        | Q(remetente=destinatario, destinatario=remetente),
        status="pendente",
    ).exists()

    if solicitacao_existente:
        return False, "Já existe uma solicitação pendente."

    # Validação 4: Rate limiting
    limite_tempo = timezone.now() - timedelta(hours=1)
    solicitacoes_recentes = SolicitacaoAmizade.objects.filter(
        remetente=remetente, data_criacao__gte=limite_tempo
    ).count()

    if solicitacoes_recentes >= 10:
        return False, "Limite de solicitações por hora atingido."

    # Garantir que o usuário tem email verificado
    if not remetente.email_verificado:
        return False, "Você precisa verificar seu email primeiro."

    # Tudo ok, criar solicitação
    try:
        SolicitacaoAmizade.objects.create(
            remetente=remetente,
            destinatario=destinatario,
            mensagem=mensagem[:500] if mensagem else "",
        )
        return True, None
    except Exception as e:
        logger.error(f"Erro ao criar solicitação de amizade: {str(e)}")
        return False, "Erro ao processar solicitação. Tente novamente."


def obter_dados_publicos_usuario(usuario):
    """
    Retorna apenas dados públicos de um usuário de forma consistente.

    Args:
        usuario: Objeto Usuario

    Returns:
        Dicionário com dados públicos
    """
    return {
        "uuid": str(usuario.uuid),
        "nome_completo": usuario.nome_completo,
        "foto_perfil": usuario.foto_perfil.url if usuario.foto_perfil else None,
        "pais_residencia": usuario.pais_residencia,
        "cidade_residencia": usuario.cidade_residencia,
        "biografia": usuario.biografia if usuario.perfil_publico else "",
    }


def validar_senha_forte(password):
    """
    Valida se a senha atende aos critérios de segurança.

    Critérios:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial (!@#$%^&*)

    Args:
        password: Senha a validar

    Raises:
        ValidationError: Se a senha não atender aos critérios
    """
    if len(password) < 8:
        raise ValidationError("A senha deve ter pelo menos 8 caracteres.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("A senha deve conter pelo menos uma letra maiúscula.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("A senha deve conter pelo menos uma letra minúscula.")

    if not re.search(r"\d", password):
        raise ValidationError("A senha deve conter pelo menos um número.")

    if not re.search(r"[!@#$%^&*]", password):
        raise ValidationError(
            "A senha deve conter pelo menos um caractere especial (!@#$%^&*)."
        )


@transaction.atomic
def desativar_usuario(usuario, motivo=""):
    """
    Desativa um usuário de forma segura e rastreável.

    Args:
        usuario: Objeto Usuario a desativar
        motivo: Motivo da desativação (opcional)
    """
    usuario.ativo = False
    usuario.save()
    logger.info(f"Usuário desativado: {usuario.email} - Motivo: {motivo}")


def validar_senha_segura(senha):
    """
    Valida se uma senha atende aos critérios de segurança.

    Args:
        senha: Senha a validar

    Returns:
        Tupla (é_válida, mensagens_erro)
    """
    erros = []

    if len(senha) < 8:
        erros.append("Senha deve ter no mínimo 8 caracteres.")

    if not any(char.isupper() for char in senha):
        erros.append("Senha deve conter pelo menos uma letra maiúscula.")

    if not any(char.isdigit() for char in senha):
        erros.append("Senha deve conter pelo menos um número.")

    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in senha):
        erros.append("Senha deve conter pelo menos um caractere especial.")

    return len(erros) == 0, erros
