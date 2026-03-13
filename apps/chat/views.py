from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Q
from datetime import date
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
        ultima_msg_data=Max('mensagens__data_envio')
    ).order_by('-ultima_msg_data')

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
            'mensagens_nao_lidas': mensagens_nao_lidas,
        })

    # Buscar amigos que não têm conversa ainda
    from apps.conexoes.models import Amizade
    amigos_com_conversa = set()
    for item in conversas_com_dados:
        amigos_com_conversa.add(item['outro_participante'].id)

    amigos_sem_conversa = []
    amizades = Amizade.objects.filter(
        Q(usuario1=request.user) | Q(usuario2=request.user),
        ativa=True
    ).select_related('usuario1', 'usuario2')

    for amizade in amizades:
        amigo = amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
        if amigo.id not in amigos_com_conversa:
            amigos_sem_conversa.append({
                'amigo': amigo,
                'amizade': amizade,
            })

    return render(request, 'chat/lista_conversas.html', {
        'conversas_com_dados': conversas_com_dados,
        'amigos_sem_conversa': amigos_sem_conversa,
        'titulo': _('Minhas Conversas'),
        'hoje': date.today().strftime('%Y-%m-%d'),
    })


@login_required
@require_http_methods(["GET"])
def view_conversa(request, uuid_conversa):
    """Visualiza uma conversa específica."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not conversa.participantes.filter(id=request.user.id).exists():
        messages.error(request, _('Você não tem permissão para acessar esta conversa.'))
        return redirect('chat:conversas')

    outro_participante = conversa.participantes.exclude(id=request.user.id).first()

    # Marca mensagens recebidas como lidas
    Mensagem.objects.filter(
        conversa=conversa,
        lida=False
    ).exclude(remetente=request.user).update(
        lida=True,
        data_leitura=timezone.now()
    )

    return render(request, 'chat/conversas.html', {
        'conversa': conversa,
        'outro_participante': outro_participante,
        'titulo': f'Chat com {outro_participante.get_nome_exibicao()}',
        'hoje': date.today().strftime('%Y-%m-%d'),
    })


@login_required
@require_http_methods(["POST"])
def view_iniciar_conversa(request, uuid_usuario):
    """Inicia uma nova conversa com um amigo."""
    outro_usuario = get_object_or_404(Usuario, uuid=uuid_usuario)

    if not Amizade.sao_amigos(request.user, outro_usuario):
        messages.error(request, _('Você só pode conversar com amigos.'))
        return redirect('destinos:buscar')

    conversa = Conversa.obter_ou_criar_conversa(request.user, outro_usuario)

    logger.info(f'Conversa iniciada: {request.user.email} <-> {outro_usuario.email}')
    return redirect('chat:conversa', uuid_conversa=conversa.uuid)


@login_required
@require_http_methods(["POST"])
def view_enviar_mensagem(request, uuid_conversa):
    """Envia uma mensagem numa conversa. Aceita AJAX e POST normal."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not conversa.participantes.filter(id=request.user.id).exists():
        if is_ajax:
            return JsonResponse({'erro': 'Sem permissão.'}, status=403)
        messages.error(request, _('Sem permissão.'))
        return redirect('chat:conversas')

    conteudo = request.POST.get('conteudo', '').strip()

    if not conteudo:
        if is_ajax:
            return JsonResponse({'erro': 'Mensagem vazia.'}, status=400)
        return redirect('chat:conversa', uuid_conversa=uuid_conversa)

    if len(conteudo) > 2000:
        if is_ajax:
            return JsonResponse({'erro': 'Mensagem muito longa (máx. 2000 caracteres).'}, status=400)
        messages.error(request, _('Mensagem muito longa.'))
        return redirect('chat:conversa', uuid_conversa=uuid_conversa)

    mensagem = Mensagem.objects.create(
        conversa=conversa,
        remetente=request.user,
        conteudo=conteudo,
    )

    # Atualiza timestamp da conversa
    conversa.data_ultima_mensagem = timezone.now()
    conversa.save(update_fields=['data_ultima_mensagem'])

    logger.info(f'Mensagem enviada: conversa={uuid_conversa} remetente={request.user.email}')

    if is_ajax:
        return JsonResponse({
            'status': 'ok',
            'id': mensagem.id,
            'conteudo': mensagem.conteudo,
            'hora': mensagem.data_envio.strftime('%H:%M'),
            'remetente_uuid': str(request.user.uuid),
        })

    return redirect('chat:conversa', uuid_conversa=uuid_conversa)


@login_required
@require_http_methods(["GET"])
def view_mensagens_json(request, uuid_conversa):
    """Retorna mensagens novas após um determinado ID (polling)."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not conversa.participantes.filter(id=request.user.id).exists():
        return JsonResponse({'erro': 'Sem permissão.'}, status=403)

    after_id = int(request.GET.get('after', 0))

    novas = Mensagem.objects.filter(
        conversa=conversa,
        id__gt=after_id
    ).select_related('remetente').order_by('data_envio')

    # Marca as recebidas como lidas
    novas.exclude(remetente=request.user).filter(lida=False).update(
        lida=True,
        data_leitura=timezone.now()
    )

    # Verifica se o outro participante está digitando
    outro = conversa.participantes.exclude(id=request.user.id).first()
    digitando = False
    if hasattr(conversa, 'digitando_por') and outro:
        digitando = conversa.digitando_por.filter(id=outro.id).exists()

    return JsonResponse({
        'mensagens': [
            {
                'id': m.id,
                'conteudo': m.conteudo,
                'hora': m.data_envio.strftime('%H:%M'),
                'remetente_uuid': str(m.remetente.uuid),
                'lida': m.lida,
            }
            for m in novas
        ],
        'digitando': digitando,
    })


@login_required
@require_http_methods(["POST"])
def view_apagar_mensagem(request, mensagem_id):
    """Apaga uma mensagem (somente o remetente pode apagar)."""
    mensagem = get_object_or_404(Mensagem, id=mensagem_id)

    if mensagem.remetente != request.user:
        return JsonResponse({'erro': 'Sem permissão.'}, status=403)

    conversa_uuid = str(mensagem.conversa.uuid)
    mensagem.delete()

    logger.info(f'Mensagem {mensagem_id} apagada por {request.user.email}')
    return JsonResponse({'status': 'ok', 'conversa_uuid': conversa_uuid})


@login_required
@require_http_methods(["POST"])
def view_nao_lidas_json(request):
    """Retorna contagem de mensagens não lidas por conversa (para polling na lista)."""
    conversas = Conversa.objects.filter(participantes=request.user, ativa=True)

    data = {
        str(c.uuid): Mensagem.objects.filter(
            conversa=c,
            lida=False
        ).exclude(remetente=request.user).count()
        for c in conversas
    }

    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def view_digitando(request, uuid_conversa):
    """Marca que o usuário está digitando nesta conversa."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not conversa.participantes.filter(id=request.user.id).exists():
        return JsonResponse({'erro': 'Sem permissão.'}, status=403)

    # Requer campo ManyToMany 'digitando_por' no model Conversa (opcional)
    if hasattr(conversa, 'digitando_por'):
        conversa.digitando_por.add(request.user)

    return JsonResponse({'status': 'ok'})


@login_required
@require_http_methods(["POST"])
def view_parou_digitar(request, uuid_conversa):
    """Remove o indicador de digitação."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if hasattr(conversa, 'digitando_por'):
        conversa.digitando_por.remove(request.user)

    return JsonResponse({'status': 'ok'})