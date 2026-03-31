import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.usuarios.models import Usuario


class SolicitacaoAmizade(models.Model):
    """Modelo para gerenciar solicitações de amizade."""

    STATUS_CHOICES = [
        ("pendente", _("Pendente")),
        ("aceita", _("Aceita")),
        ("recusada", _("Recusada")),
        ("cancelada", _("Cancelada")),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    remetente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="solicitacoes_enviadas",
        verbose_name=_("remetente"),
    )
    destinatario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="solicitacoes_recebidas",
        verbose_name=_("destinatário"),
    )
    mensagem = models.TextField(
        _("mensagem"),
        max_length=500,
        blank=True,
        help_text=_("Mensagem opcional ao enviar solicitação"),
    )
    status = models.CharField(
        _("status"), max_length=10, choices=STATUS_CHOICES, default="pendente"
    )
    data_criacao = models.DateTimeField(_("data de criação"), auto_now_add=True)
    data_resposta = models.DateTimeField(_("data de resposta"), null=True, blank=True)

    class Meta:
        verbose_name = _("solicitação de amizade")
        verbose_name_plural = _("solicitações de amizade")
        ordering = ["-data_criacao"]
        unique_together = ["remetente", "destinatario"]
        indexes = [
            models.Index(fields=["remetente", "status"]),
            models.Index(fields=["destinatario", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.remetente.get_nome_exibicao()} -> "
            f"{self.destinatario.get_nome_exibicao()}"
        )

    def aceitar(self):
        """Aceita a solicitação e cria uma amizade."""
        self.status = "aceita"
        self.data_resposta = timezone.now()
        self.save()

        # Criar amizade
        Amizade.objects.create(usuario1=self.remetente, usuario2=self.destinatario)

    def recusar(self):
        """Recusa a solicitação."""
        self.status = "recusada"
        self.data_resposta = timezone.now()
        self.save()

    def cancelar(self):
        """Cancela a solicitação (apenas pelo remetente)."""
        self.status = "cancelada"
        self.save()


@login_required
@require_POST
def enviar_solicitacao(request, user_id):
    destinatario = get_object_or_404(Usuario, id=user_id)
    remetente = request.user

    if destinatario == remetente:
        return JsonResponse({"error": "Operação inválida."}, status=400)

    if Amizade.sao_amigos(remetente, destinatario):
        return JsonResponse(
            {"message": "Vocês já estão conectados.", "status": "amigos"}, status=200
        )

    ja_existe = SolicitacaoAmizade.objects.filter(
        remetente=remetente, destinatario=destinatario, status="pendente"
    ).exists()

    if ja_existe:
        return JsonResponse({"message": "Solicitação já enviada."}, status=200)

    SolicitacaoAmizade.objects.create(
        remetente=remetente, destinatario=destinatario, status="pendente"
    )

    return JsonResponse({"message": "Solicitação enviada!"}, status=201)


class Amizade(models.Model):
    """Modelo para gerenciar amizades estabelecidas."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usuario1 = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="amizades_iniciadas",
        verbose_name=_("usuário 1"),
    )
    usuario2 = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="amizades_recebidas",
        verbose_name=_("usuário 2"),
    )
    data_criacao = models.DateTimeField(_("data de criação"), auto_now_add=True)
    ativa = models.BooleanField(_("ativa"), default=True)

    class Meta:
        verbose_name = _("amizade")
        verbose_name_plural = _("amizades")
        ordering = ["-data_criacao"]
        unique_together = ["usuario1", "usuario2"]
        indexes = [
            models.Index(fields=["usuario1", "ativa"]),
            models.Index(fields=["usuario2", "ativa"]),
        ]

    def __str__(self):
        return f"{self.usuario1.get_nome_exibicao()} <-> {self.usuario2.get_nome_exibicao()}"

    @classmethod
    def sao_amigos(cls, usuario1, usuario2):
        """Verifica se dois usuários são amigos."""
        return cls.objects.filter(
            models.Q(usuario1=usuario1, usuario2=usuario2)
            | models.Q(usuario1=usuario2, usuario2=usuario1),
            ativa=True,
        ).exists()

    def desfazer_amizade(self):
        """Remove a amizade."""
        self.ativa = False
        self.save()


class Bloqueio(models.Model):
    bloqueador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bloqueios_feitos",
        on_delete=models.CASCADE,
    )
    bloqueado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bloqueios_recebidos",
        on_delete=models.CASCADE,
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("bloqueador", "bloqueado")
        verbose_name = "Bloqueio"
        verbose_name_plural = "Bloqueios"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"{self.bloqueador} bloqueou {self.bloqueado}"
