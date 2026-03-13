class GerenciadorChat {
    constructor(uuidConversa, usuarioAtualId) {
        this.uuidConversa = uuidConversa;
        this.usuarioAtualId = usuarioAtualId;
        this.websocket = null;
        this.digitandoTimeout = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.inicializar();
    }

    inicializar() {
        this.conectarWebSocket();
        this.configurarEventos();
    }

    conectarWebSocket() {
        const protocolo = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const urlWebSocket = `${protocolo}//${window.location.host}/ws/chat/${this.uuidConversa}/`;

        try {
            this.websocket = new WebSocket(urlWebSocket);

            this.websocket.onopen = () => {
                console.log('Conexão WebSocket estabelecida');
                this.reconnectAttempts = 0;
                this.exibirNotificacao('Conectado ao chat', 'success');
                this.esconderReconectando();
            };

            this.websocket.onmessage = (evento) => {
                this.processarMensagem(evento);
            };

            this.websocket.onerror = (erro) => {
                console.error('Erro no WebSocket:', erro);
                this.exibirNotificacao('Erro na conexão', 'error');
            };

            this.websocket.onclose = () => {
                console.log('Conexão WebSocket fechada');
                this.tentarReconectar();
            };
        } catch (erro) {
            console.error('Erro ao criar WebSocket:', erro);
            this.exibirNotificacao('Erro ao conectar ao chat', 'error');
        }
    }

    tentarReconectar() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.mostrarReconectando();

            const tempoEspera = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

            setTimeout(() => {
                console.log(`Tentativa de reconexão ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.conectarWebSocket();
            }, tempoEspera);
        } else {
            this.exibirNotificacao('Não foi possível reconectar. Recarregue a página.', 'error');
        }
    }

    configurarEventos() {
        const formularioMensagem = document.getElementById('formulario-mensagem');
        const inputMensagem = document.getElementById('input-mensagem');

        // Enviar mensagem
        formularioMensagem.addEventListener('submit', (e) => {
            e.preventDefault();
            this.enviarMensagem();
        });

        // Detectar digitação
        inputMensagem.addEventListener('input', () => {
            this.notificarDigitando(true);

            clearTimeout(this.digitandoTimeout);
            this.digitandoTimeout = setTimeout(() => {
                this.notificarDigitando(false);
            }, 2000);
        });

        // Scroll automático
        this.scrollParaUltimaMensagem();
    }

    processarMensagem(evento) {
        try {
            const dados = JSON.parse(evento.data);

            switch (dados.tipo) {
                case 'historico':
                    this.carregarHistorico(dados.mensagens);
                    break;
                case 'mensagem':
                    this.adicionarMensagem(dados.mensagem);
                    break;
                case 'digitando':
                    this.mostrarDigitando(dados.usuario_nome, dados.digitando);
                    break;
                case 'erro':
                    this.exibirNotificacao(dados.mensagem, 'error');
                    break;
            }
        } catch (erro) {
            console.error('Erro ao processar mensagem:', erro);
        }
    }

    enviarMensagem() {
        const inputMensagem = document.getElementById('input-mensagem');
        const conteudo = inputMensagem.value.trim();

        if (!conteudo) return;

        if (conteudo.length > 2000) {
            this.exibirNotificacao('Mensagem muito longa (máximo 2000 caracteres)', 'error');
            return;
        }

        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                tipo: 'mensagem',
                conteudo: conteudo
            }));

            inputMensagem.value = '';
            this.notificarDigitando(false);
        } else {
            this.exibirNotificacao('Conexão perdida. Tentando reconectar...', 'warning');
        }
    }

    notificarDigitando(digitando) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                tipo: 'digitando',
                digitando: digitando
            }));
        }
    }

    carregarHistorico(mensagens) {
        const containerMensagens = document.getElementById('chat-mensagens');
        containerMensagens.innerHTML = '';

        mensagens.forEach(mensagem => {
            this.adicionarMensagem(mensagem, false);
        });

        this.scrollParaUltimaMensagem();
    }

    adicionarMensagem(mensagem, animacao = true) {
        const containerMensagens = document.getElementById('chat-mensagens');

        const divMensagem = document.createElement('div');
        divMensagem.className = 'mensagem';

        const eMinhaMensagem = mensagem.remetente_id === this.usuarioAtualId;
        divMensagem.classList.add(eMinhaMensagem ? 'mensagem-enviada' : 'mensagem-recebida');

        if (animacao) {
            divMensagem.style.opacity = '0';
            divMensagem.style.transform = 'translateY(20px)';
        }

        const dataFormatada = this.formatarData(mensagem.data_envio);

        divMensagem.innerHTML = `
            <div class="mensagem-conteudo">
                ${this.escaparHTML(mensagem.conteudo)}
            </div>
            <div class="mensagem-info">
                <small>${eMinhaMensagem ? 'Você' : mensagem.remetente_nome} · ${dataFormatada}</small>
                ${eMinhaMensagem && mensagem.lida ? '<i class="bi bi-check-all text-primary"></i>' : ''}
            </div>
        `;

        containerMensagens.appendChild(divMensagem);

        if (animacao) {
            setTimeout(() => {
                divMensagem.style.transition = 'all 0.3s ease';
                divMensagem.style.opacity = '1';
                divMensagem.style.transform = 'translateY(0)';
            }, 10);
        }

        this.scrollParaUltimaMensagem();

        // Marcar como lida se não for minha mensagem
        if (!eMinhaMensagem && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                tipo: 'leitura',
                uuid_mensagem: mensagem.uuid
            }));
        }
    }

    mostrarDigitando(nomeUsuario, digitando) {
        const indicadorDigitando = document.getElementById('indicador-digitando');

        if (digitando) {
            indicadorDigitando.textContent = `${nomeUsuario} está digitando...`;
            indicadorDigitando.style.display = 'block';
        } else {
            indicadorDigitando.style.display = 'none';
        }
    }

    scrollParaUltimaMensagem() {
        const containerMensagens = document.getElementById('chat-mensagens');
        containerMensagens.scrollTop = containerMensagens.scrollHeight;
    }

    formatarData(isoString) {
        const data = new Date(isoString);
        const agora = new Date();
        const diferencaDias = Math.floor((agora - data) / (1000 * 60 * 60 * 24));

        if (diferencaDias === 0) {
            return data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } else if (diferencaDias === 1) {
            return 'Ontem';
        } else {
            return data.toLocaleDateString('pt-BR');
        }
    }

    escaparHTML(texto) {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    exibirNotificacao(mensagem, tipo) {
        // Criar elemento de notificação
        const divNotificacao = document.createElement('div');
        divNotificacao.className = `alert alert-${tipo === 'error' ? 'danger' : tipo === 'success' ? 'success' : 'warning'} alert-custom`;
        divNotificacao.textContent = mensagem;
        divNotificacao.style.position = 'fixed';
        divNotificacao.style.top = '20px';
        divNotificacao.style.right = '20px';
        divNotificacao.style.zIndex = '9999';

        document.body.appendChild(divNotificacao);

        setTimeout(() => {
            divNotificacao.remove();
        }, 3000);
    }

    mostrarReconectando() {
        const indicadorStatus = document.getElementById('indicador-status');
        if (indicadorStatus) {
            indicadorStatus.textContent = 'Reconectando...';
            indicadorStatus.className = 'badge bg-warning';
        }
    }

    esconderReconectando() {
        const indicadorStatus = document.getElementById('indicador-status');
        if (indicadorStatus) {
            indicadorStatus.textContent = 'Online';
            indicadorStatus.className = 'badge bg-success';
        }
    }
}


// =====================================================
// static/js/mapa.js - Mapa Interativo com Mapbox
// =====================================================

class GerenciadorMapa {
    constructor(elementoMapaId, tokenMapbox) {
        this.elementoMapaId = elementoMapaId;
        this.tokenMapbox = tokenMapbox;
        this.mapa = null;
        this.marcadores = [];

        this.inicializar();
    }

    inicializar() {
        mapboxgl.accessToken = this.tokenMapbox;

        this.mapa = new mapboxgl.Map({
            container: this.elementoMapaId,
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [-47.8825, -15.7942], // Brasília como centro padrão
            zoom: 3,
            projection: 'globe'
        });

        // Adicionar controles de navegação
        this.mapa.addControl(new mapboxgl.NavigationControl(), 'top-right');

        // Adicionar controle de tela cheia
        this.mapa.addControl(new mapboxgl.FullscreenControl(), 'top-right');

        // Efeito de rotação do globo
        this.mapa.on('load', () => {
            this.mapa.setFog({
                color: 'rgb(186, 210, 235)',
                'high-color': 'rgb(36, 92, 223)',
                'horizon-blend': 0.02,
                'space-color': 'rgb(11, 11, 25)',
                'star-intensity': 0.6
            });
        });
    }

    adicionarMarcador(latitude, longitude, titulo, descricao, cor = '#4a90e2') {
        const elementoMarcador = document.createElement('div');
        elementoMarcador.className = 'marcador-customizado';
        elementoMarcador.style.backgroundColor = cor;
        elementoMarcador.style.width = '30px';
        elementoMarcador.style.height = '30px';
        elementoMarcador.style.borderRadius = '50%';
        elementoMarcador.style.border = '3px solid white';
        elementoMarcador.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
        elementoMarcador.style.cursor = 'pointer';
        elementoMarcador.style.transition = 'all 0.3s ease';

        elementoMarcador.addEventListener('mouseenter', () => {
            elementoMarcador.style.transform = 'scale(1.2)';
        });

        elementoMarcador.addEventListener('mouseleave', () => {
            elementoMarcador.style.transform = 'scale(1)';
        });

        const popup = new mapboxgl.Popup({ offset: 25 })
            .setHTML(`
                <div style="padding: 10px;">
                    <h6 style="margin: 0 0 5px 0; color: #2c3e50;">${titulo}</h6>
                    <p style="margin: 0; color: #7f8c8d; font-size: 14px;">${descricao}</p>
                </div>
            `);

        const marcador = new mapboxgl.Marker(elementoMarcador)
            .setLngLat([longitude, latitude])
            .setPopup(popup)
            .addTo(this.mapa);

        this.marcadores.push(marcador);

        return marcador;
    }

    centralizarEm(latitude, longitude, zoom = 10) {
        this.mapa.flyTo({
            center: [longitude, latitude],
            zoom: zoom,
            duration: 2000,
            essential: true
        });
    }

    ajustarParaMarcadores() {
        if (this.marcadores.length === 0) return;

        const limites = new mapboxgl.LngLatBounds();

        this.marcadores.forEach(marcador => {
            limites.extend(marcador.getLngLat());
        });

        this.mapa.fitBounds(limites, {
            padding: { top: 50, bottom: 50, left: 50, right: 50 },
            duration: 2000
        });
    }

    limparMarcadores() {
        this.marcadores.forEach(marcador => marcador.remove());
        this.marcadores = [];
    }

    buscarPais(nomePais, callback) {
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(nomePais)}.json?access_token=${this.tokenMapbox}&types=country&language=pt`;

        fetch(url)
            .then(resposta => resposta.json())
            .then(dados => {
                if (dados.features && dados.features.length > 0) {
                    const pais = dados.features[0];
                    const [longitude, latitude] = pais.center;

                    callback({
                        nome: pais.place_name,
                        latitude: latitude,
                        longitude: longitude,
                        bbox: pais.bbox
                    });
                } else {
                    callback(null);
                }
            })
            .catch(erro => {
                console.error('Erro ao buscar país:', erro);
                callback(null);
            });
    }
}

// ── Configurações ───────────────────────────────────────────────────────
const CONVERSA_UUID = "{{ conversa.uuid }}";
const USUARIO_ATUAL = "{{ request.user.uuid }}";
const CSRF_TOKEN = "{{ csrf_token }}";
const URL_MENSAGENS = "{% url 'chat:mensagens_json' uuid_conversa=conversa.uuid %}";
const URL_APAGAR = "{% url 'chat:apagar_mensagem' mensagem_id=0 %}".replace('0', '');
const POLLING_MS = 4000; // intervalo de atualização (ms)

const container = document.getElementById('mensagens-container');
const inputMensagem = document.getElementById('inputMensagem');
const formMensagem = document.getElementById('formMensagem');
const btnEnviar = document.getElementById('btnEnviar');
const alertaErro = document.getElementById('alertaErro');
const alertaErroTexto = document.getElementById('alertaErroTexto');
const emptyMessages = document.getElementById('emptyMessages');

// ── Scroll automático ───────────────────────────────────────────────────
function scrollParaBaixo() {
    container.scrollTop = container.scrollHeight;
}
scrollParaBaixo();

// ── Contagem de caracteres ──────────────────────────────────────────────
const contagem = document.getElementById('contagemCaracteres');
inputMensagem.addEventListener('input', () => {
    const len = inputMensagem.value.length;
    contagem.textContent = `${len} / 2000`;
    contagem.classList.toggle('text-danger', len > 1800);
});

// ── Enviar com Enter (Shift+Enter = nova linha) ─────────────────────────
inputMensagem.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (inputMensagem.value.trim()) formMensagem.requestSubmit();
    }
});

