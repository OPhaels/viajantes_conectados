from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
import logging

from .models import SolicitacaoAmizade, Amizade
from apps.usuarios.models import Usuario

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_enviar_solicitacao_amizade(request, uuid_usuario):
    """
    Envia uma solicitação de amizade para outro usuário.
    Implementa validações de segurança e limitação de taxa.
    """
    destinatario = get_object_or_404(Usuario, uuid=uuid_usuario)
    
    # Validações de segurança
    if destinatario == request.user:
        messages.error(request, _('Você não pode enviar solicitação para si mesmo.'))
        return redirect('destinos:buscar')
    
    if not request.user.pode_enviar_solicitacao_amizade():
        messages.error(
            request,
            _('Você precisa verificar seu email antes de enviar solicitações de amizade.')
        )
        return redirect('usuarios:perfil')
    
    if not destinatario.ativo:
        messages.error(request, _('Este usuário não está disponível.'))
        return redirect('destinos:buscar')
    
    # Verificar se já são amigos
    if Amizade.sao_amigos(request.user, destinatario):
        messages.info(request, _('Você já é amigo deste usuário.'))
        return redirect('conexoes:amigos')
    
    # Verificar se já existe solicitação pendente
    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=destinatario) |
        Q(remetente=destinatario, destinatario=request.user),
        status='pendente'
    ).first()
    
    if solicitacao_existente:
        messages.info(request, _('Já existe uma solicitação pendente entre vocês.'))
        return redirect('conexoes:solicitacoes')
    
    # Verificar limite de solicitações (anti-spam)
    from django.utils import timezone
    from datetime import timedelta
    
    limite_tempo = timezone.now() - timedelta(hours=1)
    solicitacoes_recentes = SolicitacaoAmizade.objects.filter(
        remetente=request.user,
        data_criacao__gte=limite_tempo
    ).count()
    
    if solicitacoes_recentes >= 10:
        messages.error(
            request,
            _('Você atingiu o limite de solicitações por hora. Tente novamente mais tarde.')
        )
        logger.warning(f'Limite de solicitações excedido: {request.user.email}')
        return redirect('destinos:buscar')
    
    try:
        with transaction.atomic():
            # Criar solicitação
            mensagem = request.POST.get('mensagem', '').strip()
            
            solicitacao = SolicitacaoAmizade.objects.create(
                remetente=request.user,
                destinatario=destinatario,
                mensagem=mensagem[:500]  # Limitar tamanho
            )
            
            messages.success(
                request,
                _(f'Solicitação enviada para {destinatario.get_nome_exibicao()}!')
            )
            logger.info(
                f'Solicitação de amizade enviada: '
                f'{request.user.email} -> {destinatario.email}'
            )
            
            # TODO: Enviar notificação por email (implementar com Celery)
    
    except Exception as erro:
        logger.error(f'Erro ao enviar solicitação: {str(erro)}')
        messages.error(request, _('Erro ao enviar solicitação. Tente novamente.'))
    
    return redirect('destinos:buscar')


