from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date
import logging

from .models import SolicitacaoAmizade, Amizade
from apps.usuarios.models import Usuario

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_enviar_solicitacao_amizade(request, uuid_usuario):
    """Envia uma solicitação de amizade para outro usuário."""
    destinatario = get_object_or_404(Usuario, uuid=uuid_usuario)

    if destinatario == request.user:
        messages.error(request, _('Você não pode enviar solicitação para si mesmo.'))
        return redirect('destinos:buscar')

    if not request.user.pode_enviar_solicitacao_amizade():
        messages.error(request, _('Verifique seu email antes de enviar solicitações.'))
        return redirect('usuarios:perfil')

    if not destinatario.ativo:
        messages.error(request, _('Este usuário não está disponível.'))
        return redirect('destinos:buscar')

    if Amizade.sao_amigos(request.user, destinatario):
        messages.info(request, _('Você já é amigo deste usuário.'))
        return redirect('conexoes:amigos')

    # Verificar se já existe solicitação pendente em ambas as direções
    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=destinatario) |
        Q(remetente=destinatario, destinatario=request.user),
        status='pendente'
    ).first()

    if solicitacao_existente:
        # Se o destinatário já enviou solicitação para mim, aceitar automaticamente
        if solicitacao_existente.remetente == destinatario and solicitacao_existente.destinatario == request.user:
            try:
                with transaction.atomic():
                    # Criar amizade
                    amizade, criada = Amizade.objects.get_or_create(
                        usuario1=min(request.user, destinatario, key=lambda u: u.id),
                        usuario2=max(request.user, destinatario, key=lambda u: u.id),
                        defaults={'ativa': True}
                    )
                    if not criada:
                        amizade.ativa = True
                        amizade.save(update_fields=['ativa'])

                    # Aceitar a solicitação existente
                    solicitacao_existente.status = 'aceita'
                    solicitacao_existente.data_resposta = timezone.now()
                    solicitacao_existente.save(update_fields=['status', 'data_resposta'])

                    messages.success(
                        request,
                        _(f'Parabéns! Você e {destinatario.get_nome_exibicao()} agora são amigos!')
                    )
                    logger.info(f'Amizade automática criada: {request.user.email} <-> {destinatario.email}')
                    return redirect('conexoes:amigos')
            except Exception as erro:
                logger.error(f'Erro ao criar amizade automática: {str(erro)}')
                messages.error(request, _('Erro ao processar solicitação. Tente novamente.'))
                return redirect('destinos:buscar')
        else:
            # Já enviei solicitação anteriormente
            messages.info(request, _('Já existe uma solicitação pendente entre vocês.'))
            return redirect('conexoes:solicitacoes')

    limite_tempo = timezone.now() - timedelta(hours=1)
    solicitacoes_recentes = SolicitacaoAmizade.objects.filter(
        remetente=request.user,
        data_criacao__gte=limite_tempo
    ).count()

    if solicitacoes_recentes >= 10:
        messages.error(request, _('Limite de solicitações por hora atingido.'))
        logger.warning(f'Limite de solicitações excedido: {request.user.email}')
        return redirect('destinos:buscar')

    try:
        with transaction.atomic():
            mensagem = request.POST.get('mensagem', '').strip()
            SolicitacaoAmizade.objects.create(
                remetente=request.user,
                destinatario=destinatario,
                mensagem=mensagem[:500]
            )
            messages.success(request, _(f'Solicitação enviada para {destinatario.get_nome_exibicao()}!'))
            logger.info(f'Solicitação enviada: {request.user.email} -> {destinatario.email}')
    except Exception as erro:
        logger.error(f'Erro ao enviar solicitação: {str(erro)}')
        messages.error(request, _('Erro ao enviar solicitação. Tente novamente.'))

    return redirect('destinos:buscar')


