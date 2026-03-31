import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.usuarios.models import Usuario


class Conversa(models.Model):
    """Modelo para gerenciar conversas entre amigos."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    participantes = models.ManyToManyField(
        Usuario, related_name="conversas", verbose_name=_("participantes")
    )
    data_criacao = models.DateTimeField(_("data de criação"), auto_now_add=True)
    data_ultima_mensagem = models.DateTimeField(
        _("data da última mensagem"), null=True, blank=True
    )
    ativa = models.BooleanField(_("ativa"), default=True)

    class Meta:
        verbose_name = _("conversa")
        verbose_name_plural = _("conversas")
        ordering = ["-data_ultima_mensagem"]

    def __str__(self):
        nomes = [u.get_nome_exibicao() for u in self.participantes.all()[:2]]
        return f"Conversa: {' <-> '.join(nomes)}"

    @classmethod
    def obter_ou_criar_conversa(cls, usuario1, usuario2):
        """Obtém ou cria uma conversa entre dois usuários."""
        conversa = (
            cls.objects.filter(participantes=usuario1)
            .filter(participantes=usuario2)
            .first()
        )

        if not conversa:
            conversa = cls.objects.create()
            conversa.participantes.add(usuario1, usuario2)

        return conversa


class Mensagem(models.Model):
    """Modelo para armazenar mensagens do chat."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name=_("conversa"),
    )
    remetente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="mensagens_enviadas",
        verbose_name=_("remetente"),
    )
    conteudo = models.TextField(_("conteúdo"), max_length=2000)
    data_envio = models.DateTimeField(_("data de envio"), auto_now_add=True)
    lida = models.BooleanField(_("lida"), default=False)
    data_leitura = models.DateTimeField(_("data de leitura"), null=True, blank=True)
    editada = models.BooleanField(_("editada"), default=False)
    data_edicao = models.DateTimeField(_("data de edição"), null=True, blank=True)

    class Meta:
        verbose_name = _("mensagem")
        verbose_name_plural = _("mensagens")
        ordering = ["data_envio"]
        indexes = [
            models.Index(fields=["conversa", "data_envio"]),
            models.Index(fields=["remetente", "lida"]),
        ]

    def __str__(self):
        return f"{self.remetente.get_nome_exibicao()}: {self.conteudo[:50]}"

    def marcar_como_lida(self):
        """Marca a mensagem como lida."""
        if not self.lida:
            self.lida = True
            self.data_leitura = timezone.now()
            self.save()
