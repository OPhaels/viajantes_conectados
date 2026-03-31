import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.conexoes.models import Amizade, Bloqueio
from apps.usuarios.models import Usuario

from .forms import FormularioBuscaViajantes, FormularioPlanoViagem
from .models import EnderecoPlano, Pais, PlanoViagem

logger = logging.getLogger(__name__)


# =========================
# HELPER INTERNO
# =========================


def _ids_bloqueados(usuario):
    """
    Retorna um set com os IDs de todos os usuários que bloquearam
    ou foram bloqueados pelo usuário informado.
    Usado para excluir essas pessoas de listagens e buscas.
    """
    qs = Bloqueio.objects.filter(
        Q(bloqueador=usuario) | Q(bloqueado=usuario)
    ).values_list("bloqueador_id", "bloqueado_id")

    ids = set()
    for bloqueador_id, bloqueado_id in qs:
        ids.add(bloqueador_id)
        ids.add(bloqueado_id)
    ids.discard(usuario.id)  # Remove o próprio usuário do set
    return ids


# =========================
# CRIAR PLANO
# =========================


@login_required
@require_http_methods(["GET", "POST"])
def view_criar_plano_viagem(request):
    """View para criar plano de viagem com país automático."""
    if request.method == "POST":
        pais_nome = request.POST.get("pais_nome", "").strip()
        pais_codigo_iso = request.POST.get("pais_codigo_iso", "").strip()
        cidade = request.POST.get("cidade_destino", "").strip()
        regiao = request.POST.get("regiao_destino", "").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()

        if not pais_nome:
            messages.error(request, "Por favor, selecione uma localização no mapa.")
            form = FormularioPlanoViagem(request.POST)
            return render(
                request,
                "destinos/criar_plano.html",
                {
                    "titulo": "Criar Plano de Viagem",
                    "formulario": form,
                    "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
                },
            )

        try:
            with transaction.atomic():
                pais = None

                if pais_codigo_iso:
                    pais = Pais.objects.filter(
                        codigo_iso__iexact=pais_codigo_iso
                    ).first()

                if not pais:
                    pais = Pais.objects.filter(nome__iexact=pais_nome).first()

                if not pais:
                    logger.info(
                        "Criando novo país: %s (%s)", pais_nome, pais_codigo_iso
                    )
                    lat = float(latitude) if latitude else 0.0
                    lng = float(longitude) if longitude else 0.0
                    pais = Pais.objects.create(
                        codigo_iso=pais_codigo_iso or "XX",
                        nome=pais_nome,
                        nome_completo=pais_nome,
                        continente="Não especificado",
                        latitude=lat,
                        longitude=lng,
                        ativo=True,
                    )
                    messages.success(
                        request,
                        f'País "{pais_nome}" adicionado automaticamente ao sistema!',
                    )

                dados_post = request.POST.copy()
                dados_post["pais_destino"] = pais.id
                dados_post["cidade_destino"] = cidade
                dados_post["regiao_destino"] = regiao

                form = FormularioPlanoViagem(dados_post)

                if form.is_valid():
                    plano = form.save(commit=False)
                    plano.usuario = request.user
                    plano.save()

                    if latitude and longitude:
                        EnderecoPlano.objects.create(
                            plano=plano,
                            cidade=cidade,
                            estado=regiao,
                            pais_texto=pais_nome,
                            latitude=float(latitude),
                            longitude=float(longitude),
                        )

                    messages.success(
                        request, f"Plano de viagem para {pais_nome} criado com sucesso!"
                    )
                    return redirect("destinos:detalhes_plano", uuid=plano.uuid)
                else:
                    messages.error(request, "Corrija os erros no formulário.")
                    logger.error("Erros no formulário: %s", form.errors)
                    return render(
                        request,
                        "destinos/criar_plano.html",
                        {
                            "titulo": "Criar Plano de Viagem",
                            "formulario": form,
                            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
                        },
                    )

        except Exception as e:
            logger.error("Erro ao criar plano de viagem: %s", e, exc_info=True)
            messages.error(
                request, "Erro ao salvar o plano de viagem. Tente novamente."
            )
            form = FormularioPlanoViagem(request.POST)
            return render(
                request,
                "destinos/criar_plano.html",
                {
                    "titulo": "Criar Plano de Viagem",
                    "formulario": form,
                    "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
                },
            )

    form = FormularioPlanoViagem()
    return render(
        request,
        "destinos/criar_plano.html",
        {
            "titulo": "Criar Plano de Viagem",
            "formulario": form,
            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
        },
    )