// ── Envio via AJAX ──────────────────────────────────────────────────────
formMensagem.addEventListener('submit', async (e) => {
    e.preventDefault();

    const conteudo = inputMensagem.value.trim();
    if (!conteudo) return;

    // Sanitização básica: remove tags HTML
    const conteudoSanitizado = conteudo.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    btnEnviar.disabled = true;
    esconderErro();

    try {
        const resp = await fetch(formMensagem.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `conteudo=${encodeURIComponent(conteudo)}`,
        });

        if (!resp.ok) throw new Error(`Erro ${resp.status}: não foi possível enviar a mensagem.`);

        const data = await resp.json();

        if (data.status === 'ok' || data.id) {
            inputMensagem.value = '';
            contagem.textContent = '0 / 2000';
            if (emptyMessages) emptyMessages.remove();
            adicionarMensagemDOM(data);
            scrollParaBaixo();
        } else {
            mostrarErro(data.erro || 'Erro ao enviar mensagem.');
        }
    } catch (err) {
        mostrarErro(err.message || 'Falha na conexão. Verifique sua internet.');
    } finally {
        btnEnviar.disabled = false;
        inputMensagem.focus();
    }
});

// ── Adicionar mensagem no DOM ───────────────────────────────────────────
function adicionarMensagemDOM(msg) {
    const div = document.createElement('div');
    div.className = 'mensagem mensagem-enviada';
    div.dataset.id = msg.id;
    div.innerHTML = `
            <div class="mensagem-balao">
                <div class="mensagem-conteudo">${escapeHTML(msg.conteudo)}</div>
                <div class="mensagem-acoes">
                    <button class="btn-acao" title="Copiar" onclick="copiarMensagem(this)">
                        <i class="bi bi-clipboard"></i>
                    </button>
                    <button class="btn-acao btn-apagar" title="Apagar"
                        onclick="apagarMensagem(${msg.id}, this)">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
                <p class="mensagem-timestamp">
                    ${msg.hora || new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    <i class="bi bi-check2 ms-1"></i>
                </p>
            </div>`;
    container.appendChild(div);
}

