"""
Modelos para auditoria e logging de ações sensíveis.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class LogAuditoria(models.Model):
    """
    Registro de auditoria para ações sensíveis em toda a plataforma.
    Rastreia quem fez o quê, quando e de onde.
    """
    
    # Tipos de ações possíveis
    TIPO_ACAO_CHOICES = [
        ('login_sucesso', _('Login bem-sucedido')),
        ('login_falha', _('Falha no login')),
        ('registro_novo_usuario', _('Novo usuário registrado')),
        ('deletar_usuario', _('Usuário deletado')),
        ('verificar_email', _('Email verificado')),
        ('alterar_senha', _('Senha alterada')),
        ('alterar_perfil', _('Perfil alterado')),
        ('criar_plano_viagem', _('Plano de viagem criado')),
        ('deletar_plano_viagem', _('Plano de viagem deletado')),
        ('solicitacao_amizade_enviada', _('Solicitação de amizade enviada')),
        ('amizade_aceita', _('Amizade aceita')),
        ('amizade_rejeitada', _('Amizade rejeitada')),
        ('enviar_mensagem', _('Mensagem enviada')),
        ('deletar_mensagem', _('Mensagem deletada')),
        ('acesso_negado_permissao', _('Acesso negado - permissão')),
        ('acesso_negado_autenticacao', _('Acesso negado - não autenticado')),
        ('acesso_recurso_sensivel', _('Acesso a recurso sensível')),
        ('alteracao_configuracoes', _('Configurações do sistema alteradas')),
        ('erro_aplicacao', _('Erro na aplicação')),
        ('atividade_suspeita', _('Atividade suspeita')),
    ]
    
    # Campos principais
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Ação e contexto
    tipo_acao = models.CharField(
        _('tipo de ação'),
        max_length=50,
        choices=TIPO_ACAO_CHOICES,
        db_index=True
    )
    descricao = models.TextField(_('descrição'), blank=True)
    
    # Usuário envolvido
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('usuário'),
        related_name='logs_auditoria'
    )
    usuario_email = models.EmailField(_('email do usuário'), db_index=True)
    
    # Informações da requisição
    ip_address = models.GenericIPAddressField(
        _('endereço IP'),
        db_index=True
    )
    user_agent = models.CharField(_('user agent'), max_length=500, blank=True)
    
    # Resultado e detalhes
    resultado = models.BooleanField(
        _('sucesso'),
        default=True,
        db_index=True
    )
    detalhes_erro = models.TextField(_('detalhes do erro'), blank=True)
    
    # Método HTTP e endpoint
    metodo_http = models.CharField(
        _('método HTTP'),
        max_length=10,
        choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), 
                ('PATCH', 'PATCH'), ('DELETE', 'DELETE')],
        blank=True
    )
    endpoint = models.CharField(_('endpoint'), max_length=500, blank=True)
    codigo_resposta = models.IntegerField(_('código HTTP'), null=True, blank=True)
    
    # Dados adicionais
    dados_alterados = models.JSONField(
        _('dados alterados'),
        default=dict,
        blank=True,
        help_text=_('JSON com campos que foram modificados')
    )
    
    # Flags
    requer_investigacao = models.BooleanField(
        _('requer investigação'),
        default=False,
        db_index=True,
        help_text=_('Flag para ações que podem indicar fraude ou abuso')
    )
    
    class Meta:
        verbose_name = _('log de auditoria')
        verbose_name_plural = _('logs de auditoria')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['usuario_email', '-timestamp']),
            models.Index(fields=['tipo_acao', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['requer_investigacao', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.get_tipo_acao_display()} - {self.usuario_email} - {self.timestamp}'
    
    @classmethod
    def registrar_acao(cls, tipo_acao, usuario, request, 
                      resultado=True, descricao='', detalhes_erro='', 
                      dados_alterados=None, requer_investigacao=False):
        """
        Método auxiliar para registrar uma ação de forma fácil.
        
        Args:
            tipo_acao: Tipo da ação (como em TIPO_ACAO_CHOICES)
            usuario: Objeto Usuario (pode ser None para não autenticados)
            request: Objeto da requisição Django
            resultado: bool indicando sucesso/falha
            descricao: Descrição legível da ação
            detalhes_erro: Detalhes do erro se houver
            dados_alterados: Dict com dados que foram modificados
            requer_investigacao: bool indicando se precisa investigação
        """
        from apps.core.throttles import obter_ip_cliente
        
        return cls.objects.create(
            tipo_acao=tipo_acao,
            usuario=usuario,
            usuario_email=usuario.email if usuario else 'anonimo@desconhecido.local',
            ip_address=obter_ip_cliente(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            resultado=resultado,
            descricao=descricao,
            detalhes_erro=detalhes_erro,
            metodo_http=request.method,
            endpoint=request.path,
            dados_alterados=dados_alterados or {},
            requer_investigacao=requer_investigacao,
        )


class TentativaLoginFalhado(models.Model):
    """
    Rastreia tentativas de login falhadas para detecção de ataques de força bruta.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Login attempt info
    email_tentativa = models.EmailField(_('email da tentativa'), db_index=True)
    ip_address = models.GenericIPAddressField(_('endereço IP'), db_index=True)
    user_agent = models.CharField(_('user agent'), max_length=500, blank=True)
    
    # Motivo da falha
    motivo = models.CharField(
        _('motivo da falha'),
        max_length=100,
        choices=[
            ('usuario_nao_existe', _('Usuário não existe')),
            ('senha_incorreta', _('Senha incorreta')),
            ('email_nao_verificado', _('Email não verificado')),
            ('usuario_bloqueado', _('Usuário bloqueado')),
            ('usuario_inativo', _('Usuário inativo')),
            ('outro', _('Outro')),
        ]
    )
    
    # Identificação de usuário se existir
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('usuário'),
        related_name='tentativas_login_falhado'
    )
    
    class Meta:
        verbose_name = _('tentativa de login falhado')
        verbose_name_plural = _('tentativas de login falhado')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['email_tentativa', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.email_tentativa} - {self.get_motivo_display()} - {self.timestamp}'
    
    @classmethod
    def registrar_tentativa(cls, email, request, motivo, usuario=None):
        """Registra uma tentativa de login falhada."""
        from apps.core.throttles import obter_ip_cliente
        
        return cls.objects.create(
            email_tentativa=email,
            ip_address=obter_ip_cliente(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            motivo=motivo,
            usuario=usuario,
        )
    
    @classmethod
    def contar_tentativas_recentes(cls, email_ou_ip, minutos=60):
        """
        Conta tentativas recentes de uma entidade (email ou IP).
        
        Args:
            email_ou_ip: Email ou IP para buscar
            minutos: Quantos minutos para voltar
        
        Returns:
            int: Número de tentativas
        """
        from django.utils import timezone
        from datetime import timedelta
        
        tempo_limite = timezone.now() - timedelta(minutes=minutos)
        
        # Se é um email
        if '@' in str(email_ou_ip):
            return cls.objects.filter(
                email_tentativa=email_ou_ip,
                timestamp__gte=tempo_limite
            ).count()
        
        # Se é um IP
        return cls.objects.filter(
            ip_address=email_ou_ip,
            timestamp__gte=tempo_limite
        ).count()
