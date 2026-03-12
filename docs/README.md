# 📚 Índice de Documentação

Bem-vindo! Esta é a **central de documentação** do Viajantes Conectados. Navegue por tema abaixo.

---

## 🎯 Por Onde Começar?

### ⭐ Primeiro Dia (Recomendado)
1. **Leia:** [📖 README.md](../README.md) - Visão geral do projeto
2. **Siga:** [🚀 GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) - Setup completo
3. **Entenda:** [📊 RESUMO_EXECUCAO.md](guias/RESUMO_EXECUCAO.md) - O que foi feito

### Segunda Semana
- **API:** [📖 API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) - Todos os endpoints
- **Dev:** [🛠️ DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) - Estrutura código
- **Segurança:** [🔒 SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md) - Práticas

---

## 📂 Estrutura de Documentação

### 📋 [Guias](/docs/guias/)
Documentos práticos para entender e usar o projeto.

| Arquivo | Descrição | Quando ler |
|---------|-----------|-----------|
| [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) | Setup, testes, deployment | Primeiro! ⭐ |
| [RESUMO_EXECUCAO.md](guias/RESUMO_EXECUCAO.md) | O que foi limpo e refatorado | Entender o projeto |
| [CHANGELOG_LIMPEZA.md](guias/CHANGELOG_LIMPEZA.md) | Mudanças técnicas detalhadas | Antes de mergear |

### 🔌 [API](/docs/api/)
Documentação da REST API e referências técnicas.

| Arquivo | Descrição | Quando ler |
|---------|-----------|-----------|
| [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) | Todos endpoints, parâmetros, respostas | Usando a API |
| [API_TESTES.md](api/API_TESTES.md) | Exemplos de requisições HTTP | Testando endpoints |
| [QUICK_REFERENCE.md](api/QUICK_REFERENCE.md) | Cheat sheet, comandos úteis | Desenvolvimento rápido |

### 🔒 [Segurança](/docs/seguranca/)
Práticas e configurações de segurança.

| Arquivo | Descrição | Quando ler |
|---------|-----------|-----------|
| [SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md) | Guia de melhores práticas | Setup inicial |
| [SECURITY.md](seguranca/SECURITY.md) | Implementação técnica | Deployment produção |

### 🛠️ [Desenvolvimento](/docs/desenvolvimento/)
Guias para desenvolvedores.

| Arquivo | Descrição | Quando ler |
|---------|-----------|-----------|
| [DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) | Setup local, estrutura código | Começar desenvolvimento |
| [IMPROVEMENTS.md](desenvolvimento/IMPROVEMENTS.md) | Roadmap, melhorias planejadas | Sprint planning |

### 📄 Raiz de Docs
| Arquivo | Descrição |
|---------|-----------|
| [DOCS_INDEX.md](DOCS_INDEX.md) | Índice detalhado (legado) |
| [SUMMARY.md](SUMMARY.md) | Resumo geral do projeto |

---

## 🗂️ Organizção Física

```
/docs/
├── README.md (este arquivo)
├── DOCS_INDEX.md
├── SUMMARY.md
│
├── guias/                   # Documentos práticos
│   ├── GUIA_PROXIMOS_PASSOS.md
│   ├── RESUMO_EXECUCAO.md
│   └── CHANGELOG_LIMPEZA.md
│
├── api/                     # REST API
│   ├── API_DOCUMENTATION.md
│   ├── API_TESTES.md
│   └── QUICK_REFERENCE.md
│
├── seguranca/              # Segurança
│   ├── SECURITY_GUIDE.md
│   └── SECURITY.md
│
└── desenvolvimento/        # Setup & Dev
    ├── DEVELOPMENT_GUIDE.md
    └── IMPROVEMENTS.md
```

---

## 🎯 Por Caso de Uso

### "Quero rodar a aplicação localmente"
1. [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) - Seção 1-2
2. [DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) - Setup

### "Vou usar a API"
1. [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) - Endpoints disponíveis
2. [API_TESTES.md](api/API_TESTES.md) - Exemplos de código
3. [QUICK_REFERENCE.md](api/QUICK_REFERENCE.md) - Dicas rápidas

### "Vou fazer deploy em produção"
1. [SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md) - Checklist segurança
2. [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) - Seção 5
3. [SECURITY.md](seguranca/SECURITY.md) - Configurações detalhadas

### "Vou desenvolver uma feature"
1. [DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) - Estrutura
2. [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) - Testes
3. [IMPROVEMENTS.md](desenvolvimento/IMPROVEMENTS.md) - Inspiração

### "Quero entender o que foi refatorado"
1. [RESUMO_EXECUCAO.md](guias/RESUMO_EXECUCAO.md) - Overview
2. [CHANGELOG_LIMPEZA.md](guias/CHANGELOG_LIMPEZA.md) - Detalhado
3. [SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md) - Mudanças segurança

---

## 📊 Estatísticas Documentação

| Métrica | Valor |
|---------|-------|
| **Total de .md** | 13 |
| **Linhas documentação** | ~3.500+ |
| **Seções** | 5 |
| **Pastas /docs** | 5 |
| **Tempo para setup** | 30 min ⏱️ |
| **Tempo para primeira API** | 15 min 🚀 |

---

## 🔍 Buscar Informações

### Procurando por...

**Autenticação/Login:**
- [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) - Endpoints auth
- [SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md) - Proteção

**Rate Limiting:**
- [CHANGELOG_LIMPEZA.md](guias/CHANGELOG_LIMPEZA.md) - Implementação
- [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) - Limites por endpoint

**Modelos/Banco de Dados:**
- [DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) - Estrutura

**WebSockets/Chat:**
- [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md) - Chat endpoints
- [DEVELOPMENT_GUIDE.md](desenvolvimento/DEVELOPMENT_GUIDE.md) - Setup Channels

**Testes:**
- [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md) - Seção 3
- [API_TESTES.md](api/API_TESTES.md) - Exemplos

---

## 💡 Dicas

### Atalhos Recomendados

- **Desenvolvedor novo?** → Comece com [GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md)
- **Integrando API?** → Consulte [API_DOCUMENTATION.md](api/API_DOCUMENTATION.md)
- **Preocupado com bug?** → Veja [SECURITY_GUIDE.md](seguranca/SECURITY_GUIDE.md)
- **Perdido?** → Você está aqui! 👋

### Manutenção de Docs

Quando atualizar código:
1. Atualize o arquivo .md correspondente
2. Se novo arquivo, adicione aqui em [Índice](#estrutura-de-documentação)
3. Valide com: `grep -r "TODO" docs/` (encontre pendências)

---

## 📞 Suporte

- **Erro na documentação?** Abra issue
- **Falta informação?** Volte aqui e procure outra seção
- **Perdeu algo?** Use Ctrl+F neste arquivo

---

**Versão:** 1.0 | **Última atualização:** Março 2026 | **Status:** ✅ Completo

**👉 [Comece aqui! GUIA_PROXIMOS_PASSOS.md](guias/GUIA_PROXIMOS_PASSOS.md)**
