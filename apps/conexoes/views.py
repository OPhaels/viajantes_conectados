import logging
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from apps.usuarios.models import Usuario

from .models import Amizade, Bloqueio, SolicitacaoAmizade

logger = logging.getLogger(__name__)


# =========================
# HELPER INTERNO
# =========================


def _ha_bloqueio(usuario_a, usuario_b):
    """Retorna True se existe bloqueio em qualquer direção entre os dois."""
    return Bloqueio.objects.filter(
        Q(bloqueador=usuario_a, bloqueado=usuario_b)
        | Q(bloqueador=usuario_b, bloqueado=usuario_a)
    ).exists()


def _criar_amizade_atomica(user_a, user_b, solicitacao=None):
    """
    Cria ou reativa amizade entre dois usuários e opcionalmente
    marca a solicitação como aceita. Deve ser chamado dentro de atomic().
    """
    amizade, criada = Amizade.objects.get_or_create(
        usuario1=min(user_a, user_b, key=lambda u: u.id),
        usuario2=max(user_a, user_b, key=lambda u: u.id),
        defaults={"ativa": True},
    )
    if not criada:
        amizade.ativa = True
        amizade.save(update_fields=["ativa"])

    if solicitacao:
        solicitacao.status = "aceita"
        solicitacao.data_resposta = timezone.now()
        solicitacao.save(update_fields=["status", "data_resposta"])

    return amizade


# =========================
# ENVIAR SOLICITAÇÃO (form normal)
# =========================


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_enviar_solicitacao_amizade(request, uuid_usuario):
    """Envia uma solicitação de amizade para outro usuário."""
    destinatario = get_object_or_404(Usuario, uuid=uuid_usuario)

    if destinatario == request.user:
        messages.error(request, _("Você não pode enviar solicitação para si mesmo."))
        return redirect("destinos:buscar")

    if not request.user.pode_enviar_solicitacao_amizade():
        messages.error(request, _("Verifique seu email antes de enviar solicitações."))
        return redirect("usuarios:perfil")

    if not destinatario.ativo:
        messages.error(request, _("Este usuário não está disponível."))
        return redirect("destinos:buscar")

    # ── Bloqueio em qualquer direção ──────────────────────
    if _ha_bloqueio(request.user, destinatario):
        messages.error(
            request, _("Não é possível enviar solicitação para este usuário.")
        )
        return redirect("destinos:buscar")

    if Amizade.sao_amigos(request.user, destinatario):
        messages.info(request, _("Você já é amigo deste usuário."))
        return redirect("conexoes:amigos")

    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=destinatario)
        | Q(remetente=destinatario, destinatario=request.user),
        status="pendente",
    ).first()

    if solicitacao_existente:
        # Destinatário já enviou para mim → aceitar automaticamente
        if solicitacao_existente.remetente == destinatario:
            try:
                with transaction.atomic():
                    _criar_amizade_atomica(
                        request.user, destinatario, solicitacao_existente
                    )
                messages.success(
                    request,
                    _("Parabéns! Você e {} agora são amigos!").format(
                        destinatario.get_nome_exibicao()
                    ),
                )
                logger.info(
                    "Amizade automática criada: %s <-> %s",
                    request.user.email,
                    destinatario.email,
                )
                return redirect("conexoes:amigos")
            except Exception as e:
                logger.error("Erro ao criar amizade automática: %s", e)
                messages.error(
                    request, _("Erro ao processar solicitação. Tente novamente.")
                )
                return redirect("destinos:buscar")
        else:
            messages.info(request, _("Já existe uma solicitação pendente entre vocês."))
            return redirect("conexoes:solicitacoes")

    limite_tempo = timezone.now() - timedelta(hours=1)
    if (
        SolicitacaoAmizade.objects.filter(
            remetente=request.user, data_criacao__gte=limite_tempo
        ).count()
        >= 10
    ):
        messages.error(request, _("Limite de solicitações por hora atingido."))
        logger.warning("Limite de solicitações excedido: %s", request.user.email)
        return redirect("destinos:buscar")

    try:
        with transaction.atomic():
            mensagem = request.POST.get("mensagem", "").strip()
            SolicitacaoAmizade.objects.create(
                remetente=request.user,
                destinatario=destinatario,
                mensagem=mensagem[:500],
            )
        messages.success(
            request, _(f"Solicitação enviada para {destinatario.get_nome_exibicao()}!")
        )
        logger.info(
            "Solicitação enviada: %s -> %s", request.user.email, destinatario.email
        )
    except Exception as e:
        logger.error("Erro ao enviar solicitação: %s", e)
        messages.error(request, _("Erro ao enviar solicitação. Tente novamente."))

    return redirect("destinos:buscar")


