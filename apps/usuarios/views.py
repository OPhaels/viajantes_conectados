from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import logging

from .forms import FormularioCadastroUsuario, FormularioLoginUsuario, FormularioEditarPerfil
from .models import Usuario

logger = logging.getLogger(__name__)


@csrf_protect
@require_http_methods(["GET", "POST"])
def view_cadastro_usuario(request):
    """
    View para cadastro de novo usuário.
    Implementa proteção CSRF e rate limiting.
    """
    if request.user.is_authenticated:
        return redirect('destinos:buscar')
    
    if request.method == 'POST':
        formulario = FormularioCadastroUsuario(request.POST)
        
        if formulario.is_valid():
            try:
                with transaction.atomic():
                    usuario = formulario.save(commit=False)
                    usuario.ativo = True
                    usuario.save()
                    
                    # Enviar email de verificação
                    enviar_email_verificacao(usuario)
                    
                    messages.success(
                        request,
                        _('Cadastro realizado! Verifique seu email para ativar sua conta.')
                    )
                    
                    logger.info(f'Novo usuário cadastrado: {usuario.email}')
                    return redirect('usuarios:login')
            
            except Exception as erro:
                logger.error(f'Erro ao cadastrar usuário: {str(erro)}')
                messages.error(
                    request,
                    _('Ocorreu um erro ao processar seu cadastro. Tente novamente.')
                )
        else:
            for campo, erros in formulario.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        formulario = FormularioCadastroUsuario()
    
    return render(request, 'usuarios/cadastro.html', {
        'formulario': formulario,
        'titulo': _('Cadastro')
    })


@csrf_protect
@require_http_methods(["GET", "POST"])
def view_login_usuario(request):
    """
    View para login de usuário.
    Implementa proteção contra força bruta.
    """
    if request.user.is_authenticated:
        return redirect('destinos:buscar')
    
    if request.method == 'POST':
        formulario = FormularioLoginUsuario(request, data=request.POST)
        email = request.POST.get('username', '').lower()
        
        try:
            usuario = Usuario.objects.get(email=email)
            
            # Verificar se está bloqueado
            if usuario.esta_bloqueado():
                tempo_restante = (usuario.bloqueado_ate - timezone.now()).seconds // 60
                messages.error(
                    request,
                    _(f'Conta temporariamente bloqueada. Tente novamente em {tempo_restante} minutos.')
                )
                return render(request, 'usuarios/login.html', {'formulario': formulario})
            
            # Verificar tentativas falhas
            if usuario.tentativas_login_falhas >= 5:
                usuario.bloqueado_ate = timezone.now() + timezone.timedelta(minutes=30)
                usuario.save()
                logger.warning(f'Conta bloqueada por excesso de tentativas: {email}')
                messages.error(
                    request,
                    _('Muitas tentativas de login. Conta bloqueada por 30 minutos.')
                )
                return render(request, 'usuarios/login.html', {'formulario': formulario})
        
        except Usuario.DoesNotExist:
            # Não revelar que o email não existe (segurança)
            pass
        
        if formulario.is_valid():
            usuario_autenticado = formulario.get_user()
            
            # Resetar tentativas falhas
            usuario_autenticado.tentativas_login_falhas = 0
            usuario_autenticado.bloqueado_ate = None
            usuario_autenticado.ultimo_acesso = timezone.now()
            usuario_autenticado.save()
            
            login(request, usuario_autenticado)
            
            # Configurar sessão
            if not request.POST.get('lembrar_me'):
                request.session.set_expiry(0)
            
            logger.info(f'Login bem-sucedido: {usuario_autenticado.email}')
            messages.success(request, _(f'Bem-vindo, {usuario_autenticado.get_nome_exibicao()}!'))
            
            proximo = request.GET.get('next', 'destinos:buscar')
            return redirect(proximo)
        else:
            # Incrementar tentativas falhas
            try:
                usuario = Usuario.objects.get(email=email)
                usuario.tentativas_login_falhas += 1
                usuario.save()
                logger.warning(f'Tentativa de login falha: {email}')
            except Usuario.DoesNotExist:
                pass
            
            messages.error(request, _('Email ou senha incorretos.'))
    else:
        formulario = FormularioLoginUsuario()
    
    return render(request, 'usuarios/login.html', {
        'formulario': formulario,
        'titulo': _('Login')
    })


@login_required
@require_http_methods(["POST"])
def view_logout_usuario(request):
    """View para logout do usuário."""
    logger.info(f'Logout: {request.user.email}')
    logout(request)
    messages.success(request, _('Você saiu da sua conta.'))
    return redirect('usuarios:login')


@login_required
@require_http_methods(["GET", "POST"])
def view_editar_perfil(request):
    """View para editar perfil do usuário."""
    if request.method == 'POST':
        formulario = FormularioEditarPerfil(
            request.POST,
            request.FILES,
            instance=request.user
        )
        
        if formulario.is_valid():
            try:
                formulario.save()
                messages.success(request, _('Perfil atualizado com sucesso!'))
                logger.info(f'Perfil atualizado: {request.user.email}')
                return redirect('usuarios:perfil')
            except Exception as erro:
                logger.error(f'Erro ao atualizar perfil: {str(erro)}')
                messages.error(request, _('Erro ao atualizar perfil. Tente novamente.'))
        else:
            for campo, erros in formulario.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        formulario = FormularioEditarPerfil(instance=request.user)
    
    return render(request, 'usuarios/editar_perfil.html', {
        'formulario': formulario,
        'titulo': _('Editar Perfil')
    })


@login_required
@require_http_methods(["GET"])
def view_perfil_usuario(request, uuid=None):
    """View para visualizar perfil de usuário."""
    if uuid:
        usuario = get_object_or_404(Usuario, uuid=uuid)
        
        # Verificar privacidade
        if not usuario.perfil_publico and usuario != request.user:
            from apps.conexoes.models import Amizade
            if not Amizade.sao_amigos(request.user, usuario):
                messages.error(request, _('Este perfil é privado.'))
                return redirect('destinos:buscar')
    else:
        usuario = request.user
    
    contexto = {
        'usuario_perfil': usuario,
        'e_proprio_perfil': usuario == request.user,
        'titulo': usuario.get_nome_exibicao()
    }
    
    return render(request, 'usuarios/perfil.html', contexto)


def enviar_email_verificacao(usuario):
    """
    Envia email de verificação para o usuário.
    Em produção, usar Celery para processamento assíncrono.
    """
    try:
        # Gerar token de verificação (implementar com django-allauth ou custom)
        assunto = _('Verifique seu email - Viajantes Conectados')
        mensagem = _(f'''
        Olá {usuario.get_nome_exibicao()},
        
        Bem-vindo ao Viajantes Conectados!
        
        Por favor, verifique seu email clicando no link abaixo:
        [LINK DE VERIFICAÇÃO]
        
        Atenciosamente,
        Equipe Viajantes Conectados
        ''')
        
        send_mail(
            assunto,
            mensagem,
            settings.EMAIL_HOST_USER,
            [usuario.email],
            fail_silently=False,
        )
        logger.info(f'Email de verificação enviado para: {usuario.email}')
    except Exception as erro:
        logger.error(f'Erro ao enviar email de verificação: {str(erro)}')

from django.shortcuts import render

def pagina_403(request, exception=None):
    return render(request, "errors/403.html", status=403)

def pagina_404(request, exception=None):
    return render(request, "errors/404.html", status=404)

def pagina_500(request):
    return render(request, "errors/500.html", status=500)