# =========================
# EDITAR PLANO
# =========================


@login_required
@require_http_methods(["GET", "POST"])
def view_editar_plano(request, uuid):
    plano = get_object_or_404(PlanoViagem, uuid=uuid)

    if plano.usuario != request.user:
        messages.error(request, _("Você não pode editar este plano."))
        return redirect("destinos:meus_planos")

    if request.method == "POST":
        pais_nome = request.POST.get("pais_nome", "").strip()
        cidade = request.POST.get("cidade_destino", "").strip()
        regiao = request.POST.get("regiao_destino", "").strip()
        latitude = request.POST.get("latitude", "").strip().replace(",", ".")
        longitude = request.POST.get("longitude", "").strip().replace(",", ".")

        dados_post = request.POST.copy()
        dados_post["cidade_destino"] = cidade
        dados_post["regiao_destino"] = regiao

        form = FormularioPlanoViagem(dados_post, instance=plano)

        if form.is_valid():
            plano = form.save(commit=False)
            plano.cidade_destino = cidade
            plano.regiao_destino = regiao
            plano.save()

            EnderecoPlano.objects.update_or_create(
                plano=plano,
                defaults={
                    "cidade": cidade,
                    "estado": regiao,
                    "pais_texto": pais_nome or plano.pais_destino.nome,
                    **(
                        {"latitude": float(latitude), "longitude": float(longitude)}
                        if latitude and longitude
                        else {}
                    ),
                },
            )

            messages.success(request, _("Plano de viagem atualizado com sucesso!"))
            return redirect("destinos:detalhes_plano", uuid=plano.uuid)
        else:
            messages.error(request, "Corrija os erros no formulário.")
    else:
        form = FormularioPlanoViagem(instance=plano)

    return render(
        request,
        "destinos/criar_plano.html",
        {
            "titulo": _("Editar Plano de Viagem"),
            "formulario": form,
            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
        },
    )


# =========================
# BUSCAR VIAGENS
# =========================