# =========================
# ENVIAR SOLICITAÇÃO (AJAX / get_or_create)
# =========================


@login_required
@require_POST
def enviar_solicitacao(request, uuid_destinatario):
    """Envia solicitação via AJAX com get_or_create."""
    destinatario = get_object_or_404(Usuario, uuid=uuid_destinatario)

    if destinatario == request.user:
        messages.error(request, _("Operação inválida."))
        return redirect("destinos:buscar")

    # ── Bloqueio em qualquer direção ──────────────────────
    if _ha_bloqueio(request.user, destinatario):
        messages.error(
            request, _("Não é possível enviar solicitação para este usuário.")
        )
        return redirect("destinos:buscar")

    if Amizade.sao_amigos(request.user, destinatario):
        messages.info(request, _("Vocês já são amigos."))
        return redirect("conexoes:amigos")

    solicitacao_existente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=destinatario)
        | Q(remetente=destinatario, destinatario=request.user),
        status="pendente",
    ).first()

    if solicitacao_existente:
        if solicitacao_existente.remetente == destinatario:
            try:
                with transaction.atomic():
                    _criar_amizade_atomica(
                        request.user, destinatario, solicitacao_existente
                    )
                messages.success(
                    request,
                    _("Parabéns! Você e {} agora são amigos!").format(
                        destinatario.get_nome_exibicao()
                    ),
                )
                logger.info(
                    "Amizade automática criada: %s <-> %s",
                    request.user.email,
                    destinatario.email,
                )
                return redirect("conexoes:amigos")
            except Exception as e:
                logger.error("Erro ao criar amizade automática: %s", e)
                messages.error(
                    request, _("Erro ao processar solicitação. Tente novamente.")
                )
                return redirect("destinos:buscar")
        else:
            messages.warning(request, _("Solicitação já enviada anteriormente."))
            return redirect("conexoes:solicitacoes")

    try:
        with transaction.atomic():
            solicitacao, criado = SolicitacaoAmizade.objects.get_or_create(
                remetente=request.user,
                destinatario=destinatario,
                defaults={"status": "pendente"},
            )
            if criado:
                messages.success(request, _("Solicitação enviada com sucesso!"))
                logger.info(
                    "Solicitação enviada: %s -> %s",
                    request.user.email,
                    destinatario.email,
                )
            elif solicitacao.status == "pendente":
                messages.warning(request, _("Solicitação já enviada anteriormente."))
            else:
                solicitacao.status = "pendente"
                solicitacao.data_criacao = timezone.now()
                solicitacao.save(update_fields=["status", "data_criacao"])
                messages.success(request, _("Solicitação enviada com sucesso!"))
                logger.info(
                    "Solicitação reativada: %s -> %s",
                    request.user.email,
                    destinatario.email,
                )
    except Exception as e:
        logger.error("Erro ao enviar solicitação: %s", e)
        messages.error(request, _("Erro ao enviar solicitação. Tente novamente."))

    return redirect("destinos:buscar")


# =========================
# LISTA DE SOLICITAÇÕES
# =========================


