from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Usuario
import re


class FormularioCadastroUsuario(UserCreationForm):
    """Formulário de cadastro com validações de segurança."""
    
    nome_completo = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo'
        }),
        label=_('Nome Completo')
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        label=_('Email')
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha forte'
        }),
        label=_('Senha')
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        }),
        label=_('Confirmar Senha')
    )
    aceita_termos = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Aceito os termos de uso e política de privacidade')
    )
    
    class Meta:
        model = Usuario
        fields = ('nome_completo', 'email', 'password1', 'password2', 'aceita_termos')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
    
    def clean_email(self):
        """Valida se o email já está cadastrado."""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError(
                _('Este email já está cadastrado. Tente fazer login ou recuperar sua senha.')
            )
        return email.lower()
    
    def clean_nome_completo(self):
        """Valida o nome completo."""
        nome = self.cleaned_data.get('nome_completo')
        if len(nome.split()) < 2:
            raise ValidationError(_('Por favor, forneça seu nome completo.'))
        
        # Verifica caracteres especiais suspeitos
        if re.search(r'[<>{}[\]\\]', nome):
            raise ValidationError(_('Nome contém caracteres inválidos.'))
        
        return nome.strip()
    
    def clean_password1(self):
        """Validações adicionais de senha."""
        password = self.cleaned_data.get('password1')
        
        # Verifica complexidade
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('A senha deve conter pelo menos uma letra maiúscula.'))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('A senha deve conter pelo menos uma letra minúscula.'))
        
        if not re.search(r'[0-9]', password):
            raise ValidationError(_('A senha deve conter pelo menos um número.'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('A senha deve conter pelo menos um caractere especial.'))
        
        return password


class FormularioLoginUsuario(AuthenticationForm):
    """Formulário de login customizado."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com',
            'autofocus': True
        }),
        label=_('Email')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        }),
        label=_('Senha')
    )
    lembrar_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Lembrar-me')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


class FormularioEditarPerfil(forms.ModelForm):
    """Formulário para editar perfil do usuário."""
    
    class Meta:
        model = Usuario
        fields = [
            'nome_completo', 'data_nascimento', 'telefone',
            'pais_residencia', 'cidade_residencia', 'biografia',
            'foto_perfil', 'perfil_publico', 'mostrar_email', 'mostrar_telefone'
        ]
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'pais_residencia': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade_residencia': forms.TextInput(attrs={'class': 'form-control'}),
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_foto_perfil(self):
        """Valida o upload da foto."""
        foto = self.cleaned_data.get('foto_perfil')
        if foto:
            if foto.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError(_('A imagem não pode exceder 5MB.'))
            
            if not foto.content_type in ['image/jpeg', 'image/png', 'image/webp']:
                raise ValidationError(_('Formato de imagem não suportado. Use JPEG, PNG ou WebP.'))
        
        return foto