@login_required
@require_http_methods(["GET"])
def view_lista_solicitacoes(request):
    """Lista todas as solicitações de amizade do usuário."""
    
    # Solicitações recebidas pendentes
    solicitacoes_recebidas = SolicitacaoAmizade.objects.filter(
        destinatario=request.user,
        status='pendente'
    ).select_related('remetente').order_by('-data_criacao')
    
    # Solicitações enviadas pendentes
    solicitacoes_enviadas = SolicitacaoAmizade.objects.filter(
        remetente=request.user,
        status='pendente'
    ).select_related('destinatario').order_by('-data_criacao')
    
    contexto = {
        'solicitacoes_recebidas': solicitacoes_recebidas,
        'solicitacoes_enviadas': solicitacoes_enviadas,
        'titulo': _('Solicitações de Amizade')
    }
    
    return render(request, 'conexoes/solicitacoes.html', contexto)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_responder_solicitacao(request, uuid_solicitacao, acao):
    """
    Responde a uma solicitação de amizade (aceitar ou recusar).
    """
    solicitacao = get_object_or_404(
        SolicitacaoAmizade,
        uuid=uuid_solicitacao,
        destinatario=request.user,
        status='pendente'
    )
    
    try:
        with transaction.atomic():
            if acao == 'aceitar':
                solicitacao.aceitar()
                messages.success(
                    request,
                    _(f'Você agora é amigo de {solicitacao.remetente.get_nome_exibicao()}!')
                )
                logger.info(
                    f'Solicitação aceita: '
                    f'{solicitacao.remetente.email} <-> {request.user.email}'
                )
            
            elif acao == 'recusar':
                solicitacao.recusar()
                messages.info(request, _('Solicitação recusada.'))
                logger.info(
                    f'Solicitação recusada: '
                    f'{solicitacao.remetente.email} -> {request.user.email}'
                )
            
            else:
                messages.error(request, _('Ação inválida.'))
    
    except Exception as erro:
        logger.error(f'Erro ao responder solicitação: {str(erro)}')
        messages.error(request, _('Erro ao processar solicitação. Tente novamente.'))
    
    return redirect('conexoes:solicitacoes')


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_cancelar_solicitacao(request, uuid_solicitacao):
    """Cancela uma solicitação enviada."""
    solicitacao = get_object_or_404(
        SolicitacaoAmizade,
        uuid=uuid_solicitacao,
        remetente=request.user,
        status='pendente'
    )
    
    try:
        solicitacao.cancelar()
        messages.success(request, _('Solicitação cancelada.'))
        logger.info(f'Solicitação cancelada: {request.user.email}')
    
    except Exception as erro:
        logger.error(f'Erro ao cancelar solicitação: {str(erro)}')
        messages.error(request, _('Erro ao cancelar solicitação.'))
    
    return redirect('conexoes:solicitacoes')


@login_required
@require_http_methods(["GET"])
def view_lista_amigos(request):
    """Lista todos os amigos do usuário."""
    
    # Buscar todas as amizades ativas
    amizades = Amizade.objects.filter(
        Q(usuario1=request.user) | Q(usuario2=request.user),
        ativa=True
    ).select_related('usuario1', 'usuario2').order_by('-data_criacao')
    
    # Organizar dados dos amigos
    amigos_dados = []
    for amizade in amizades:
        amigo = amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
        
        # Buscar planos de viagem ativos do amigo
        planos_amigo = amigo.planos_viagem.filter(
            ativo=True,
            viagem_concluida=False
        ).select_related('pais_destino')
        
        amigos_dados.append({
            'amigo': amigo,
            'amizade': amizade,
            'planos': planos_amigo
        })
    
    # Paginação
    paginador = Paginator(amigos_dados, 12)
    numero_pagina = request.GET.get('page', 1)
    amigos_paginados = paginador.get_page(numero_pagina)
    
    contexto = {
        'amigos_dados': amigos_paginados,
        'total_amigos': len(amigos_dados),
        'titulo': _('Meus Amigos')
    }
    
    return render(request, 'conexoes/lista_amigos.html', contexto)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_desfazer_amizade(request, uuid_amigo):
    """Remove uma amizade."""
    amigo = get_object_or_404(Usuario, uuid=uuid_amigo)
    
    try:
        with transaction.atomic():
            # Buscar a amizade
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=amigo) |
                Q(usuario1=amigo, usuario2=request.user),
                ativa=True
            ).first()
            
            if amizade:
                amizade.desfazer_amizade()
                messages.success(
                    request,
                    _(f'Amizade com {amigo.get_nome_exibicao()} desfeita.')
                )
                logger.info(
                    f'Amizade desfeita: '
                    f'{request.user.email} <-> {amigo.email}'
                )
            else:
                messages.error(request, _('Amizade não encontrada.'))
    
    except Exception as erro:
        logger.error(f'Erro ao desfazer amizade: {str(erro)}')
        messages.error(request, _('Erro ao desfazer amizade. Tente novamente.'))
    
    return redirect('conexoes:amigos')