@login_required
@require_http_methods(["GET"])
def view_lista_solicitacoes(request):
    """Lista solicitações recebidas, enviadas, amigos e sugestões."""
    # Achata os pares em um set simples
    ids_excluir = set()
    for par in Bloqueio.objects.filter(
        Q(bloqueador=request.user) | Q(bloqueado=request.user)
    ).values_list("bloqueador_id", "bloqueado_id"):
        ids_excluir.update(par)
    ids_excluir.discard(request.user.id)

    # Solicitações recebidas — exclui remetentes bloqueados
    solicitacoes_recebidas = (
        SolicitacaoAmizade.objects.filter(
            destinatario=request.user,
            status="pendente",
        )
        .exclude(
            remetente__id__in=ids_excluir,
        )
        .select_related("remetente")
        .order_by("-data_criacao")
    )

    solicitacoes_enviadas = (
        SolicitacaoAmizade.objects.filter(
            remetente=request.user,
            status="pendente",
        )
        .select_related("destinatario")
        .order_by("-data_criacao")
    )

    amizades = (
        Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True,
        )
        .select_related("usuario1", "usuario2")
        .order_by("-data_criacao")
    )

    amigos_dados = []
    pendentes_ids = set()
    pendentes_ids.add(request.user.id)

    for amizade in amizades:
        amigo = (
            amizade.usuario2 if amizade.usuario1 == request.user else amizade.usuario1
        )
        planos_amigo = amigo.planos_viagem.filter(
            ativo=True, viagem_concluida=False
        ).select_related("pais_destino")
        amigos_dados.append(
            {"amigo": amigo, "amizade": amizade, "planos": planos_amigo}
        )
        pendentes_ids.add(amigo.id)

    for r, d in SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user) | Q(destinatario=request.user),
        status="pendente",
    ).values_list("remetente_id", "destinatario_id"):
        pendentes_ids.add(r)
        pendentes_ids.add(d)

    bloqueados = (
        Bloqueio.objects.filter(
            bloqueador=request.user,
        )
        .select_related("bloqueado")
        .order_by("-data_criacao")
    )
    for b in bloqueados:
        pendentes_ids.add(b.bloqueado.id)

    # Sugestões excluem bloqueados
    sugestoes = (
        Usuario.objects.filter(ativo=True)
        .exclude(id__in=pendentes_ids | ids_excluir)
        .order_by("?")[:8]
    )

    return render(
        request,
        "conexoes/solicitacoes.html",
        {
            "solicitacoes_recebidas": solicitacoes_recebidas,
            "solicitacoes_enviadas": solicitacoes_enviadas,
            "amigos_dados": amigos_dados,
            "sugestoes": sugestoes,
            "bloqueados": bloqueados,
            "titulo": _("Solicitações de Amizade"),
            "hoje": date.today().strftime("%Y-%m-%d"),
        },
    )


# =========================
# RESPONDER SOLICITAÇÃO
# =========================


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_responder_solicitacao(request, uuid_solicitacao, acao):
    """
    Responde a uma solicitação de amizade.
    Rejeita automaticamente se houver bloqueio ativo entre os usuários.
    """
    solicitacao = get_object_or_404(
        SolicitacaoAmizade,
        uuid=uuid_solicitacao,
        destinatario=request.user,
        status="pendente",
    )

    try:
        with transaction.atomic():
            if acao == "aceitar":
                # Bloquear aceite se houver bloqueio (pode ter sido bloqueado
                # após o envio)
                if _ha_bloqueio(request.user, solicitacao.remetente):
                    solicitacao.status = "recusada"
                    solicitacao.data_resposta = timezone.now()
                    solicitacao.save(update_fields=["status", "data_resposta"])
                    messages.error(
                        request, _("Não é possível aceitar esta solicitação.")
                    )
                    return redirect("conexoes:solicitacoes")

                if Amizade.sao_amigos(request.user, solicitacao.remetente):
                    solicitacao.status = "aceita"
                    solicitacao.save(update_fields=["status"])
                    messages.info(request, _("Vocês já eram amigos!"))
                    return redirect("conexoes:amigos")

                _criar_amizade_atomica(request.user, solicitacao.remetente, solicitacao)
                messages.success(
                    request,
                    _(
                        f"Você agora é amigo de {solicitacao.remetente.get_nome_exibicao()}!"
                    ),
                )
                logger.info(
                    "Solicitação aceita: %s <-> %s",
                    solicitacao.remetente.email,
                    request.user.email,
                )

            elif acao in ("rejeitar", "recusar"):
                solicitacao.status = "recusada"
                solicitacao.data_resposta = timezone.now()
                solicitacao.save(update_fields=["status", "data_resposta"])
                messages.info(request, _("Solicitação rejeitada."))
                logger.info(
                    "Solicitação rejeitada: %s -> %s",
                    solicitacao.remetente.email,
                    request.user.email,
                )

            else:
                messages.error(request, _("Ação inválida."))
                return redirect("conexoes:solicitacoes")

    except Exception as e:
        logger.error("Erro ao responder solicitação: %s", e)
        messages.error(request, _("Erro ao processar solicitação. Tente novamente."))

    return redirect("conexoes:solicitacoes")


