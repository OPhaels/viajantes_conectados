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
@require_http_methods(["GET", "POST"])
def view_editar_plano(request, uuid):
    """View para editar um plano de viagem existente."""
    plano = get_object_or_404(PlanoViagem, uuid=uuid)

    if plano.usuario != request.user:
        messages.error(request, _('Você não pode editar este plano.'))
        return redirect('destinos:meus_planos')

    if request.method == 'POST':
        pais_nome = request.POST.get('pais_nome', '').strip()
        pais_codigo_iso = request.POST.get('pais_codigo_iso', '').strip()
        cidade = request.POST.get('cidade_destino', '').strip()
        regiao = request.POST.get('regiao_destino', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()

        pais = plano.pais_destino

        if pais_nome:
            if pais_codigo_iso:
                pais = Pais.objects.filter(codigo_iso__iexact=pais_codigo_iso).first() or pais

            if not pais or pais.nome.lower() != pais_nome.lower():
                pais = Pais.objects.filter(nome__iexact=pais_nome).first() or pais

            if not pais:
                logger.info(f"Criando novo país para edição: {pais_nome} ({pais_codigo_iso})")
                lat = float(latitude) if latitude else 0.0
                lng = float(longitude) if longitude else 0.0
                pais = Pais.objects.create(
                    codigo_iso=pais_codigo_iso or 'XX',
                    nome=pais_nome,
                    nome_completo=pais_nome,
                    continente='Não especificado',
                    latitude=lat,
                    longitude=lng,
                    ativo=True
                )

        dados_post = request.POST.copy()
        dados_post['pais_destino'] = pais.id
        dados_post['cidade_destino'] = cidade
        dados_post['regiao_destino'] = regiao

        form = FormularioPlanoViagem(dados_post, instance=plano)

        if form.is_valid():
            plano = form.save(commit=False)
            plano.pais_destino = pais
            plano.save()

            if latitude and longitude:
                EnderecoPlano.objects.update_or_create(
                    plano=plano,
                    defaults={
                        'cidade': cidade,
                        'estado': regiao,
                        'pais_texto': pais_nome or plano.pais_destino.nome,
                        'latitude': float(latitude),
                        'longitude': float(longitude),
                    }
                )

            messages.success(request, _('Plano de viagem atualizado com sucesso!'))
            return redirect('destinos:detalhes_plano', uuid=plano.uuid)
        else:
            messages.error(request, _('Corrija os erros no formulário.'))
            logger.error(f"Erros no formulário de edição: {form.errors}")
    else:
        form = FormularioPlanoViagem(instance=plano)

    context = {
        'titulo': _('Editar Plano de Viagem'),
        'formulario': form,
        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
    }

    return render(request, 'destinos/criar_plano.html', context)


@login_required
@require_http_methods(["GET"])
def view_buscar_viajantes(request):
    """View para buscar viajantes que estão planejando viagens (excluindo o próprio usuário)."""
    formulario = FormularioBuscaViajantes(request.GET)

    queryset_destinos = (
        PlanoViagem.objects
        .filter(
            ativo=True,
            viagem_concluida=False
        )
        .exclude(usuario=request.user)
        .select_related('pais_destino', 'usuario')  
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
    amigos_uuids = set()
    if request.user.is_authenticated:
        amizades = Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True
        )
        for a in amizades:
            amigo = a.usuario2 if a.usuario1 == request.user else a.usuario1
            amigos_ids.add(amigo.id)
            amigos_uuids.add(amigo.uuid)

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
        'amigos_uuids': amigos_uuids,
        'MAPBOX_TOKEN': settings.MAPBOX_TOKEN,
        'total_resultados': len(destinos_filtrados),
        'title': _('Buscar Viagens'), 
    }

    return render(request, 'destinos/buscar.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_listar_viajantes(request):
    """View para listar viajantes (usuários que têm perfil público), excluindo o próprio usuário."""
    
    # Queryset base: usuários ativos, com perfil público, exceto o próprio
    queryset_viajantes = (
        Usuario.objects
        .filter(ativo=True, perfil_publico=True)
        .exclude(uuid=request.user.uuid)
    )
    
    # Filtros de busca
    busca = request.GET.get('q', '').strip()
    if busca:
        queryset_viajantes = queryset_viajantes.filter(
            Q(nome_completo__icontains=busca) |
            Q(pais_residencia__icontains=busca) |
            Q(cidade_residencia__icontains=busca)
        )
    
    pais = request.GET.get('pais', '').strip()
    if pais:
        queryset_viajantes = queryset_viajantes.filter(
            pais_residencia__icontains=pais
        )
    
    cidade = request.GET.get('cidade', '').strip()
    if cidade:
        queryset_viajantes = queryset_viajantes.filter(
            cidade_residencia__icontains=cidade
        )
    
    # Ordenação
    queryset_viajantes = queryset_viajantes.order_by('-data_criacao')
    
    # Paginação
    paginador = Paginator(queryset_viajantes, 12)
    viajantes_paginados = paginador.get_page(request.GET.get('page', 1))
    
    # Amizades
    amigos_ids = set()
    if request.user.is_authenticated:
        amizades = Amizade.objects.filter(
            Q(usuario1=request.user) | Q(usuario2=request.user),
            ativa=True
        )
        for a in amizades:
            amigos_ids.add(a.usuario2.id if a.usuario1 == request.user else a.usuario1.id)
    
    contexto = {
        'viajantes': viajantes_paginados,
        'page_obj': viajantes_paginados,
        'amigos_ids': amigos_ids,
        'total_viajantes': paginador.count,
        'titulo': _('Listar Viajantes'),
    }
    
    return render(request, 'destinos/buscar_viajantes.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_meus_planos(request):
    """View para listar os planos de viagem do usuário autenticado."""
    
    planos = PlanoViagem.objects.filter(
        usuario=request.user
    ).select_related('pais_destino').order_by('-data_inicio')
    
    # Paginação
    paginador = Paginator(planos, 12)
    planos_paginados = paginador.get_page(request.GET.get('page', 1))
    
    contexto = {
        'meus_planos': planos_paginados,
        'page_obj': planos_paginados,
        'titulo': _('Meus Planos de Viagem'),
    }
    
    return render(request, 'destinos/meus_planos.html', contexto)


@login_required
@require_http_methods(["GET"])
def view_detalhes_plano(request, uuid):
    """View para visualizar detalhes de um plano de viagem."""
    plano = get_object_or_404(PlanoViagem, uuid=uuid)
    
    # Verificar permissão de visualização
    if not plano.pode_ser_visto_por(request.user):
        messages.error(request, _('Você não tem permissão para visualizar este plano.'))
        return redirect('destinos:buscar_viajantes')
    
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
@require_http_methods(["POST"])
def view_deletar_plano(request, uuid):
    """View para deletar um plano de viagem (apenas o próprio)."""
    
    plano = get_object_or_404(PlanoViagem, uuid=uuid)
    
    # Verificar se é o proprietário
    if plano.usuario != request.user:
        messages.error(request, _('Você não pode deletar este plano.'))
        return redirect('destinos:meus_planos')
    
    try:
        plano_nome = f"{plano.pais_destino.nome} ({plano.data_inicio.strftime('%d/%m/%Y')})"
        plano.delete()
        messages.success(request, f'Plano de viagem "{plano_nome}" deletado com sucesso!')
        logger.info(f'Plano deletado por {request.user.email}: {plano_nome}')
    except Exception as e:
        logger.error(f"Erro ao deletar plano: {e}")
        messages.error(request, _('Erro ao deletar o plano. Tente novamente.'))
    
    return redirect('destinos:meus_planos')


@login_required
@require_http_methods(["GET"])
def api_paises_autocomplete(request):
    """
    ⚠️ API DESCONTINUADA - Use /api/paises/ com filtro 'search' em vez disso.
    
    Migração: GET /api/paises/?search=termo
    """
    return JsonResponse({
        'erro': 'Esta API foi descontinuada.',
        'mensagem': 'Use o novo endpoint: GET /destinos/api/paises/?search=<termo>',
        'novo_endpoint': '/destinos/api/paises/?search=',
        'codigo_migracao': 'Use DjangoFilterBackend com SearchFilter'
    }, status=410)  # 410 Gone


@login_required
@require_http_methods(["GET"])
def api_estatisticas_destino(request, pais_id):
    """
    ⚠️ API DESCONTINUADA - Use ViewSets de PlanoViagem para análises.
    
    Migração: GET /destinos/api/planos/?pais_destino=<id>
    """
    return JsonResponse({
        'erro': 'Esta API foi descontinuada.',
        'mensagem': 'Use o novo endpoint: GET /destinos/api/planos/?pais_destino=<id>',
        'novo_endpoint': '/destinos/api/planos/?pais_destino=',
        'nota_segurança': 'Dados agregados agora requerem permissões apropriadas'
    }, status=410)  # 410 Gone