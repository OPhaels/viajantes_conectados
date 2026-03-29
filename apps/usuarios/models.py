from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class GerenciadorUsuarioCustomizado(BaseUserManager):
    """Gerenciador customizado para criação de usuários com email como identificador."""
    
    def create_user(self, email, password=None, **campos_extras):
        """Cria e salva um usuário com email e senha."""
        if not email:
            raise ValueError(_('O endereço de email deve ser fornecido'))
        
        email = self.normalize_email(email)
        usuario = self.model(email=email, **campos_extras)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario
    
    def create_superuser(self, email, password=None, **campos_extras):
        """Cria e salva um superusuário."""
        campos_extras.setdefault('is_staff', True)
        campos_extras.setdefault('is_superuser', True)
        campos_extras.setdefault('email_verificado', True)
        
        if campos_extras.get('is_staff') is not True:
            raise ValueError(_('Superusuário deve ter is_staff=True'))
        if campos_extras.get('is_superuser') is not True:
            raise ValueError(_('Superusuário deve ter is_superuser=True'))
        
        return self.create_user(email, password, **campos_extras)


class Usuario(AbstractUser):
    """
    Modelo de usuário customizado com segurança aprimorada.
    Utiliza email como identificador único e hash de senha com Argon2.
    """
    
    # Removendo campo username padrão
    username = None
    
    # UUID para identificação pública
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('UUID')
    )
    
    # Informações de Autenticação
    email = models.EmailField(
        _('email'),
        unique=True,
        error_messages={
            'unique': _('Um usuário com este email já existe.'),
        }
    )
    email_verificado = models.BooleanField(
        _('email verificado'),
        default=False,
        help_text=_('Indica se o email foi verificado.')
    )
    
    # Informações Pessoais
    nome_completo = models.CharField(
        _('nome completo'),
        max_length=150,
        validators=[MinLengthValidator(3)]
    )
    data_nascimento = models.DateField(
        _('data de nascimento'),
        null=True,
        blank=True
    )
    
    # Contato
    telefone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Telefone deve estar no formato: "+999999999". Até 15 dígitos permitidos.')
    )
    telefone = models.CharField(
        _('telefone'),
        validators=[telefone_regex],
        max_length=17,
        blank=True
    )
    
    # Localização
    pais_residencia = models.CharField(
        _('país de residência'),
        max_length=100,
        blank=True
    )
    cidade_residencia = models.CharField(
        _('cidade de residência'),
        max_length=100,
        blank=True
    )
    
    # Perfil
    biografia = models.TextField(
        _('biografia'),
        max_length=500,
        blank=True,
        help_text=_('Máximo de 500 caracteres.')
    )
    foto_perfil = models.ImageField(
        _('foto de perfil'),
        upload_to='fotos_perfil/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Preferências de Privacidade
    perfil_publico = models.BooleanField(
        _('perfil público'),
        default=True,
        help_text=_('Permite que outros usuários vejam seu perfil.')
    )
    mostrar_email = models.BooleanField(
        _('mostrar email'),
        default=False,
        help_text=_('Permite que amigos vejam seu email.')
    )
    mostrar_telefone = models.BooleanField(
        _('mostrar telefone'),
        default=False,
        help_text=_('Permite que amigos vejam seu telefone.')
    )
    
    # Controle de Conta
    ativo = models.BooleanField(_('ativo'), default=True)
    data_criacao = models.DateTimeField(_('data de criação'), auto_now_add=True)
    data_atualizacao = models.DateTimeField(_('data de atualização'), auto_now=True)
    ultimo_acesso = models.DateTimeField(_('último acesso'), null=True, blank=True)
    
    # Segurança
    tentativas_login_falhas = models.IntegerField(
        _('tentativas de login falhas'),
        default=0
    )
    bloqueado_ate = models.DateTimeField(
        _('bloqueado até'),
        null=True,
        blank=True
    )
    
    objects = GerenciadorUsuarioCustomizado()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo']
    
    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['uuid']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_nome_exibicao(self):
        """Retorna o nome para exibição pública."""
        if self.nome_completo and self.nome_completo.strip():
            first_name = self.nome_completo.strip().split()[0]
            if first_name:
                return first_name
        return self.email.split('@')[0] if self.email else "Viajante"
    
    def esta_bloqueado(self):
        """Verifica se a conta está temporariamente bloqueada."""
        if self.bloqueado_ate and self.bloqueado_ate > timezone.now():
            return True
        return False
    
    def pode_enviar_solicitacao_amizade(self):
        """Verifica se o usuário pode enviar solicitações de amizade."""
        return self.email_verificado and self.ativo