@login_required
@require_POST
def enviar_solicitacao(request, uuid_destinatario):
    """Envia solicitação com get_or_create para evitar UNIQUE constraint."""
    destinatario = get_object_or_404(Usuario, uuid=uuid_destinatario)

    if destinatario == request.user:
        messages.error(request, _('Operação inválida.'))
        return redirect('destinos:buscar')

    if Amizade.sao_amigos(request.user, destinatario):
        messages.info(request, _('Vocês já são amigos.'))
        return redirect('conexoes:amigos')

    # Verificar se já existe solicitação pendente em ambas as direções
    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=destinatario) |
        Q(remetente=destinatario, destinatario=request.user),
        status='pendente'
    ).first()

    if solicitacao_existente:
        # Se o destinatário já enviou solicitação para mim, aceitar automaticamente
        if solicitacao_existente.remetente == destinatario and solicitacao_existente.destinatario == request.user:
            try:
                with transaction.atomic():
                    # Criar amizade
                    amizade, criada = Amizade.objects.get_or_create(
                        usuario1=min(request.user, destinatario, key=lambda u: u.id),
                        usuario2=max(request.user, destinatario, key=lambda u: u.id),
                        defaults={'ativa': True}
                    )
                    if not criada:
                        amizade.ativa = True
                        amizade.save(update_fields=['ativa'])

                    # Aceitar a solicitação existente
                    solicitacao_existente.status = 'aceita'
                    solicitacao_existente.data_resposta = timezone.now()
                    solicitacao_existente.save(update_fields=['status', 'data_resposta'])

                    messages.success(
                        request,
                        _(f'Parabéns! Você e {destinatario.get_nome_exibicao()} agora são amigos!')
                    )
                    logger.info(f'Amizade automática criada: {request.user.email} <-> {destinatario.email}')
                    return redirect('conexoes:amigos')
            except Exception as erro:
                logger.error(f'Erro ao criar amizade automática: {str(erro)}')
                messages.error(request, _('Erro ao processar solicitação. Tente novamente.'))
                return redirect('destinos:buscar')
        else:
            # Já enviei solicitação anteriormente
            messages.warning(request, _('Solicitação já enviada anteriormente.'))
            return redirect('conexoes:solicitacoes')

    try:
        with transaction.atomic():
            solicitacao, criado = SolicitacaoAmizade.objects.get_or_create(
                remetente=request.user,
                destinatario=destinatario,
                defaults={'status': 'pendente'}
            )

            if criado:
                messages.success(request, _('Solicitação enviada com sucesso!'))
                logger.info(f'Solicitação enviada: {request.user.email} -> {destinatario.email}')
            elif solicitacao.status == 'pendente':
                messages.warning(request, _('Solicitação já enviada anteriormente.'))
            else:
                # Reativa solicitação cancelada/recusada
                solicitacao.status = 'pendente'
                solicitacao.data_criacao = timezone.now()
                solicitacao.save(update_fields=['status', 'data_criacao'])
                messages.success(request, _('Solicitação enviada com sucesso!'))
                logger.info(f'Solicitação reativada: {request.user.email} -> {destinatario.email}')

    except Exception as erro:
        logger.error(f'Erro ao enviar solicitação: {str(erro)}')
        messages.error(request, _('Erro ao enviar solicitação. Tente novamente.'))

    return redirect('destinos:buscar')


@login_required
@require_http_methods(["GET"])
def view_lista_solicitacoes(request):
    """Lista todas as solicitações de amizade do usuário."""
    solicitacoes_recebidas = SolicitacaoAmizade.objects.filter(
        destinatario=request.user,
        status='pendente'
    ).select_related('remetente').order_by('-data_criacao')

    solicitacoes_enviadas = SolicitacaoAmizade.objects.filter(
        remetente=request.user,
        status='pendente'
    ).select_related('destinatario').order_by('-data_criacao')

    # ── Amigos (para a aba Amigos no template) ───────────────
    amizades = Amizade.objects.filter(
        Q(usuario1=request.user) | Q(usuario2=request.user),
        ativa=True
    ).select_related('usuario1', 'usuario2').order_by('-data_criacao')

    amigos_dados = []
    for amizade in amizades:
        amigo = amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
        planos_amigo = amigo.planos_viagem.filter(
            ativo=True,
            viagem_concluida=False
        ).select_related('pais_destino')
        amigos_dados.append({
            'amigo': amigo,
            'amizade': amizade,
            'planos': planos_amigo,
        })

    # ── IDs a excluir das sugestões ──────────────────────────
    ids_excluir = {request.user.id}

    for amizade in amizades:
        ids_excluir.add(amizade.usuario1_id)
        ids_excluir.add(amizade.usuario2_id)

    pendentes_ids = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user) | Q(destinatario=request.user),
        status='pendente'
    ).values_list('remetente_id', 'destinatario_id')
    for r, d in pendentes_ids:
        ids_excluir.add(r)
        ids_excluir.add(d)

    sugestoes = Usuario.objects.filter(
        ativo=True
    ).exclude(id__in=ids_excluir).order_by('?')[:8]

    return render(request, 'conexoes/solicitacoes.html', {
        'solicitacoes_recebidas': solicitacoes_recebidas,
        'solicitacoes_enviadas': solicitacoes_enviadas,
        'amigos_dados': amigos_dados,
        'sugestoes': sugestoes,
        'titulo': _('Solicitações de Amizade'),
        'hoje': date.today().strftime('%Y-%m-%d'),
    })

