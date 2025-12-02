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

from django.db import transaction
from django.conf import settings
from .forms import FormularioPlanoViagem, FormularioBuscaViajantes
from .models import PlanoViagem, Pais, EnderecoPlano
from apps.usuarios.models import Usuario
from apps.conexoes.models import Amizade

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET", "POST"])
def view_criar_plano_viagem(request):
    """
    View para criar plano de viagem com país automático.
    Não precisa passar lista de países - tudo é criado dinamicamente!
    """
    if request.method == 'POST':
        # Extrai dados de localização do formulário
        pais_nome = request.POST.get('pais_nome', '').strip()
        pais_codigo_iso = request.POST.get('pais_codigo_iso', '').strip()
        cidade = request.POST.get('cidade_destino', '').strip()
        regiao = request.POST.get('regiao_destino', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        
        # Valida se o usuário selecionou uma localização
        if not pais_nome:
            messages.error(request, 'Por favor, selecione uma localização no mapa.')
            form = FormularioPlanoViagem(request.POST)
            context = {
                'titulo': 'Criar Plano de Viagem',
                'formulario': form,
                'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
            }
            return render(request, 'destinos/criar_plano.html', context)
        
        try:
            with transaction.atomic():
                # 1. Busca ou cria o país automaticamente
                pais = None
                
                if pais_codigo_iso:
                    # Tenta buscar por código ISO primeiro
                    pais = Pais.objects.filter(
                        codigo_iso__iexact=pais_codigo_iso
                    ).first()
                
                if not pais:
                    # Tenta buscar por nome
                    pais = Pais.objects.filter(
                        nome__iexact=pais_nome
                    ).first()
                
                if not pais:
                    # Cria o país automaticamente
                    logger.info(f"Criando novo país: {pais_nome} ({pais_codigo_iso})")
                    
                    # Define coordenadas padrão ou usa as fornecidas
                    lat = float(latitude) if latitude else 0.0
                    lng = float(longitude) if longitude else 0.0
                    
                    pais = Pais.objects.create(
                        codigo_iso=pais_codigo_iso or 'XX',  # Código genérico se não tiver
                        nome=pais_nome,
                        nome_completo=pais_nome,
                        continente='Não especificado',  # Pode ser melhorado depois
                        latitude=lat,
                        longitude=lng,
                        ativo=True
                    )
                    
                    messages.success(
                        request, 
                        f'País "{pais_nome}" adicionado automaticamente ao sistema!'
                    )
                
                # 2. Cria uma cópia mutável do POST para adicionar o país
                dados_post = request.POST.copy()
                dados_post['pais_destino'] = pais.id  # Adiciona o ID do país ao formulário
                dados_post['cidade_destino'] = cidade
                dados_post['regiao_destino'] = regiao
                
                # Processa o formulário com o país já preenchido
                form = FormularioPlanoViagem(dados_post)
                
                if form.is_valid():
                    plano = form.save(commit=False)
                    plano.usuario = request.user
                    plano.save()
                    
                    # 3. Salva endereço completo com coordenadas (opcional)
                    if latitude and longitude:
                        EnderecoPlano.objects.create(
                            plano=plano,
                            cidade=cidade,
                            estado=regiao,
                            pais_texto=pais_nome,
                            latitude=float(latitude),
                            longitude=float(longitude)
                        )
                    
                    messages.success(
                        request, 
                        f'Plano de viagem para {pais_nome} criado com sucesso!'
                    )
                    return redirect('destinos:detalhes_plano', uuid=plano.uuid)
                else:
                    messages.error(request, 'Corrija os erros no formulário.')
                    logger.error(f"Erros no formulário: {form.errors}")
                    # Renderiza novamente com os erros
                    context = {
                        'titulo': 'Criar Plano de Viagem',
                        'formulario': form,
                        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
                    }
                    return render(request, 'destinos/criar_plano.html', context)
        
        except Exception as e:
            logger.error(f"Erro ao criar plano de viagem: {e}", exc_info=True)
            messages.error(
                request, 
                'Erro ao salvar o plano de viagem. Tente novamente.'
            )
            # Recria o formulário com os dados enviados
            form = FormularioPlanoViagem(request.POST)
            context = {
                'titulo': 'Criar Plano de Viagem',
                'formulario': form,
                'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
            }
            return render(request, 'destinos/criar_plano.html', context)
    
    else:
        form = FormularioPlanoViagem()
    
    context = {
        'titulo': 'Criar Plano de Viagem',
        'formulario': form,
        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
    }
    
    return render(request, 'destinos/criar_plano.html', context)

@login_required
@require_http_methods(["GET"])
def view_buscar_viajantes(request):
    formulario = FormularioBuscaViajantes(request.GET)

    # Query base — sem o campo INVALIDO "endereco_plano"
    queryset_destinos = (
        PlanoViagem.objects
        .filter(
            ativo=True,
            viagem_concluida=False
        )
        .exclude(usuario=request.user)
        .select_related('pais_destino', 'usuario')  # <- CORRETO
    )

    # Aplicar filtros
    if formulario.is_valid():
        dados = formulario.cleaned_data

        # País
        if dados.get('pais_destino'):
            queryset_destinos = queryset_destinos.filter(
                pais_destino=dados['pais_destino']
            )

        # Período
        if dados.get('data_inicio'):
            data_inicio = dados['data_inicio']
            data_fim = dados.get('data_fim') or data_inicio + timedelta(days=30)

            queryset_destinos = queryset_destinos.filter(
                Q(data_inicio__lte=data_fim) &
                Q(data_fim__gte=data_inicio)
            )

        # Motivo
        if dados.get('motivo_viagem'):
            queryset_destinos = queryset_destinos.filter(
                motivo_viagem=dados['motivo_viagem']
            )

        # Duração mínima
        if dados.get('duracao_minima'):
            from django.db.models import F, ExpressionWrapper, DurationField
            queryset_destinos = queryset_destinos.annotate(
                duracao=ExpressionWrapper(
                    F('data_fim') - F('data_inicio'),
                    output_field=DurationField()
                )
            ).filter(duracao__gte=timedelta(days=dados['duracao_minima']))

    # Filtro de privacidade
    destinos_filtrados = [
        plano for plano in queryset_destinos
        if plano.pode_ser_visto_por(request.user)
    ]

    # Paginação
    paginador = Paginator(destinos_filtrados, 12)
    destinos_paginados = paginador.get_page(request.GET.get('page', 1))

    # Amizades
    amigos_ids = set()
    if request.user.is_authenticated:
        amizades = Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True
        )
        for a in amizades:
            amigos_ids.add(a.usuario2.id if a.usuario1 == request.user else a.usuario1.id)

    # Meus destinos
    meus_destinos = (
        PlanoViagem.objects
        .filter(usuario=request.user, ativo=True)
        .select_related('pais_destino')
    )

    contexto = {
        'formulario': formulario,
        'destinos': destinos_paginados,
        'meus_destinos': meus_destinos,
        'amigos_ids': amigos_ids,
        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
        'total_resultados': len(destinos_filtrados),
        'title': _('Buscar Viajantes'), 
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
        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
        'titulo': f'{plano.pais_destino.nome} - {plano.usuario.get_nome_exibicao()}'
    }
    
    return render(request, 'destinos/detalhes_plano.html', contexto)


@login_required
@require_http_methods(["GET"])
def api_paises_autocomplete(request):
    """
    API para autocomplete de países.
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
        
        destinos = PlanoViagem.objects.filter(
            pais_destino=pais,
            ativo=True,
            viagem_concluida=False
        )
        
        total_viajantes = destinos.count()
        
        # Período mais popular
        from django.db.models import Count
        periodos = destinos.extra(
            select={'mes': 'EXTRACT(month FROM data_inicio)'}
        ).values('mes').annotate(total=Count('id')).order_by('-total')
        
        mes_popular = periodos.first()['mes'] if periodos else None
        
        # Motivo mais comum
        motivos = destinos.values('motivo_viagem').annotate(
            total=Count('id')
        ).order_by('-total')
        
        motivo_popular = motivos.first()['motivo_viagem'] if motivos else None
        
        estatisticas = {
            'total_viajantes': total_viajantes,
            'mes_popular': mes_popular,
            'motivo_popular': motivo_popular,
            'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
            'nome_pais': pais.nome
        }
        
        return JsonResponse(estatisticas)
    
    except Exception as erro:
        logger.error(f'Erro ao obter estatísticas: {str(erro)}')
        return JsonResponse({'erro': 'Erro ao obter estatísticas'}, status=500)