# =========================
# CANCELAR SOLICITAÇÃO
# =========================


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_cancelar_solicitacao(request, uuid_solicitacao):
    """Cancela uma solicitação enviada."""
    solicitacao = get_object_or_404(
        SolicitacaoAmizade,
        uuid=uuid_solicitacao,
        remetente=request.user,
        status="pendente",
    )
    try:
        solicitacao.status = "cancelada"
        solicitacao.save(update_fields=["status"])
        messages.success(request, _("Solicitação cancelada."))
        logger.info("Solicitação cancelada: %s", request.user.email)
    except Exception as e:
        logger.error("Erro ao cancelar solicitação: %s", e)
        messages.error(request, _("Erro ao cancelar solicitação."))

    return redirect("conexoes:solicitacoes")


# =========================
# LISTA DE AMIGOS
# =========================


@login_required
@require_http_methods(["GET"])
def view_lista_amigos(request):
    """Lista todos os amigos do usuário."""
    try:
        amizades = (
            Amizade.objects.filter(
                Q(usuario1=request.user) | Q(usuario2=request.user),
                ativa=True,
            )
            .select_related("usuario1", "usuario2")
            .order_by("-data_criacao")
        )

        amigos_dados = []
        amigos_ids = set()

        for amizade in amizades:
            amigo = (
                amizade.usuario2
                if amizade.usuario1 == request.user
                else amizade.usuario1
            )
            planos_amigo = amigo.planos_viagem.filter(
                ativo=True,
                viagem_concluida=False,
            ).select_related("pais_destino")
            amigos_dados.append(
                {"amigo": amigo, "amizade": amizade, "planos": planos_amigo}
            )
            amigos_ids.add(amigo.id)

        logger.info("Usuário %s tem %d amigos", request.user.email, len(amigos_dados))

        paginador = Paginator(amigos_dados, 12)
        amigos_paginados = paginador.get_page(request.GET.get("page", 1))

        pendentes_ids = set()
        for r, d in SolicitacaoAmizade.objects.filter(
            Q(remetente=request.user) | Q(destinatario=request.user),
            status="pendente",
        ).values_list("remetente_id", "destinatario_id"):
            pendentes_ids.add(r)
            pendentes_ids.add(d)

        # Bloqueados não aparecem na lista de conexões possíveis
        bloqueados_ids = set()
        for par in Bloqueio.objects.filter(
            Q(bloqueador=request.user) | Q(bloqueado=request.user)
        ).values_list("bloqueador_id", "bloqueado_id"):
            bloqueados_ids.update(par)
        bloqueados_ids.discard(request.user.id)

        todos_usuarios = []
        for usuario in (
            Usuario.objects.filter(ativo=True)
            .exclude(id=request.user.id)
            .exclude(id__in=bloqueados_ids)
        ):
            if usuario.id in amigos_ids:
                status = "amigo"
            elif usuario.id in pendentes_ids:
                status = "pendente"
            else:
                status = "nenhum"
            todos_usuarios.append({"usuario": usuario, "status": status})

        return render(
            request,
            "conexoes/lista_amigos.html",
            {
                "amigos_dados": amigos_paginados,
                "total_amigos": len(amigos_dados),
                "todos_usuarios": todos_usuarios,
                "titulo": _("Meus Amigos"),
            },
        )

    except Exception as e:
        logger.error("Erro ao listar amigos para %s: %s", request.user.email, e)
        messages.error(request, _("Erro ao carregar lista de amigos. Tente novamente."))
        return render(
            request,
            "conexoes/lista_amigos.html",
            {
                "amigos_dados": [],
                "total_amigos": 0,
                "titulo": _("Meus Amigos"),
            },
        )