// ── Polling: busca novas mensagens periodicamente ───────────────────────
let ultimoId = obterUltimoId();

function obterUltimoId() {
    const msgs = container.querySelectorAll('.mensagem[data-id]');
    if (!msgs.length) return 0;
    return Math.max(...[...msgs].map(m => parseInt(m.dataset.id) || 0));
}

async function buscarNovasMensagens() {
    try {
        const resp = await fetch(`${URL_MENSAGENS}?after=${ultimoId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!resp.ok) return;

        const data = await resp.json();

        if (data.mensagens && data.mensagens.length > 0) {
            if (emptyMessages) emptyMessages.remove();
            const estavaNoBaixo = container.scrollHeight - container.scrollTop - container.clientHeight < 100;

            data.mensagens.forEach(msg => {
                if (!container.querySelector(`[data-id="${msg.id}"]`)) {
                    const isMinha = msg.remetente_uuid === USUARIO_ATUAL;
                    const div = document.createElement('div');
                    div.className = `mensagem ${isMinha ? 'mensagem-enviada' : 'mensagem-recebida'}`;
                    div.dataset.id = msg.id;
                    div.innerHTML = `
                            <div class="mensagem-balao">
                                <div class="mensagem-conteudo">${escapeHTML(msg.conteudo)}</div>
                                <div class="mensagem-acoes">
                                    <button class="btn-acao" title="Copiar" onclick="copiarMensagem(this)">
                                        <i class="bi bi-clipboard"></i>
                                    </button>
                                    ${isMinha ? `<button class="btn-acao btn-apagar" title="Apagar"
                                        onclick="apagarMensagem(${msg.id}, this)">
                                        <i class="bi bi-trash"></i>
                                    </button>` : ''}
                                </div>
                                <p class="mensagem-timestamp">${msg.hora} <i class="bi bi-check2 ms-1"></i></p>
                            </div>`;
                    container.appendChild(div);
                    ultimoId = Math.max(ultimoId, msg.id);
                }
            });

            if (estavaNoBaixo) scrollParaBaixo();
        }

        // Indicador "está digitando"
        const indicador = document.getElementById('digitandoIndicador');
        if (data.digitando) {
            indicador.classList.remove('d-none');
            scrollParaBaixo();
        } else {
            indicador.classList.add('d-none');
        }

    } catch (_) {
        // silencioso para não poluir a UI em falhas de rede temporárias
    }
}

setInterval(buscarNovasMensagens, POLLING_MS);

// ── "Está digitando": notifica o servidor ──────────────────────────────
let digitandoTimeout;
inputMensagem.addEventListener('input', () => {
    clearTimeout(digitandoTimeout);
    // Notifica que está digitando (endpoint opcional)
    fetch(`/chat/${CONVERSA_UUID}/digitando/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'X-Requested-With': 'XMLHttpRequest' },
    }).catch(() => { });

    // Para de notificar após 3s de inatividade
    digitandoTimeout = setTimeout(() => {
        fetch(`/chat/${CONVERSA_UUID}/parou-digitar/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN, 'X-Requested-With': 'XMLHttpRequest' },
        }).catch(() => { });
    }, 3000);
});

// ── Copiar mensagem ─────────────────────────────────────────────────────
function copiarMensagem(btn) {
    const texto = btn.closest('.mensagem-balao')
        .querySelector('.mensagem-conteudo')
        .textContent.trim();
    navigator.clipboard.writeText(texto).then(() => {
        const toast = new bootstrap.Toast(document.getElementById('toastCopiado'));
        toast.show();
    }).catch(() => {
        mostrarErro('Não foi possível copiar. Selecione o texto manualmente.');
    });
}

// ── Apagar mensagem ─────────────────────────────────────────────────────
async function apagarMensagem(id, btn) {
    if (!confirm('Apagar esta mensagem?')) return;

    try {
        const resp = await fetch(`${URL_APAGAR}${id}/apagar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
        });

        if (!resp.ok) throw new Error();

        const elem = btn.closest('.mensagem');
        elem.style.transition = 'opacity 0.3s';
        elem.style.opacity = '0';
        setTimeout(() => elem.remove(), 300);

    } catch (_) {
        mostrarErro('Não foi possível apagar a mensagem.');
    }
}

// ── Helpers ─────────────────────────────────────────────────────────────
function escapeHTML(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function mostrarErro(msg) {
    alertaErroTexto.textContent = msg;
    alertaErro.classList.remove('d-none');
    setTimeout(esconderErro, 5000);
}

function esconderErro() {
    alertaErro.classList.add('d-none');
}