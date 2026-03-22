from attrs import field
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import PlanoViagem, Pais
from .utils import validar_lista_urls_imagem

class FormularioPlanoViagem(forms.ModelForm):

    imagens_urls = forms.CharField(
        label='Imagens do Destino',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cole uma URL por linha (máx. 6)'
        }),
    )

    class Meta:
        model = PlanoViagem
        fields = [
            'pais_destino', 'cidade_destino', 'regiao_destino',
            'data_inicio', 'data_fim', 'datas_flexiveis',
            'motivo_viagem', 'descricao', 'nivel_privacidade',
            'orcamento_mensal_minimo',
            'imagens_urls',
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'motivo_viagem': forms.Select(),
            'nivel_privacidade': forms.Select(),
            'descricao': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔥 PADRONIZA TODOS OS CAMPOS
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{existing} form-control'.strip()

        # pré-preenche imagens
        if self.instance and self.instance.pk and self.instance.imagens_urls:
            self.initial['imagens_urls'] = '\n'.join(self.instance.imagens_urls)

        self.fields['pais_destino'].queryset = Pais.objects.filter(ativo=True).order_by('nome')

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'

    def clean_imagens_urls(self):
        valor = self.cleaned_data.get('imagens_urls', '')
        urls = [u.strip() for u in valor.splitlines() if u.strip()]

        if len(urls) > 6:
            raise ValidationError('Máximo de 6 imagens permitidas.')

        erros = validar_lista_urls_imagem(urls)
        if erros:
            raise ValidationError(erros)

        return urls

    def clean(self):
        dados = super().clean()

        data_inicio = dados.get('data_inicio')
        data_fim = dados.get('data_fim')
        orcamento_mensal_minimo = dados.get('orcamento_mensal_minimo')

        if not data_inicio:
            raise ValidationError(_('A data de início é obrigatória.'))

        if data_inicio and data_fim and data_fim <= data_inicio:
            raise ValidationError(_('A data de término deve ser posterior à data de início.'))

        return dados

 
class CampoUrlsImagens(forms.Field):
    """
    Campo customizado para múltiplas URLs de imagem.
    Aceita uma URL por linha no textarea.
    """
    widget = forms.Textarea
 
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('help_text',
            'Cole uma URL por linha (máx. 6). Use apenas imagens públicas com HTTPS.'
        )
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': (
                'https://images.unsplash.com/...\n'
                'https://i.imgur.com/...\n'
                'https://images.pexels.com/...'
            ),
        })
 
    def to_python(self, value):
        if not value:
            return []
        linhas = [l.strip() for l in value.strip().splitlines() if l.strip()]
        return linhas
 
    def validate(self, value):
        super().validate(value)
        if not value:
            return
        erros = validar_lista_urls_imagem(value)
        if erros:
            raise ValidationError(erros)
 
    def prepare_value(self, value):
        if isinstance(value, list):
            return '\n'.join(value)
        return value or ''
    

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
        
