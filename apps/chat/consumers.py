import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Conversa, Mensagem

logger = logging.getLogger(__name__)


class ConsumidorChat(AsyncWebsocketConsumer):
    """
    Consumer para WebSocket de chat em tempo real.
    Implementa segurança e validação de mensagens.
    """

    async def connect(self):
        """Estabelece conexão WebSocket."""
        self.usuario = self.scope["user"]
        self.uuid_conversa = self.scope["url_route"]["kwargs"]["uuid_conversa"]
        self.nome_grupo_chat = f"chat_{self.uuid_conversa}"

        # Verificar autenticação
        if not self.usuario.is_authenticated:
            await self.close()
            return

        # Verificar permissão para acessar a conversa
        tem_permissao = await self.verificar_permissao_conversa()
        if not tem_permissao:
            logger.warning(
                f"Tentativa de acesso não autorizado ao chat: "
                f"{self.usuario.email} -> {self.uuid_conversa}"
            )
            await self.close()
            return

        # Adicionar ao grupo do chat
        await self.channel_layer.group_add(self.nome_grupo_chat, self.channel_name)

        await self.accept()
        logger.info(
            f"Conexão WebSocket estabelecida: {self.usuario.email} - {self.uuid_conversa}"
        )

        # Enviar histórico de mensagens
        historico = await self.obter_historico_mensagens()
        await self.send(
            text_data=json.dumps({"tipo": "historico", "mensagens": historico})
        )

    async def disconnect(self, codigo_fechamento):
        """Encerra conexão WebSocket."""
        await self.channel_layer.group_discard(self.nome_grupo_chat, self.channel_name)
        logger.info(f"Conexão WebSocket encerrada: {self.usuario.email}")

    async def receive(self, text_data):
        """
        Recebe mensagem do cliente.
        Implementa validação e sanitização.
        """
        try:
            dados = json.loads(text_data)
            tipo_mensagem = dados.get("tipo", "mensagem")

            if tipo_mensagem == "mensagem":
                await self.processar_mensagem(dados)
            elif tipo_mensagem == "digitando":
                await self.processar_digitando(dados)
            elif tipo_mensagem == "leitura":
                await self.processar_leitura(dados)

        except json.JSONDecodeError as erro:
            logger.error(f"Erro ao decodificar JSON: {str(erro)}")
            await self.send_erro("Formato de mensagem inválido")

        except Exception as erro:
            logger.error(f"Erro ao processar mensagem: {str(erro)}")
            await self.send_erro("Erro ao processar mensagem")

    async def processar_mensagem(self, dados):
        """Processa e envia mensagem de texto."""
        conteudo = dados.get("conteudo", "").strip()

        # Validar conteúdo
        if not conteudo:
            await self.send_erro("Mensagem vazia")
            return

        if len(conteudo) > 2000:
            await self.send_erro("Mensagem muito longa (máximo 2000 caracteres)")
            return

        # Sanitizar conteúdo (remover scripts maliciosos)
        conteudo_sanitizado = self.sanitizar_conteudo(conteudo)

        # Salvar mensagem no banco de dados
        mensagem = await self.salvar_mensagem(conteudo_sanitizado)

        if mensagem:
            # Enviar para todos no grupo
            await self.channel_layer.group_send(
                self.nome_grupo_chat,
                {
                    "type": "chat_mensagem",
                    "mensagem": {
                        "uuid": str(mensagem.uuid),
                        "conteudo": mensagem.conteudo,
                        "remetente_id": mensagem.remetente.id,
                        "remetente_nome": mensagem.remetente.get_nome_exibicao(),
                        "data_envio": mensagem.data_envio.isoformat(),
                        "lida": mensagem.lida,
                    },
                },
            )
            logger.info(
                f"Mensagem enviada: {self.usuario.email} -> {self.uuid_conversa}"
            )

    async def processar_digitando(self, dados):
        """Notifica quando usuário está digitando."""
        await self.channel_layer.group_send(
            self.nome_grupo_chat,
            {
                "type": "usuario_digitando",
                "usuario_id": self.usuario.id,
                "usuario_nome": self.usuario.get_nome_exibicao(),
                "digitando": dados.get("digitando", False),
            },
        )

    async def processar_leitura(self, dados):
        """Marca mensagens como lidas."""
        uuid_mensagem = dados.get("uuid_mensagem")
        if uuid_mensagem:
            await self.marcar_mensagem_como_lida(uuid_mensagem)

    async def chat_mensagem(self, evento):
        """Envia mensagem para o WebSocket."""
        await self.send(
            text_data=json.dumps({"tipo": "mensagem", "mensagem": evento["mensagem"]})
        )

    async def usuario_digitando(self, evento):
        """Envia notificação de digitação."""
        # Não enviar de volta para o próprio usuário
        if evento["usuario_id"] != self.usuario.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "tipo": "digitando",
                        "usuario_nome": evento["usuario_nome"],
                        "digitando": evento["digitando"],
                    }
                )
            )

    async def send_erro(self, mensagem_erro):
        """Envia mensagem de erro ao cliente."""
        await self.send(
            text_data=json.dumps({"tipo": "erro", "mensagem": mensagem_erro})
        )

    @database_sync_to_async
    def verificar_permissao_conversa(self):
        """Verifica se o usuário tem permissão para acessar a conversa."""
        try:
            conversa = Conversa.objects.get(uuid=self.uuid_conversa)
            return conversa.participantes.filter(id=self.usuario.id).exists()
        except Conversa.DoesNotExist:
            return False

    @database_sync_to_async
    def salvar_mensagem(self, conteudo):
        """Salva mensagem no banco de dados."""
        try:
            conversa = Conversa.objects.get(uuid=self.uuid_conversa)

            mensagem = Mensagem.objects.create(
                conversa=conversa, remetente=self.usuario, conteudo=conteudo
            )

            # Atualizar timestamp da conversa
            conversa.data_ultima_mensagem = timezone.now()
            conversa.save()

            return mensagem

        except Exception as erro:
            logger.error(f"Erro ao salvar mensagem: {str(erro)}")
            return None

    @database_sync_to_async
    def obter_historico_mensagens(self, limite=50):
        """Obtém histórico de mensagens da conversa."""
        try:
            conversa = Conversa.objects.get(uuid=self.uuid_conversa)
            mensagens = conversa.mensagens.select_related("remetente").order_by(
                "-data_envio"
            )[:limite]

            historico = []
            for msg in reversed(list(mensagens)):
                historico.append(
                    {
                        "uuid": str(msg.uuid),
                        "conteudo": msg.conteudo,
                        "remetente_id": msg.remetente.id,
                        "remetente_nome": msg.remetente.get_nome_exibicao(),
                        "data_envio": msg.data_envio.isoformat(),
                        "lida": msg.lida,
                    }
                )

            return historico

        except Exception as erro:
            logger.error(f"Erro ao obter histórico: {str(erro)}")
            return []

    @database_sync_to_async
    def marcar_mensagem_como_lida(self, uuid_mensagem):
        """Marca uma mensagem como lida."""
        try:
            mensagem = Mensagem.objects.get(uuid=uuid_mensagem)
            if mensagem.remetente != self.usuario:
                mensagem.marcar_como_lida()
        except Mensagem.DoesNotExist:
            pass

    def sanitizar_conteudo(self, conteudo):
        """Remove conteúdo potencialmente malicioso."""
        import html
        import re

        # Escapar HTML
        conteudo_sanitizado = html.escape(conteudo)

        # Remover scripts
        conteudo_sanitizado = re.sub(
            r"<script[^>]*>.*?</script>", "", conteudo_sanitizado, flags=re.DOTALL
        )

        # Remover event handlers
        conteudo_sanitizado = re.sub(
            r'on\w+\s*=\s*["\'].*?["\']', "", conteudo_sanitizado
        )

        return conteudo_sanitizado
