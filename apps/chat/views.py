from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Count, Max
from django.db import transaction
from datetime import date
import logging

from .models import Conversa, Mensagem
from apps.usuarios.models import Usuario
from apps.conexoes.models import Amizade, Bloqueio
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)


# =========================
# HELPERS INTERNOS
# =========================

def _marcar_mensagens_lidas(conversa, usuario):
    """Marca como lidas todas as mensagens não lidas do outro participante."""
    return Mensagem.objects.filter(
        conversa=conversa,
        lida=False,
    ).exclude(remetente=usuario).update(
        lida=True,
        data_leitura=timezone.now(),
    )


def _verificar_participante(conversa, usuario):
    """Retorna True se o usuário é participante da conversa."""
    return conversa.participantes.filter(id=usuario.id).exists()


def _esta_bloqueado(usuario, outro):
    """
    Retorna True se existe bloqueio em qualquer direção entre os dois usuários.
    Usa Bloqueio de apps.conexoes.models.
    """
    return Bloqueio.objects.filter(
        Q(bloqueador=usuario, bloqueado=outro) |
        Q(bloqueador=outro,   bloqueado=usuario)
    ).exists()


def _sao_amigos_ativos(usuario, outro):
    """Retorna True somente se existe amizade ativa entre os dois."""
    return Amizade.sao_amigos(usuario, outro)


# =========================
# LISTA DE CONVERSAS
# =========================

@login_required
@require_http_methods(["GET"])
def view_lista_conversas(request):
    """Lista todas as conversas ativas do usuário com contagem de não lidas."""
    conversas = (
        Conversa.objects
        .filter(participantes=request.user, ativa=True)
        .annotate(
            ultima_msg=Coalesce('data_ultima_mensagem', 'data_criacao'),
            # Resolve o problema N+1: conta não lidas em uma única query
            mensagens_nao_lidas=Count(
                'mensagens',
                filter=Q(mensagens__lida=False) & ~Q(mensagens__remetente=request.user),
            ),
        )
        .prefetch_related('participantes')
        .order_by('-ultima_msg')
    )

    conversas_com_dados = []
    amigos_com_conversa = set()

    for conversa in conversas:
        outro = conversa.participantes.exclude(id=request.user.id).first()
        if outro:
            amigos_com_conversa.add(outro.id)

        conversas_com_dados.append({
            'conversa': conversa,
            'outro_participante': outro,
            'mensagens_nao_lidas': conversa.mensagens_nao_lidas,
        })

    amizades = (
        Amizade.objects
        .filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True,
        )
        .select_related('usuario1', 'usuario2')
    )

    amigos_sem_conversa = [
        {'amigo': amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1,
         'amizade': amizade}
        for amizade in amizades
        if (amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1).id
        not in amigos_com_conversa
    ]

    return render(request, 'chat/lista_conversas.html', {
        'conversas_com_dados': conversas_com_dados,
        'amigos_sem_conversa': amigos_sem_conversa,
        'titulo': _('Minhas Conversas'),
        'hoje': date.today().strftime('%Y-%m-%d'),
    })


# =========================
# VISUALIZAR CONVERSA
# =========================

@login_required
@require_http_methods(["GET"])
def view_conversa(request, uuid_conversa):
    """
    Exibe uma conversa.
    Bloqueia acesso se:
    - o usuário não é participante
    - existe bloqueio em qualquer direção
    - a amizade foi desfeita
    """
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        messages.error(request, _('Você não tem permissão para acessar esta conversa.'))
        return redirect('chat:conversas')

    outro = conversa.participantes.exclude(id=request.user.id).first()

    if outro and _esta_bloqueado(request.user, outro):
        messages.error(request, _('Não é possível acessar esta conversa.'))
        return redirect('chat:conversas')

    if outro and not _sao_amigos_ativos(request.user, outro):
        messages.warning(request, _('Você e este usuário não são mais amigos. O chat está em modo leitura.'))

    mensagens = conversa.mensagens.select_related('remetente').order_by('data_envio')
    _marcar_mensagens_lidas(conversa, request.user)

    return render(request, 'chat/conversas.html', {
        'conversa': conversa,
        'outro_participante': outro,
        'mensagens': mensagens,
        'titulo': f'Chat com {outro.get_nome_exibicao()}',
        'hoje': date.today().strftime('%Y-%m-%d'),
        'sao_amigos': _sao_amigos_ativos(request.user, outro) if outro else False,
    })