@login_required
@require_http_methods(["GET"])
def view_buscar_viajantes(request):
    """
    Busca planos de viagem de outros usuários.
    Exclui automaticamente planos de usuários bloqueados (em qualquer direção).
    """
    formulario = FormularioBuscaViajantes(request.GET)
    ids_excluir = _ids_bloqueados(request.user)

    queryset_destinos = (
        PlanoViagem.objects.filter(ativo=True, viagem_concluida=False)
        .exclude(usuario=request.user)
        .exclude(usuario__id__in=ids_excluir)  # ← exclui bloqueados
        .select_related("pais_destino", "usuario")
    )

    if formulario.is_valid():
        dados = formulario.cleaned_data

        if dados.get("pais_destino"):
            queryset_destinos = queryset_destinos.filter(
                pais_destino=dados["pais_destino"]
            )

        if dados.get("data_inicio"):
            data_inicio = dados["data_inicio"]
            data_fim = dados.get("data_fim") or data_inicio + timedelta(days=30)
            queryset_destinos = queryset_destinos.filter(
                Q(data_inicio__lte=data_fim) & Q(data_fim__gte=data_inicio)
            )

        if dados.get("motivo_viagem"):
            queryset_destinos = queryset_destinos.filter(
                motivo_viagem=dados["motivo_viagem"]
            )

        if dados.get("duracao_minima"):
            from django.db.models import DurationField, ExpressionWrapper, F

            queryset_destinos = queryset_destinos.annotate(
                duracao=ExpressionWrapper(
                    F("data_fim") - F("data_inicio"),
                    output_field=DurationField(),
                )
            ).filter(duracao__gte=timedelta(days=dados["duracao_minima"]))

    # Filtro de privacidade (método do model)
    destinos_filtrados = [
        plano for plano in queryset_destinos if plano.pode_ser_visto_por(request.user)
    ]

    paginador = Paginator(destinos_filtrados, 12)
    destinos_paginados = paginador.get_page(request.GET.get("page", 1))

    amigos_ids = set()
    amigos_uuids = set()
    amizades = Amizade.objects.filter(
        Q(usuario1=request.user) | Q(usuario2=request.user),
        ativa=True,
    )
    for a in amizades:
        amigo = a.usuario2 if a.usuario1 == request.user else a.usuario1
        amigos_ids.add(amigo.id)
        amigos_uuids.add(amigo.uuid)

    meus_destinos = PlanoViagem.objects.filter(
        usuario=request.user, ativo=True
    ).select_related("pais_destino")

    return render(
        request,
        "destinos/buscar.html",
        {
            "formulario": formulario,
            "destinos": destinos_paginados,
            "meus_destinos": meus_destinos,
            "amigos_ids": amigos_ids,
            "amigos_uuids": amigos_uuids,
            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
            "total_resultados": len(destinos_filtrados),
            "title": _("Buscar Viagens"),
        },
    )


# =========================
# LISTAR VIAJANTES
# =========================


@login_required
@require_http_methods(["GET"])
def view_listar_viajantes(request):
    """
    Lista usuários com perfil público.
    Exclui usuários bloqueados (em qualquer direção).
    """
    ids_excluir = _ids_bloqueados(request.user)

    queryset_viajantes = (
        Usuario.objects.filter(ativo=True, perfil_publico=True)
        .exclude(uuid=request.user.uuid)
        .exclude(id__in=ids_excluir)  # ← exclui bloqueados
        .order_by("-data_criacao")
    )

    busca = request.GET.get("q", "").strip()
    if busca:
        queryset_viajantes = queryset_viajantes.filter(
            Q(nome_completo__icontains=busca)
            | Q(pais_residencia__icontains=busca)
            | Q(cidade_residencia__icontains=busca)
        )

    pais = request.GET.get("pais", "").strip()
    if pais:
        queryset_viajantes = queryset_viajantes.filter(pais_residencia__icontains=pais)

    cidade = request.GET.get("cidade", "").strip()
    if cidade:
        queryset_viajantes = queryset_viajantes.filter(
            cidade_residencia__icontains=cidade
        )

    paginador = Paginator(queryset_viajantes, 12)
    viajantes_paginados = paginador.get_page(request.GET.get("page", 1))

    amigos_ids = set()
    amizades = Amizade.objects.filter(
        Q(usuario1=request.user) | Q(usuario2=request.user),
        ativa=True,
    )
    for a in amizades:
        amigos_ids.add(a.usuario2.id if a.usuario1 == request.user else a.usuario1.id)

    return render(
        request,
        "destinos/buscar_viajantes.html",
        {
            "viajantes": viajantes_paginados,
            "page_obj": viajantes_paginados,
            "amigos_ids": amigos_ids,
            "total_viajantes": paginador.count,
            "titulo": _("Listar Viajantes"),
        },
    )


# =========================
# MEUS PLANOS
# =========================


@login_required
@require_http_methods(["GET"])
def view_meus_planos(request):
    """Lista os planos de viagem do usuário autenticado."""
    planos = (
        PlanoViagem.objects.filter(usuario=request.user)
        .select_related("pais_destino")
        .order_by("-data_inicio")
    )

    paginador = Paginator(planos, 12)
    planos_paginados = paginador.get_page(request.GET.get("page", 1))

    return render(
        request,
        "destinos/meus_planos.html",
        {
            "meus_planos": planos_paginados,
            "page_obj": planos_paginados,
            "titulo": _("Meus Planos de Viagem"),
        },
    )


