from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Max
import logging

from .models import Conversa, Mensagem
from apps.usuarios.models import Usuario
from apps.conexoes.models import Amizade

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def view_lista_conversas(request):
    """Lista todas as conversas do usuário."""
    conversas = Conversa.objects.filter(
        participantes=request.user,
        ativa=True
    ).prefetch_related('participantes').annotate(
        ultima_mensagem=Max('mensagens__data_envio')
    ).order_by('-ultima_mensagem')
    
    # Calcular mensagens não lidas
    conversas_com_dados = []
    for conversa in conversas:
        outro_participante = conversa.participantes.exclude(id=request.user.id).first()
        mensagens_nao_lidas = Mensagem.objects.filter(
            conversa=conversa,
            lida=False
        ).exclude(remetente=request.user).count()
        
        conversas_com_dados.append({
            'conversa': conversa,
            'outro_participante': outro_participante,
            'mensagens_nao_lidas': mensagens_nao_lidas
        })
    
    contexto = {
        'conversas_com_dados': conversas_com_dados,
        'titulo': _('Minhas Conversas')
    }
    
    return render(request, 'chat/lista_conversas.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_conversa(request, uuid_conversa):
    """Visualiza uma conversa específica."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)
    
    # Verificar se o usuário é participante
    if not conversa.participantes.filter(id=request.user.id).exists():
        messages.error(request, _('Você não tem permissão para acessar esta conversa.'))
        return redirect('chat:conversas')
    
    # Obter o outro participante
    outro_participante = conversa.participantes.exclude(id=request.user.id).first()
    
    # Marcar mensagens como lidas
    Mensagem.objects.filter(
        conversa=conversa,
        lida=False
    ).exclude(remetente=request.user).update(
        lida=True,
        data_leitura=timezone.now()
    )
    
    contexto = {
        'conversa': conversa,
        'outro_participante': outro_participante,
        'titulo': f'Chat com {outro_participante.get_nome_exibicao()}'
    }
    
    return render(request, 'chat/conversa.html', contexto)


@login_required
@require_http_methods(["POST"])
def view_iniciar_conversa(request, uuid_usuario):
    """Inicia uma nova conversa com um amigo."""
    outro_usuario = get_object_or_404(Usuario, uuid=uuid_usuario)
    
    # Verificar se são amigos
    if not Amizade.sao_amigos(request.user, outro_usuario):
        messages.error(request, _('Você só pode conversar com amigos.'))
        return redirect('destinos:buscar')
    
    # Obter ou criar conversa
    conversa = Conversa.obter_ou_criar_conversa(request.user, outro_usuario)
    
    logger.info(f'Conversa iniciada: {request.user.email} <-> {outro_usuario.email}')
    return redirect('chat:conversa', uuid_conversa=conversa.uuid)