# =========================
# INICIAR CONVERSA
# =========================

@login_required
@require_http_methods(["GET", "POST"])
def view_iniciar_conversa(request, uuid_usuario):
    """
    Inicia ou retoma uma conversa com um amigo.
    Rejeita se não há amizade ativa ou se há bloqueio em qualquer direção.
    """
    outro = get_object_or_404(Usuario, uuid=uuid_usuario)

    if outro == request.user:
        messages.error(request, _('Você não pode conversar consigo mesmo.'))
        return redirect('chat:conversas')

    if _esta_bloqueado(request.user, outro):
        messages.error(request, _('Não é possível iniciar esta conversa.'))
        return redirect('chat:conversas')

    if not _sao_amigos_ativos(request.user, outro):
        messages.error(request, _('Você só pode conversar com pessoas da sua lista de amigos.'))
        return redirect('destinos:buscar')

    conversa = Conversa.obter_ou_criar_conversa(request.user, outro)

    if not conversa.ativa:
        conversa.ativa = True
        conversa.save(update_fields=['ativa'])

    logger.info('Conversa iniciada: %s <-> %s', request.user.email, outro.email)
    return redirect('chat:conversa', uuid_conversa=conversa.uuid)


# =========================
# ENVIAR MENSAGEM
# =========================

@login_required
@require_http_methods(["POST"])
def view_enviar_mensagem(request, uuid_conversa):
    """
    Envia uma mensagem na conversa indicada.
    Rejeita se há bloqueio ou se a amizade foi desfeita.
    Reativa automaticamente conversas inativas.
    """
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    outro = conversa.participantes.exclude(id=request.user.id).first()

    if outro and _esta_bloqueado(request.user, outro):
        return JsonResponse({'erro': _('Não é possível enviar mensagens para este usuário.')}, status=403)

    if outro and not _sao_amigos_ativos(request.user, outro):
        return JsonResponse({'erro': _('Vocês não são mais amigos. Não é possível enviar mensagens.')}, status=403)

    conteudo = request.POST.get('conteudo', '').strip()

    if not conteudo:
        return JsonResponse({'erro': _('Mensagem vazia.')}, status=400)

    if len(conteudo) > 2000:
        return JsonResponse({'erro': _('Mensagem muito longa.')}, status=400)

    with transaction.atomic():
        if not conversa.ativa:
            Conversa.objects.filter(pk=conversa.pk).update(ativa=True)

        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            conteudo=conteudo,
        )
        Conversa.objects.filter(pk=conversa.pk).update(
            data_ultima_mensagem=timezone.now()
        )

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'status': 'ok',
            'id': mensagem.id,
            'conteudo': mensagem.conteudo,
            'hora': mensagem.data_envio.strftime('%H:%M'),
            'remetente_uuid': str(request.user.uuid),
        })

    return redirect('chat:conversa', uuid_conversa=uuid_conversa)


# =========================
# POLLING DE MENSAGENS
# =========================

