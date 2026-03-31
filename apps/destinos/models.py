import uuid

from django import forms
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.usuarios.models import Usuario


class Pais(models.Model):
    """Modelo para armazenar países."""

    codigo_iso = models.CharField(
        _("código ISO"),
        max_length=2,
        unique=True,
        help_text=_("Código ISO 3166-1 alpha-2"),
    )
    nome = models.CharField(_("nome"), max_length=100, unique=True)
    nome_completo = models.CharField(_("nome completo"), max_length=200)
    continente = models.CharField(_("continente"), max_length=50)
    latitude = models.DecimalField(_("latitude"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("longitude"), max_digits=9, decimal_places=6)
    ativo = models.BooleanField(_("ativo"), default=True)

    imagem = models.ImageField(
        _("imagem do país"), upload_to="paises/", blank=True, null=True
    )

    class Meta:
        verbose_name = _("país")
        verbose_name_plural = _("países")
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PlanoViagem(models.Model):
    """
    Modelo para armazenar os planos de viagem dos usuários.
    Contém informações sensíveis que devem ser protegidas.
    """

    MOTIVO_VIAGEM_CHOICES = [
        ("turismo", _("Turismo")),
        ("trabalho", _("Trabalho")),
        ("estudo", _("Estudo")),
        ("voluntariado", _("Voluntariado")),
        ("outro", _("Outro")),
    ]

    NIVEL_PRIVACIDADE_CHOICES = [
        ("publico", _("Público - Visível para todos")),
        ("amigos", _("Apenas Amigos")),
        ("privado", _("Privado - Não visível")),
    ]

    # Identificação
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="planos_viagem",
        verbose_name=_("usuário"),
    )

    # Destino
    pais_destino = models.ForeignKey(
        Pais,
        on_delete=models.PROTECT,
        related_name="planos_viagem",
        verbose_name=_("país de destino"),
    )
    cidade_destino = models.CharField(
        _("cidade de destino"), max_length=100, blank=True
    )
    regiao_destino = models.CharField(
        _("região de destino"), max_length=100, blank=True
    )

    # Datas
    data_inicio = models.DateField(_("data de início"))
    data_fim = models.DateField(_("data de término"), null=True, blank=True)
    datas_flexiveis = models.BooleanField(
        _("datas flexíveis"),
        default=False,
        help_text=_("Indica se as datas podem ser ajustadas"),
    )

    # Detalhes da Viagem
    motivo_viagem = models.CharField(
        _("motivo da viagem"),
        max_length=20,
        choices=MOTIVO_VIAGEM_CHOICES,
        default="turismo",
    )
    descricao = models.TextField(
        _("descrição"),
        max_length=1000,
        blank=True,
        help_text=_("Descreva seus planos e interesses para a viagem"),
    )

    # Privacidade
    nivel_privacidade = models.CharField(
        _("nível de privacidade"),
        max_length=10,
        choices=NIVEL_PRIVACIDADE_CHOICES,
        default="publico",
    )

    # Orçamento (mensal, como usado no template)
    orcamento_mensal_minimo = models.DecimalField(
        _("orçamento mensal mínimo"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Imagens (lista de URLs públicas)
    imagens_urls = models.JSONField(
        verbose_name=_("URLs de imagens"),
        default=list,
        blank=True,
        help_text=_(
            'Lista de URLs públicas de imagens do destino (máx. 6). Ex: ["url1", "url2"]'
        ),
    )

    # Status
    ativo = models.BooleanField(_("ativo"), default=True)
    viagem_concluida = models.BooleanField(_("viagem concluída"), default=False)
    data_criacao = models.DateTimeField(_("data de criação"), auto_now_add=True)
    data_atualizacao = models.DateTimeField(_("data de atualização"), auto_now=True)

    class Meta:
        verbose_name = _("plano de viagem")
        verbose_name_plural = _("planos de viagem")
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["usuario", "ativo"]),
            models.Index(fields=["pais_destino", "data_inicio"]),
            models.Index(fields=["nivel_privacidade"]),
        ]

    def __str__(self):
        return f"{self.usuario.get_nome_exibicao()} - {self.pais_destino.nome}"

    @property
    def duracao_dias(self):
        if self.data_fim:
            return (self.data_fim - self.data_inicio).days
        return None

    def pode_ser_visto_por(self, usuario_solicitante):
        """Verifica se um usuário pode ver este plano de viagem."""
        if self.usuario == usuario_solicitante:
            return True

        if self.nivel_privacidade == "publico":
            return True

        if self.nivel_privacidade == "privado":
            return False

        # Nível 'amigos'
        from apps.conexoes.models import Amizade

        return Amizade.sao_amigos(self.usuario, usuario_solicitante)


class EnderecoPlano(models.Model):
    """
    Endereço e coordenadas associados a um PlanoViagem (1:1).
    """

    plano = models.OneToOneField(
        PlanoViagem,
        on_delete=models.CASCADE,
        related_name="endereco_plano",
        verbose_name=_("plano de viagem"),
    )
    cep = models.CharField(_("CEP"), max_length=20, blank=True, null=True)
    endereco = models.CharField(_("endereço"), max_length=255, blank=True)
    numero = models.CharField(_("número"), max_length=30, blank=True)
    bairro = models.CharField(_("bairro"), max_length=120, blank=True)
    cidade = models.CharField(_("cidade"), max_length=120, blank=True)
    estado = models.CharField(_("estado"), max_length=120, blank=True)
    pais_texto = models.CharField(_("país (texto)"), max_length=120, blank=True)

    latitude = models.DecimalField(
        _("latitude"), max_digits=10, decimal_places=7, blank=True, null=True
    )
    longitude = models.DecimalField(
        _("longitude"), max_digits=10, decimal_places=7, blank=True, null=True
    )

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)
    atualizado_em = models.DateTimeField(_("atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("endereço do plano")
        verbose_name_plural = _("endereços dos planos")

    def __str__(self):
        return f"{self.endereco} — {self.cidade} / {self.estado}"


class PlanoViagemForm(forms.ModelForm):
    class Meta:
        model = PlanoViagem
        fields = [
            "pais_destino",
            "cidade_destino",
            "regiao_destino",
            "data_inicio",
            "data_fim",
            "motivo_viagem",
            "nivel_privacidade",
            "orcamento_mensal_minimo",
        ]
        widgets = {
            "pais_destino": forms.Select(attrs={"class": "form-select"}),
        }


class OfertaResidencia(models.Model):
    """
    Informações da oferta de residência (opcional), vinculada a um PlanoViagem.
    """

    plano = models.OneToOneField(
        PlanoViagem,
        on_delete=models.CASCADE,
        related_name="oferta_residencia",
        verbose_name=_("plano de viagem"),
    )
    nome_anfitriao = models.CharField(_("nome do anfitrião"), max_length=150)
    contato_anfitriao = models.CharField(_("contato do anfitrião"), max_length=150)
    descricao_local = models.TextField(_("descrição da residência"), blank=True)

    criado_em = models.DateTimeField(_("criado em"), auto_now_add=True)

    class Meta:
        verbose_name = _("oferta de residência")
        verbose_name_plural = _("ofertas de residência")

    def __str__(self):
        return f"{self.nome_anfitriao} — {self.contato_anfitriao}"
