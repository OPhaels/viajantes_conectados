from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import logging

from .models import PlanoViagem, Pais
from .forms import FormularioPlanoViagem, FormularioBuscaViajantes
from apps.usuarios.models import Usuario
from apps.conexoes.models import Amizade

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def view_criar_plano_viagem(request):
    """
    View para criar um novo plano de viagem.
    """
    if request.method == 'POST':
        formulario = FormularioPlanoViagem(request.POST)
        
        if formulario.is_valid():
            try:
                plano = formulario.save(commit=False)
                plano.usuario = request.user
                
                # Validar datas
                if plano.data_inicio < timezone.now().date():
                    messages.error(request, _('A data de início não pode ser no passado.'))
                    return render(request, 'destinos/criar_plano.html', {'formulario': formulario})
                
                if plano.data_fim <= plano.data_inicio:
                    messages.error(request, _('A data de término deve ser posterior à data de início.'))
                    return render(request, 'destinos/criar_plano.html', {'formulario': formulario})
                
                plano.save()
                
                messages.success(
                    request,
                    _('Plano de viagem criado com sucesso! Agora você pode encontrar outros viajantes.')
                )
                logger.info(f'Plano de viagem criado: {request.user.email} - {plano.pais_destino.nome}')
                
                return redirect('destinos:buscar')
            
            except Exception as erro:
                logger.error(f'Erro ao criar plano de viagem: {str(erro)}')
                messages.error(request, _('Erro ao criar plano de viagem. Tente novamente.'))
        else:
            for campo, erros in formulario.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        formulario = FormularioPlanoViagem()
    
    # Obter lista de países para o mapa
    paises = Pais.objects.filter(ativo=True).values('codigo_iso', 'nome', 'latitude', 'longitude')
    
    contexto = {
        'formulario': formulario,
        'paises': list(paises),
        'titulo': _('Criar Plano de Viagem')
    }
    
    return render(request, 'destinos/criar_plano.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_buscar_viajantes(request):
    """
    View para buscar viajantes com destinos similares.
    Implementa filtros avançados e paginação.
    """
    formulario = FormularioBuscaViajantes(request.GET)
    
    # Query base - apenas planos públicos e de outros usuários
    queryset_planos = PlanoViagem.objects.filter(
        ativo=True,
        viagem_concluida=False
    ).exclude(
        usuario=request.user
    ).select_related('pais_destino', 'usuario')
    
    # Aplicar filtros
    if formulario.is_valid():
        dados_limpos = formulario.cleaned_data
        
        # Filtro por país
        if dados_limpos.get('pais_destino'):
            queryset_planos = queryset_planos.filter(pais_destino=dados_limpos['pais_destino'])
        
        # Filtro por período
        if dados_limpos.get('data_inicio'):
            # Buscar viagens que se sobrepõem ao período especificado
            data_inicio = dados_limpos['data_inicio']
            data_fim = dados_limpos.get('data_fim', data_inicio + timedelta(days=30))
            
            queryset_planos = queryset_planos.filter(
                Q(data_inicio__lte=data_fim) & Q(data_fim__gte=data_inicio)
            )
        
        # Filtro por motivo
        if dados_limpos.get('motivo_viagem'):
            queryset_planos = queryset_planos.filter(motivo_viagem=dados_limpos['motivo_viagem'])
        
        # Filtro por duração
        if dados_limpos.get('duracao_minima'):
            # Filtrar por duração (calculada dinamicamente)
            from django.db.models import F, ExpressionWrapper, fields
            queryset_planos = queryset_planos.annotate(
                duracao=ExpressionWrapper(
                    F('data_fim') - F('data_inicio'),
                    output_field=fields.DurationField()
                )
            ).filter(duracao__gte=timedelta(days=dados_limpos['duracao_minima']))
    
    # Aplicar filtros de privacidade
    planos_filtrados = []
    for plano in queryset_planos:
        if plano.pode_ser_visto_por(request.user):
            planos_filtrados.append(plano)
    
    # Paginação
    paginador = Paginator(planos_filtrados, 12)
    numero_pagina = request.GET.get('page', 1)
    planos_paginados = paginador.get_page(numero_pagina)
    
    # Verificar amizades existentes
    amigos_ids = set()
    if request.user.is_authenticated:
        amizades = Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True
        )
        for amizade in amizades:
            if amizade.usuario1 == request.user:
                amigos_ids.add(amizade.usuario2.id)
            else:
                amigos_ids.add(amizade.usuario1.id)
    
    # Obter planos do usuário atual
    meus_planos = PlanoViagem.objects.filter(
        usuario=request.user,
        ativo=True
    ).select_related('pais_destino')
    
    contexto = {
        'formulario': formulario,
        'planos': planos_paginados,
        'meus_planos': meus_planos,
        'amigos_ids': amigos_ids,
        'total_resultados': len(planos_filtrados),
        'titulo': _('Buscar Viajantes')
    }
    
    return render(request, 'destinos/buscar.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_detalhes_plano(request, uuid):
    """View para visualizar detalhes de um plano de viagem."""
    plano = get_object_or_404(PlanoViagem, uuid=uuid)
    
    # Verificar permissão de visualização
    if not plano.pode_ser_visto_por(request.user):
        messages.error(request, _('Você não tem permissão para visualizar este plano.'))
        return redirect('destinos:buscar')
    
    # Verificar se são amigos
    sao_amigos = Amizade.sao_amigos(request.user, plano.usuario)
    
    # Verificar se há solicitação pendente
    from apps.conexoes.models import SolicitacaoAmizade
    solicitacao_pendente = SolicitacaoAmizade.objects.filter(
        Q(remetente=request.user, destinatario=plano.usuario) |
        Q(remetente=plano.usuario, destinatario=request.user),
        status='pendente'
    ).exists()
    
    contexto = {
        'plano': plano,
        'sao_amigos': sao_amigos,
        'solicitacao_pendente': solicitacao_pendente,
        'titulo': f'{plano.pais_destino.nome} - {plano.usuario.get_nome_exibicao()}'
    }
    
    return render(request, 'destinos/detalhes_plano.html', contexto)


@login_required
@require_http_methods(["GET"])
def api_paises_autocomplete(request):
    """
    API para autocomplete de países.
    Retorna lista de países que correspondem ao termo de busca.
    """
    termo = request.GET.get('q', '').strip()
    
    if len(termo) < 2:
        return JsonResponse({'resultados': []})
    
    try:
        paises = Pais.objects.filter(
            Q(nome__icontains=termo) | Q(nome_completo__icontains=termo),
            ativo=True
        ).values('id', 'nome', 'codigo_iso', 'latitude', 'longitude')[:10]
        
        return JsonResponse({
            'resultados': list(paises)
        })
    
    except Exception as erro:
        logger.error(f'Erro na API de autocomplete: {str(erro)}')
        return JsonResponse({'erro': 'Erro ao buscar países'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_estatisticas_destino(request, pais_id):
    """
    API para obter estatísticas de um destino.
    Retorna número de viajantes, período mais popular, etc.
    """
    try:
        pais = get_object_or_404(Pais, id=pais_id)
        
        planos = PlanoViagem.objects.filter(
            pais_destino=pais,
            ativo=True,
            viagem_concluida=False
        )
        
        total_viajantes = planos.count()
        
        # Período mais popular
        from django.db.models import Count
        periodos = planos.extra(
            select={'mes': 'EXTRACT(month FROM data_inicio)'}
        ).values('mes').annotate(total=Count('id')).order_by('-total')
        
        mes_popular = periodos.first()['mes'] if periodos else None
        
        # Motivo mais comum
        motivos = planos.values('motivo_viagem').annotate(
            total=Count('id')
        ).order_by('-total')
        
        motivo_popular = motivos.first()['motivo_viagem'] if motivos else None
        
        estatisticas = {
            'total_viajantes': total_viajantes,
            'mes_popular': mes_popular,
            'motivo_popular': motivo_popular,
            'nome_pais': pais.nome
        }
        
        return JsonResponse(estatisticas)
    
    except Exception as erro:
        logger.error(f'Erro ao obter estatísticas: {str(erro)}')
        return JsonResponse({'erro': 'Erro ao obter estatísticas'}, status=500)