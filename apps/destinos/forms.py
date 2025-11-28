from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import PlanoViagem, Pais


class FormularioPlanoViagem(forms.ModelForm):
    """Formulário para criar/editar planos de viagem."""
    
    class Meta:
        model = PlanoViagem
        fields = [
            'pais_destino', 'cidade_destino', 'regiao_destino',
            'data_inicio', 'data_fim', 'flexibilidade_datas',
            'motivo_viagem', 'descricao', 'nivel_privacidade',
            'orcamento_diario_min', 'orcamento_diario_max'
        ]
        widgets = {
            'pais_destino': forms.Select(attrs={
                'class': 'form-control form-control-custom',
                'required': True
            }),
            'cidade_destino': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': 'Ex: Paris'
            }),
            'regiao_destino': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': 'Ex: Île-de-France'
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control form-control-custom',
                'type': 'date'
            }),
            'data_fim': forms.DateInput(attrs={
                'class': 'form-control form-control-custom',
                'type': 'date'
            }),
            'flexibilidade_datas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'motivo_viagem': forms.Select(attrs={
                'class': 'form-control form-control-custom'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-control-custom',
                'rows': 4,
                'placeholder': 'Descreva seus planos e interesses...'
            }),
            'nivel_privacidade': forms.Select(attrs={
                'class': 'form-control form-control-custom'
            }),
            'orcamento_diario_min': forms.NumberInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'orcamento_diario_max': forms.NumberInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        
        # Carregar apenas países ativos
        self.fields['pais_destino'].queryset = Pais.objects.filter(ativo=True).order_by('nome')
    
    def clean(self):
        """Validações customizadas."""
        dados_limpos = super().clean()
        
        data_inicio = dados_limpos.get('data_inicio')
        data_fim = dados_limpos.get('data_fim')
        orcamento_min = dados_limpos.get('orcamento_diario_min')
        orcamento_max = dados_limpos.get('orcamento_diario_max')
        
        if data_inicio and data_fim:
            if data_fim <= data_inicio:
                raise ValidationError(
                    _('A data de término deve ser posterior à data de início.')
                )
        
        if orcamento_min and orcamento_max:
            if orcamento_max < orcamento_min:
                raise ValidationError(
                    _('O orçamento máximo deve ser maior que o mínimo.')
                )
        
        return dados_limpos


class FormularioBuscaViajantes(forms.Form):
    """Formulário para buscar viajantes por destino e critérios."""
    
    pais_destino = forms.ModelChoiceField(
        queryset=Pais.objects.filter(ativo=True).order_by('nome'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': 'Selecione um país'
        }),
        label=_('País de Destino')
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-custom',
            'type': 'date'
        }),
        label=_('Data de Início')
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-custom',
            'type': 'date'
        }),
        label=_('Data de Término')
    )
    
    motivo_viagem = forms.ChoiceField(
        choices=[('', '-- Todos os motivos --')] + PlanoViagem.MOTIVO_VIAGEM_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-custom'
        }),
        label=_('Motivo da Viagem')
    )
    
    duracao_minima = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': 'Dias'
        }),
        label=_('Duração Mínima (dias)')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'