# =========================
# DETALHES DO PLANO
# =========================


@login_required
@require_http_methods(["GET"])
def view_detalhes_plano(request, uuid):
    """
    Exibe detalhes de um plano de viagem.
    Bloqueia o acesso se o dono do plano tiver bloqueado o visitante
    ou vice-versa, mesmo que a URL seja conhecida.
    """
    plano = get_object_or_404(PlanoViagem, uuid=uuid)
    dono = plano.usuario

    # Próprio dono sempre tem acesso
    if dono != request.user:
        # Bloqueio em qualquer direção → nega acesso
        if Bloqueio.objects.filter(
            Q(bloqueador=request.user, bloqueado=dono)
            | Q(bloqueador=dono, bloqueado=request.user)
        ).exists():
            messages.error(
                request, _("Você não tem permissão para visualizar este plano.")
            )
            return redirect("destinos:buscar")

        # Verifica privacidade do plano (método do model)
        if not plano.pode_ser_visto_por(request.user):
            messages.error(
                request, _("Você não tem permissão para visualizar este plano.")
            )
            return redirect("destinos:buscar")

    sao_amigos = Amizade.sao_amigos(request.user, dono)

    from apps.conexoes.models import SolicitacaoAmizade

    solicitacao_pendente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=dono)
        | Q(remetente=dono, destinatario=request.user),
        status="pendente",
    ).exists()

    return render(
        request,
        "destinos/detalhes_plano.html",
        {
            "plano": plano,
            "sao_amigos": sao_amigos,
            "e_amigo": sao_amigos,
            "solicitacao_pendente": solicitacao_pendente,
            "MAPBOX_TOKEN": settings.MAPBOX_TOKEN,
            "titulo": f"{plano.pais_destino.nome} — {dono.get_nome_exibicao()}",
        },
    )


# =========================
# DELETAR PLANO
# =========================


@login_required
@require_http_methods(["POST"])
def view_deletar_plano(request, uuid):
    """Deleta um plano de viagem (apenas o próprio dono)."""
    plano = get_object_or_404(PlanoViagem, uuid=uuid)

    if plano.usuario != request.user:
        messages.error(request, _("Você não pode deletar este plano."))
        return redirect("destinos:meus_planos")

    try:
        nome = f"{plano.pais_destino.nome} ({plano.data_inicio.strftime('%d/%m/%Y')})"
        plano.delete()
        messages.success(request, f'Plano de viagem "{nome}" deletado com sucesso!')
        logger.info("Plano deletado por %s: %s", request.user.email, nome)
    except Exception as e:
        logger.error("Erro ao deletar plano: %s", e)
        messages.error(request, _("Erro ao deletar o plano. Tente novamente."))

    return redirect("destinos:meus_planos")


# =========================
# APIs DESCONTINUADAS
# =========================


@login_required
@require_http_methods(["GET"])
def api_paises_autocomplete(request):
    """⚠️ API descontinuada. Use /destinos/api/paises/?search=<termo>"""
    return JsonResponse(
        {
            "erro": "Esta API foi descontinuada.",
            "mensagem": "Use o novo endpoint: GET /destinos/api/paises/?search=<termo>",
            "novo_endpoint": "/destinos/api/paises/?search=",
        },
        status=410,
    )


@login_required
@require_http_methods(["GET"])
def api_estatisticas_destino(request, pais_id):
    """⚠️ API descontinuada. Use /destinos/api/planos/?pais_destino=<id>"""
    return JsonResponse(
        {
            "erro": "Esta API foi descontinuada.",
            "mensagem": "Use o novo endpoint: GET /destinos/api/planos/?pais_destino=<id>",
            "novo_endpoint": "/destinos/api/planos/?pais_destino=",
        },
        status=410,
    )