@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_responder_solicitacao(request, uuid_solicitacao, acao):
    """
    Responde a uma solicitação de amizade.
    Aceita as ações 'aceitar' e 'rejeitar' (template usa 'rejeitar').
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
                # Verificar se já são amigos (precaução extra)
                if Amizade.sao_amigos(request.user, solicitacao.remetente):
                    solicitacao.status = 'aceita'
                    solicitacao.save(update_fields=['status'])
                    messages.info(request, _(f'Vocês já eram amigos!'))
                    logger.info(f'Solicitação aceita (já eram amigos): {solicitacao.remetente.email} <-> {request.user.email}')
                    return redirect('conexoes:amigos')

                # get_or_create evita UNIQUE constraint caso amizade já exista
                amizade, criada = Amizade.objects.get_or_create(
                    usuario1=min(request.user, solicitacao.remetente, key=lambda u: u.id),
                    usuario2=max(request.user, solicitacao.remetente, key=lambda u: u.id),
                    defaults={'ativa': True}
                )
                if not criada:
                    amizade.ativa = True
                    amizade.save(update_fields=['ativa'])

                solicitacao.status = 'aceita'
                solicitacao.data_resposta = timezone.now()
                solicitacao.save(update_fields=['status', 'data_resposta'])

                messages.success(
                    request,
                    _(f'Você agora é amigo de {solicitacao.remetente.get_nome_exibicao()}!')
                )
                logger.info(f'Solicitação aceita: {solicitacao.remetente.email} <-> {request.user.email}')

            elif acao in ('rejeitar', 'recusar'):
                solicitacao.status = 'recusada'
                solicitacao.data_resposta = timezone.now()
                solicitacao.save(update_fields=['status', 'data_resposta'])
                messages.info(request, _('Solicitação rejeitada.'))
                logger.info(f'Solicitação rejeitada: {solicitacao.remetente.email} -> {request.user.email}')

            else:
                messages.error(request, _('Ação inválida.'))
                return redirect('conexoes:solicitacoes')

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
        solicitacao.status = 'cancelada'
        solicitacao.save(update_fields=['status'])
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
    try:
        amizades = Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True
        ).select_related('usuario1', 'usuario2').order_by('-data_criacao')

        amigos_dados = []
        for amizade in amizades:
            amigo = amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
            planos_amigo = amigo.planos_viagem.filter(
                ativo=True,
                viagem_concluida=False
            ).select_related('pais_destino')

            amigos_dados.append({
                'amigo': amigo,
                'amizade': amizade,
                'planos': planos_amigo,
            })

        # Debug: imprimir número de amigos encontrados
        logger.info(f'Usuário {request.user.email} tem {len(amigos_dados)} amigos')

        paginador = Paginator(amigos_dados, 12)
        pagina_numero = request.GET.get('page', 1)

        try:
            amigos_paginados = paginador.get_page(pagina_numero)
        except Exception as e:
            logger.error(f'Erro na paginação: {str(e)}')
            amigos_paginados = paginador.get_page(1)

        # Todos os usuários (para conexões) - incluindo status de amizade/pendência
        usuarios_ativos = Usuario.objects.filter(ativo=True).exclude(id=request.user.id)

        # Já são amigos?
        amigos_ids = set()
        for amizade in amizades:
            amigo = amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
            amigos_ids.add(amigo.id)

        # Solicitações pendentes entre o usuário e outros
        pendentes = SolicitacaoAmizade.objects.filter(
            Q(remetente=request.user) | Q(destinatario=request.user),
            status='pendente'
        ).values_list('remetente_id', 'destinatario_id')

        pendentes_ids = set()
        for r, d in pendentes:
            pendentes_ids.add(r)
            pendentes_ids.add(d)

        todos_usuarios = []
        for usuario in usuarios_ativos:
            if usuario.id in amigos_ids:
                status = 'amigo'
            elif usuario.id in pendentes_ids:
                status = 'pendente'
            else:
                status = 'nenhum'

            todos_usuarios.append({
                'usuario': usuario,
                'status': status,
            })

        return render(request, 'conexoes/lista_amigos.html', {
            'amigos_dados': amigos_paginados,
            'total_amigos': len(amigos_dados),
            'todos_usuarios': todos_usuarios,
            'titulo': _('Meus Amigos'),
        })

    except Exception as erro:
        logger.error(f'Erro ao listar amigos para {request.user.email}: {str(erro)}')
        messages.error(request, _('Erro ao carregar lista de amigos. Tente novamente.'))
        return render(request, 'conexoes/lista_amigos.html', {
            'amigos_dados': [],
            'total_amigos': 0,
            'titulo': _('Meus Amigos'),
        })


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_desfazer_amizade(request, uuid_amigo):
    """Remove uma amizade."""
    amigo = get_object_or_404(Usuario, uuid=uuid_amigo)

    # Verificar se realmente são amigos
    if not Amizade.sao_amigos(request.user, amigo):
        messages.error(request, _('Vocês não são amigos.'))
        return redirect('conexoes:amigos')

    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=amigo) |
                Q(usuario1=amigo, usuario2=request.user),
                ativa=True
            ).first()

            if amizade:
                amizade.desfazer_amizade()
                messages.success(request, _(f'Amizade com {amigo.get_nome_exibicao()} desfeita.'))
                logger.info(f'Amizade desfeita: {request.user.email} <-> {amigo.email}')
            else:
                messages.error(request, _('Amizade não encontrada.'))

    except Exception as erro:
        logger.error(f'Erro ao desfazer amizade: {str(erro)}')
        messages.error(request, _('Erro ao desfazer amizade. Tente novamente.'))

    return redirect('conexoes:amigos')