# =========================
# DESFAZER AMIZADE
# =========================


@login_required
@csrf_protect
@require_http_methods(["POST"])
def view_desfazer_amizade(request, uuid_amigo):
    """Remove uma amizade."""
    amigo = get_object_or_404(Usuario, uuid=uuid_amigo)

    if not Amizade.sao_amigos(request.user, amigo):
        messages.error(request, _("Vocês não são amigos."))
        return redirect("conexoes:amigos")

    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=amigo)
                | Q(usuario1=amigo, usuario2=request.user),
                ativa=True,
            ).first()
            if amizade:
                amizade.desfazer_amizade()
                messages.success(
                    request, _(f"Amizade com {amigo.get_nome_exibicao()} desfeita.")
                )
                logger.info(
                    "Amizade desfeita: %s <-> %s", request.user.email, amigo.email
                )
            else:
                messages.error(request, _("Amizade não encontrada."))
    except Exception as e:
        logger.error("Erro ao desfazer amizade: %s", e)
        messages.error(request, _("Erro ao desfazer amizade. Tente novamente."))

    return redirect("conexoes:amigos")


@login_required
@require_http_methods(["POST"])
def view_desfazer_amizade_ajax(request, uuid_amigo):
    """Remove amizade via AJAX."""
    amigo = get_object_or_404(Usuario, uuid=uuid_amigo)
    if not Amizade.sao_amigos(request.user, amigo):
        return JsonResponse({"erro": "Vocês não são amigos."}, status=400)
    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=amigo)
                | Q(usuario1=amigo, usuario2=request.user),
                ativa=True,
            ).first()
            if amizade:
                amizade.desfazer_amizade()
        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.error("Erro ao desfazer amizade %s: %s", uuid_amigo, e)
        return JsonResponse({"erro": "Erro ao remover amigo."}, status=500)


# =========================
# BLOQUEAR / DESBLOQUEAR
# =========================


@login_required
@require_http_methods(["POST"])
def view_bloquear_usuario(request, uuid_usuario):
    """Bloqueia um usuário: desfaz amizade, desativa conversas e registra o bloqueio."""
    alvo = get_object_or_404(Usuario, uuid=uuid_usuario)

    if alvo == request.user:
        return JsonResponse({"erro": "Operação inválida."}, status=400)

    try:
        with transaction.atomic():
            amizade = Amizade.objects.filter(
                Q(usuario1=request.user, usuario2=alvo)
                | Q(usuario1=alvo, usuario2=request.user),
                ativa=True,
            ).first()
            if amizade:
                amizade.desfazer_amizade()

            # Cancela solicitações pendentes em ambas as direções
            SolicitacaoAmizade.objects.filter(
                Q(remetente=request.user, destinatario=alvo)
                | Q(remetente=alvo, destinatario=request.user),
                status="pendente",
            ).update(status="cancelada")

            try:
                from apps.chat.models import Conversa

                Conversa.objects.filter(
                    participantes=request.user,
                    ativa=True,
                ).filter(
                    participantes=alvo
                ).update(ativa=False)
            except Exception as e:
                logger.warning("Erro ao desativar conversas: %s", e)

            Bloqueio.objects.get_or_create(bloqueador=request.user, bloqueado=alvo)

        logger.info("Usuário %s bloqueou %s", request.user.email, alvo.email)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.error("Erro ao bloquear %s: %s", uuid_usuario, e)
        return JsonResponse({"erro": "Erro ao bloquear."}, status=500)


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
            logger.info("Usuário %s desbloqueou %s", request.user.email, alvo.email)
            return JsonResponse({"status": "ok"})
        return JsonResponse({"erro": "Bloqueio não encontrado."}, status=404)
    except Exception as e:
        logger.error("Erro ao desbloquear %s: %s", uuid_usuario, e)
        return JsonResponse({"erro": "Erro ao desbloquear."}, status=500)
