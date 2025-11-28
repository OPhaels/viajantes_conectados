function validarFormulario(formularioId) {
    const formulario = document.getElementById(formularioId);
    
    if (!formulario) return true;
    
    const camposInvalidos = formulario.querySelectorAll(':invalid');
    
    if (camposInvalidos.length > 0) {
        camposInvalidos[0].focus();
        
        camposInvalidos.forEach(campo => {
            campo.classList.add('shake');
            setTimeout(() => {
                campo.classList.remove('shake');
            }, 500);
        });
        
        return false;
    }
    
    return true;
}

// Função para exibir modal de confirmação
function confirmarAcao(mensagem, callback) {
    if (confirm(mensagem)) {
        callback();
    }
}

// Função para formatar data em português
function formatarDataPTBR(dataISO) {
    const data = new Date(dataISO);
    return data.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Função para calcular diferença de dias
function calcularDiferencaDias(dataInicio, dataFim) {
    const inicio = new Date(dataInicio);
    const fim = new Date(dataFim);
    const diferencaMs = fim - inicio;
    return Math.ceil(diferencaMs / (1000 * 60 * 60 * 24));
}

// Adicionar animação de shake ao CSS
const estiloShake = document.createElement('style');
estiloShake.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    .shake {
        animation: shake 0.5s;
        border-color: var(--cor-acento) !important;
    }
`;
document.head.appendChild(estiloShake);

// Prevenir múltiplos envios de formulário
document.addEventListener('DOMContentLoaded', () => {
    const formularios = document.querySelectorAll('form');
    
    formularios.forEach(formulario => {
        formulario.addEventListener('submit', function(e) {
            const botaoSubmit = this.querySelector('[type="submit"]');
            
            if (botaoSubmit && !botaoSubmit.disabled) {
                botaoSubmit.disabled = true;
                botaoSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processando...';
                
                // Reabilitar após 3 segundos (caso não redirecione)
                setTimeout(() => {
                    botaoSubmit.disabled = false;
                    botaoSubmit.innerHTML = botaoSubmit.dataset.originalText || 'Enviar';
                }, 3000);
            }
        });
    });
});

console.log('🌍 Viajantes Conectados - Sistema inicializado com sucesso!');