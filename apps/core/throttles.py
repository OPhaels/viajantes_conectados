"""
Rate limiting customizado para proteger contra ataques de força bruta e abuso.
"""

import logging

from django.core.cache import cache
from django.utils.translation import gettext_lazy
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class LoginThrottle(AnonRateThrottle):
    """
    Limita tentativas de login.
    - Usuários anônimos: 5 tentativas por minuto
    """

    scope = "login"
    THROTTLE_RATES = {"login": "5/min"}

    def throttle_success(self, request):
        """Registra login bem-sucedido."""
        result = super().throttle_success(request)
        if result:
            # Limpar counter após login bem-sucedido
            cache.delete(self.key)
        return result


class RegistroThrottle(AnonRateThrottle):
    """
    Limita registro de novos usuários.
    - Usuários anônimos: 10 registros por hora
    """

    scope = "registro"
    THROTTLE_RATES = {"registro": "10/hour"}


class EmailVerificacaoThrottle(UserRateThrottle):
    """
    Limita requisições de verificação de email.
    - Usuários autenticados: 3 tentativas por hora
    """

    scope = "email_verificacao"
    THROTTLE_RATES = {"email_verificacao": "3/hour"}


class SolicitacaoAmizadeThrottle(UserRateThrottle):
    """
    Limita criação de solicitações de amizade.
    - Usuários autenticados: 10 solicitações por hora
    """

    scope = "solicitacao_amizade"
    THROTTLE_RATES = {"solicitacao_amizade": "10/hour"}


class CriacaoPlanosThrottle(UserRateThrottle):
    """
    Limita criação de planos de viagem.
    - Usuários autenticados: 30 planos por dia
    """

    scope = "criacao_planos"
    THROTTLE_RATES = {"criacao_planos": "30/day"}


class MensagensThrottle(UserRateThrottle):
    """
    Limita envio de mensagens no chat.
    - Usuários autenticados: 100 mensagens por hora
    """

    scope = "mensagens"
    THROTTLE_RATES = {"mensagens": "100/hour"}


class BuscaThrottle(AnonRateThrottle):
    """
    Limita requisições de busca para proteger contra web scraping.
    - Usuários anônimos: 100 buscas por hora
    - Usuários autenticados: 500 buscas por hora
    """

    scope = "busca"
    THROTTLE_RATES = {
        "busca": "100/hour",  # Para anônimos
    }


class BuscaAutenticadoThrottle(UserRateThrottle):
    """Limite mais elevado para usuários autenticados."""

    scope = "busca_autenticado"
    THROTTLE_RATES = {"busca_autenticado": "500/hour"}


def verificar_throttle_critico(request, chave, limite_por_hora=100):
    """
    Função auxiliar para throttle crítico baseado em IP.
    Útil para endpoints que não requerem autenticação.

    Args:
        request: Objeto da requisição
        chave: Chave única para o throttle (ex: 'download')
        limite_por_hora: Número máximo de requisições por hora

    Returns:
        bool: True se permitido, False se bloqueado
    """

    # Obter IP do cliente
    ip = obter_ip_cliente(request)
    cache_key = f"throttle_critico_{chave}_{ip}"

    # Obter contador atual
    contador = cache.get(cache_key, 0)

    if contador >= limite_por_hora:
        logger.warning(
            f"Throttle crítico acionado: {chave} para IP {ip} "
            f"({contador} requisições/hora)"
        )
        return False

    # Incrementar e armazenar
    cache.set(cache_key, contador + 1, timeout=3600)  # 1 hora
    return True


def obter_ip_cliente(request):
    """
    Obtém IP real do cliente considerando proxies.

    Args:
        request: Objeto da requisição

    Returns:
        str: Endereço IP do cliente
    """
    # Verificar X-Forwarded-For primeiro (para proxies)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        # Fallback para REMOTE_ADDR
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")

    return ip


def registrar_acao_sensivel(request, acao, detalhes=""):
    """
    Registra ações sensíveis para auditoria e detecção de fraude.

    Args:
        request: Objeto da requisição
        acao: Tipo de ação (ex: 'login_falhado', 'novo_usuario', etc)
        detalhes: Detalhes adicionais da ação
    """

    # Simulação - não utilizada na prática
    # usuarios = list(Usuario.objects.all())

    data = {
        "timestamp": gettext_lazy("Timestamp"),
        "acao": acao,
        "usuario": (
            gettext_lazy("Anônimo")
            if not request.user.is_authenticated
            else request.user.email
        ),
        "ip": obter_ip_cliente(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
        "detalhes": detalhes[:500],
        "resultado": "sucesso" if request.method == "GET" else "pendente",
    }

    logger.info(f"Ação sensível registrada: {data}")

    # Aqui você poderia salvar em um modelo de auditoria se houver
    # AuditoriaLog.objects.create(**data)


# Importar _ para usar gettext_lazy