@login_required
@require_http_methods(["GET"])
def view_mensagens_json(request, uuid_conversa):
    """
    Endpoint de polling do chat. Retorna mensagens novas e eventos de controle.

    Além das mensagens, pode retornar um campo `evento` que o cliente JS
    usa para reagir em tempo real sem necessidade de refresh manual:

      evento: 'bloqueado'        → redireciona para /chat/conversas/
      evento: 'amizade_desfeita' → desativa o input, exibe aviso
      evento: 'conversa_limpa'   → apaga o DOM e reseta _ultimoId para 0
      evento: None               → fluxo normal
    """
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    outro = conversa.participantes.exclude(id=request.user.id).first()

    # ── Verificações de estado da relação ──────────────────
    if outro and _esta_bloqueado(request.user, outro):
        return JsonResponse({'evento': 'bloqueado'})

    amigos = _sao_amigos_ativos(request.user, outro) if outro else False

    try:
        after_id = int(request.GET.get('after', 0))
    except (ValueError, TypeError):
        return JsonResponse({'erro': _('Parâmetro inválido.')}, status=400)

    # ── Detecta limpeza de conversa ────────────────────────
    # Se o cliente tem um after_id > 0 mas não existe nenhuma mensagem
    # com id <= after_id, significa que o histórico foi apagado.
    if after_id > 0:
        ainda_existe = Mensagem.objects.filter(
            conversa=conversa, id=after_id
        ).exists()
        if not ainda_existe:
            return JsonResponse({'evento': 'conversa_limpa'})

    novas = list(
        Mensagem.objects
        .filter(conversa=conversa, id__gt=after_id)
        .select_related('remetente')
        .order_by('data_envio')
    )

    ids_para_marcar = [
        m.id for m in novas
        if not m.lida and m.remetente_id != request.user.id
    ]
    if ids_para_marcar:
        Mensagem.objects.filter(id__in=ids_para_marcar).update(
            lida=True,
            data_leitura=timezone.now(),
        )

    digitando = (
        hasattr(conversa, 'digitando_por')
        and outro is not None
        and conversa.digitando_por.filter(id=outro.id).exists()
    )

    return JsonResponse({
        'evento': None if amigos else 'amizade_desfeita',
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


# =========================
# APAGAR CONVERSA
# =========================

@login_required
@require_POST
def view_apagar_conversa(request, uuid_conversa):
    """
    Limpa o histórico de mensagens visível para o usuário que pediu.

    Comportamento intencional:
    - Apaga TODAS as mensagens da conversa (ambos veem o histórico limpo).
    - A conversa em si permanece ATIVA — o outro participante ainda pode
      enviar mensagens e receber notificações normalmente.
    - Isso evita o bug onde desativar a conversa impede o outro usuário
      de abrir o chat ou receber notificações.

    Se quiser limpar apenas para si (sem afetar o outro), isso requer
    um campo de "ocultação por participante" no model Conversa.
    """
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    try:
        with transaction.atomic():
            conversa_locked = (
                Conversa.objects
                .select_for_update()
                .get(pk=conversa.pk)
            )
            qtd, _ = Mensagem.objects.filter(conversa=conversa_locked).delete()

            # Garante que a conversa fique ativa após a limpeza
            if not conversa_locked.ativa:
                conversa_locked.ativa = True
                conversa_locked.save(update_fields=['ativa'])

        logger.info(
            'Histórico da conversa %s limpo por %s (%d mensagens removidas)',
            uuid_conversa, request.user.email, qtd,
        )
        return JsonResponse({'status': 'ok', 'mensagens_removidas': qtd})

    except Exception as e:
        logger.error('Erro ao limpar conversa %s: %s', uuid_conversa, e)
        return JsonResponse({'erro': _('Não foi possível limpar a conversa.')}, status=500)


# =========================
# APAGAR MENSAGEM
# =========================

@login_required
@require_http_methods(["POST"])
def view_apagar_mensagem(request, mensagem_id):
    """Remove uma mensagem, garantindo que só o remetente possa fazê-lo."""
    mensagem = get_object_or_404(Mensagem, id=mensagem_id)

    if mensagem.remetente != request.user:
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    conversa_uuid = str(mensagem.conversa.uuid)
    mensagem.delete()

    logger.info('Mensagem %s apagada por %s', mensagem_id, request.user.email)

    return JsonResponse({'status': 'ok', 'conversa_uuid': conversa_uuid})


# =========================
# NÃO LIDAS
# =========================

@login_required
@require_http_methods(["GET"])
def view_nao_lidas_json(request):
    """
    Retorna, por UUID de conversa, a contagem de mensagens não lidas.
    Resolve o problema N+1 anterior com uma única query agregada.
    """
    contagens = (
        Mensagem.objects
        .filter(
            conversa__participantes=request.user,
            conversa__ativa=True,
            lida=False,
        )
        .exclude(remetente=request.user)
        .values('conversa__uuid')
        .annotate(total=Count('id'))
    )

    data = {str(row['conversa__uuid']): row['total'] for row in contagens}

    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def view_nao_lidas_detalhes_json(request):
    """
    Versão enriquecida de não-lidas usada pelo polling global (base.html).
    Compatível com SQLite e PostgreSQL — não usa DISTINCT ON.

    Retorna uma lista de objetos, um por conversa com mensagens não lidas:
    [
      {
        "uuid":    "<uuid da conversa>",
        "total":   <int>,
        "nome":    "<str>",
        "inicial": "<char>",
        "foto":    "<url ou ''>",
        "preview": "<str até 60 chars>"
      },
      ...
    ]
    """
    from django.db.models import Max

    # Passo 1: contagens e ID da mensagem mais recente por conversa — duas queries,
    # ambas compatíveis com qualquer banco suportado pelo Django.
    agregados = (
        Mensagem.objects
        .filter(
            conversa__participantes=request.user,
            lida=False,
        )
        .exclude(remetente=request.user)
        .values('conversa__uuid')
        .annotate(total=Count('id'), ultima_id=Max('id'))
    )

    if not agregados:
        return JsonResponse([], safe=False)

    # Passo 2: busca os objetos Mensagem correspondentes aos IDs máximos
    ids_ultimas  = [row['ultima_id'] for row in agregados]
    totais_map   = {str(row['conversa__uuid']): row['total'] for row in agregados}

    mensagens_map = {
        str(m.conversa.uuid): m
        for m in (
            Mensagem.objects
            .filter(id__in=ids_ultimas)
            .select_related('remetente', 'conversa')
        )
    }

    resultado = []
    for uuid, total in totais_map.items():
        msg = mensagens_map.get(uuid)
        if not msg:
            continue

        remetente = msg.remetente
        nome = remetente.get_nome_exibicao()

        foto_url = ''
        if hasattr(remetente, 'foto_perfil') and remetente.foto_perfil:
            try:
                foto_url = remetente.foto_perfil.url
            except Exception:
                pass

        preview = msg.conteudo
        if preview.lstrip().startswith('{'):
            preview = '📍 Compartilhou uma viagem'
        elif len(preview) > 60:
            preview = preview[:57] + '…'

        resultado.append({
            'uuid':    uuid,
            'total':   total,
            'nome':    nome,
            'inicial': nome[0].upper() if nome else '?',
            'foto':    foto_url,
            'preview': preview,
        })

    return JsonResponse(resultado, safe=False)


# =========================
# DIGITANDO
# =========================

@login_required
@require_http_methods(["POST"])
def view_digitando(request, uuid_conversa):
    """Marca que o usuário está digitando nesta conversa."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    if hasattr(conversa, 'digitando_por'):
        conversa.digitando_por.add(request.user)

    return JsonResponse({'status': 'ok'})


@login_required
@require_http_methods(["POST"])
def view_parou_digitar(request, uuid_conversa):
    """Remove o indicador de digitação do usuário nesta conversa."""
    conversa = get_object_or_404(Conversa, uuid=uuid_conversa)

    if not _verificar_participante(conversa, request.user):
        return JsonResponse({'erro': _('Sem permissão.')}, status=403)

    if hasattr(conversa, 'digitando_por'):
        conversa.digitando_por.remove(request.user)

    return JsonResponse({'status': 'ok'})


# =========================
# AMIZADE / BLOQUEIO
# =========================

@login_required
@require_http_methods(["POST"])
def view_desfazer_amizade_ajax(request, uuid_amigo):
    """Desfaz amizade entre o usuário autenticado e o amigo indicado."""
    amigo = get_object_or_404(Usuario, uuid=uuid_amigo)

    if not Amizade.sao_amigos(request.user, amigo):
        return JsonResponse({'erro': _('Vocês não são amigos.')}, status=400)

    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=amigo) |
                Q(usuario1=amigo, usuario2=request.user),
                ativa=True,
            ).first()
            if amizade:
                amizade.desfazer_amizade()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error('Erro ao desfazer amizade %s: %s', uuid_amigo, e)
        return JsonResponse({'erro': _('Erro ao remover amigo.')}, status=500)


@login_required
@require_http_methods(["POST"])
def view_bloquear_usuario(request, uuid_usuario):
    """
    Bloqueia um usuário: desfaz amizade, desativa conversas em comum
    e registra o bloqueio.
    """
    alvo = get_object_or_404(Usuario, uuid=uuid_usuario)

    if alvo == request.user:
        return JsonResponse({'erro': _('Operação inválida.')}, status=400)

    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=alvo) |
                Q(usuario1=alvo, usuario2=request.user),
                ativa=True,
            ).first()
            if amizade:
                amizade.desfazer_amizade()

            Conversa.objects.filter(
                participantes=request.user,
                ativa=True,
            ).filter(participantes=alvo).update(ativa=False)

            Bloqueio.objects.get_or_create(bloqueador=request.user, bloqueado=alvo)

        logger.info('Usuário %s bloqueou %s', request.user.email, alvo.email)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error('Erro ao bloquear %s: %s', uuid_usuario, e)
        return JsonResponse({'erro': _('Erro ao bloquear.')}, status=500)


@login_required
@require_http_methods(["POST"])
def view_desbloquear_usuario(request, uuid_usuario):
    """Remove o bloqueio sobre um usuário."""
    alvo = get_object_or_404(Usuario, uuid=uuid_usuario)

    try:
        deleted, _ = Bloqueio.objects.filter(
            bloqueador=request.user,
            bloqueado=alvo,
        ).delete()

        if deleted:
            logger.info('Usuário %s desbloqueou %s', request.user.email, alvo.email)
            return JsonResponse({'status': 'ok'})

        return JsonResponse({'erro': _('Bloqueio não encontrado.')}, status=404)
    except Exception as e:
        logger.error('Erro ao desbloquear %s: %s', uuid_usuario, e)
        return JsonResponse({'erro': _('Erro ao desbloquear.')}, status=500)


# =========================
# CONVERSA COM CONTEXTO DE VIAGEM
# =========================

@login_required
@require_http_methods(["GET"])
def view_iniciar_conversa_viagem(request, uuid_usuario, uuid_plano):
    """
    Abre o chat com contexto de um plano de viagem.

    Sempre envia o card do plano, exceto se o mesmo plano já foi compartilhado
    nesta conversa nos últimos 5 minutos (evita spam por cliques repetidos).
    """
    import json
    from apps.destinos.models import PlanoViagem

    outro_usuario = get_object_or_404(Usuario, uuid=uuid_usuario)
    plano = get_object_or_404(PlanoViagem, uuid=uuid_plano)

    if outro_usuario == request.user:
        return redirect('destinos:detalhes_plano', uuid=uuid_plano)

    if _esta_bloqueado(request.user, outro_usuario):
        messages.error(request, _('Não é possível iniciar esta conversa.'))
        return redirect('destinos:buscar')

    if not Amizade.sao_amigos(request.user, outro_usuario):
        messages.error(request, _('Você só pode conversar com amigos.'))
        return redirect('destinos:buscar')

    conversa = Conversa.obter_ou_criar_conversa(request.user, outro_usuario)

    if not conversa.ativa:
        conversa.ativa = True
        conversa.save(update_fields=['ativa'])

    # Evita reenvio do mesmo card nos últimos 5 minutos (clique duplo, etc.)
    uuid_plano_str = str(plano.uuid)
    limite = timezone.now() - timezone.timedelta(minutes=5)
    ja_enviado = conversa.mensagens.filter(
        remetente=request.user,
        data_envio__gte=limite,
        conteudo__contains=uuid_plano_str,
    ).exists()

    if not ja_enviado:
        destino = plano.pais_destino.nome if plano.pais_destino else 'Destino indefinido'
        cidade  = plano.cidade_destino or ''
        motivo  = plano.get_motivo_viagem_display() if hasattr(plano, 'get_motivo_viagem_display') else ''

        periodo = ''
        if plano.data_inicio:
            periodo = plano.data_inicio.strftime('%d/%m/%Y')
            if plano.data_fim:
                periodo += f' → {plano.data_fim.strftime("%d/%m/%Y")}'

        duracao = f'{plano.duracao_dias} dias' if plano.duracao_dias else None

        imagem_url = ''
        if plano.imagens_urls:
            imagem_url = plano.imagens_urls[0]
        elif plano.pais_destino and plano.pais_destino.codigo_iso:
            imagem_url = f'https://flagcdn.com/w640/{plano.pais_destino.codigo_iso.lower()}.png'

        card_data = {
            '__tipo':    'viagem_card',
            'destino':   destino,
            'cidade':    cidade,
            'periodo':   periodo,
            'duracao':   duracao,
            'motivo':    motivo,
            'imagem':    imagem_url,
            'url':       f'/destinos/{plano.uuid}/',
            'uuid_plano': uuid_plano_str,
            'mensagem':  'Oi! Vi sua viagem e adorei o destino. Topa trocar uma ideia? ✈️🌍',
        }

        with transaction.atomic():
            Mensagem.objects.create(
                conversa=conversa,
                remetente=request.user,
                conteudo=json.dumps(card_data, ensure_ascii=False),
            )
            Conversa.objects.filter(pk=conversa.pk).update(
                data_ultima_mensagem=timezone.now()
            )

        logger.info('Card de viagem enviado: %s -> %s (plano %s)',
                    request.user.email, outro_usuario.email, uuid_plano_str)

    return redirect('chat:conversa', uuid_conversa=conversa.uuid)