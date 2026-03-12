# CHANGELOG - Viajantes Conectados

## [VERSÃO LIMPA E SEGURA] - Refatoração Completa

### 🔒 SEGURANÇA - Mudanças Críticas

#### ✅ Implementado
- **[CRÍTICO]** Removido CSP Middleware descontinuado que removia proteções contra XSS
- **[CRÍTICO]** Implementado token de verificação seguro usando JWT com expiração automática
  - Antigo: SHA256 com timestamp público (previsível)
  - Novo: JWT com claims customizados + validação de expiração
- **[CRÍTICO]** Configurado CORS corretamente com whitelist de origens
  - Adicionar `CORS_ALLOWED_ORIGINS` em `.env`
  - Credenciais habilitadas nas requisições
- **[ALTO]** Removidas senhas de exemplo em documentações
  - Substitua `<INSIRA_SUA_SENHA>` com valores reais em `.env`
- **[ALTO]** Implementado rate limiting robusto (apps/core/throttles.py)
  - Login: 5 tentativas/minuto
  - Registro: 10 por hora
  - Email verificação: 3 por hora
  - Amizade: 10 por hora
  - Planos: 30 por dia
  - Mensagens: 100 por hora
  - Busca: 100/hora (anônimo), 500/hora (autenticado)
- **[ALTO]** Implementado audit logging completo (apps/core/models.py)
  - LogAuditoria: Rastreia TODAS as ações sensíveis
  - TentativaLoginFalhado: Detecção de força bruta
  - Integrado com admin Django

---

### 🔧 DUPLICIDADE - Eliminadas Completamente

#### Arquivos Deletados (Garantia de Zero Duplicidade)
- ❌ `apps/core/viewsets.py` → UsuarioViewSetMelhorado (não utilizado, mantém usuarios/viewsets.py)
- ❌ `apps/middleware.py` → MapboxCSPMiddleware (remove proteção contra XSS)
- ❌ `apps/usuarios/signals.py` → Arquivo vazio sem uso
- ❌ `apps/destinos/signals.py` → Arquivo vazio sem uso

#### Serializers Consolidados
- ✅ `apps/destinos/serializers.py` agora importa `UsuarioPerfilSerializer` de `apps/usuarios.serializers`
  - Antes: 2 classes duplicadas (UsuarioResumidoSerializer + UsuarioPerfilSerializer)
  - Depois: 1 classe única, reutilizável
  - Atualizado em PlanoViagemSerializer e PlanoViagemListaSerializer

#### APIs Legacy Descontinuadas
- ✅ `/api/paises/autocomplete/` → Retorna HTTP 410 Gone com instruções de migração
  - Use novo endpoint: `GET /destinos/api/paises/?search=<termo>`
- ✅ `/api/estatisticas/<int:pais_id>/` → Retorna HTTP 410 Gone
  - Use novo endpoint: `GET /destinos/api/planos/?pais_destino=<id>`

---

### 📊 PERFORMANCE - Otimizações

#### Query Optimization (N+1 Elimination)
- ✅ PlanoViagemViewSet.get_queryset() otimizado com `select_related()`
  - Usuario + PaisDestino carregados em 1 query
  - Filtro de amigos otimizado com subquery única
  - Antes: múltiplas queries por produto exibido
  - Depois: número fixo de queries independente do tamanho da listagem

#### Paginação Padronizada
- ✅ Configurado `DEFAULT_PAGINATION_CLASS` em REST_FRAMEWORK
- ✅ Page size padrão: 20 itens (configurável por cliente)
- ✅ Máximo: 100 itens por página

---

### 🏗️ ESTRUTURA - Organizacional

#### Sistema de Rate Limiting (apps/core/throttles.py)
```
LoginThrottle                    → 5/min
RegistroThrottle                → 10/hour
EmailVerificacaoThrottle        → 3/hour
SolicitacaoAmizadeThrottle      → 10/hour
CriacaoPlanosThrottle           → 30/day
MensagensThrottle               → 100/hour
BuscaThrottle                   → 100/hour (anônimo)
BuscaAutenticadoThrottle        → 500/hour (autenticado)
```

#### Sistema de Auditoria (apps/core/models.py)
`LogAuditoria`:
- Rastreia: tipo_acao, usuario, ip, user_agent, resultado, endpoint
- Indexado por: timestamp, usuario_email, tipo_acao, ip_address
- Admin integrado com filtros e busca

`TentativaLoginFalhado`:
- Rastreia tentativas falhadas para detecção de força bruta
- Motivos: usuario_nao_existe, senha_incorreta, email_nao_verificado, etc
- Método: `contar_tentativas_recentes(email_ou_ip, minutos=60)`

---

### 🔐 CONFIGURAÇÕES - Atualizadas

#### settings.py
```python
# CORS - Agora configurado
CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://localhost:8000', ...]
CORS_ALLOW_CREDENTIALS = True

# Rate Limiting - Expandido
'DEFAULT_THROTTLE_RATES': {
    'login': '5/min',
    'registro': '10/hour',
    'email_verificacao': '3/hour',
    'solicitacao_amizade': '10/hour',
    'criacao_planos': '30/day',
    'mensagens': '100/hour',
    'busca': '100/hour',
    'busca_autenticado': '500/hour',
}

# CSP - Mantido em settings (removido Middleware)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://api.mapbox.com")
# ...
```

---

### 📝 MIGRAÇÕES

#### Novos Modelos Criados
- ✅ `apps/core/migrations/000X_initial.py` → LogAuditoria + TentativaLoginFalhado
- Status: Aplicadas ao banco de dados ✅

---

## 📋 CHECKLIST PÓS-LIMPEZA

### Antes de Deployar em Produção

- [ ] Definir variáveis de ambiente:
  ```bash
  CORS_ALLOWED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
  SECRET_KEY=seu-secret-key-super-seguro
  DEBUG=False
  ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
  ```

- [ ] Testar endpoints críticos:
  - [ ] POST /usuarios/api/usuarios/registrar/ (rate limited)
  - [ ] POST /api-token-auth/token/ (rate limited)
  - [ ] GET /destinos/api/planos/ (otimizado, sem N+1)
  - [ ] GET /usuarios/api/usuarios/ (filtros funcionais)

- [ ] Verificar logs de auditoria:
  - [ ] Acessar admin: /admin/core/logauditoria/
  - [ ] Confirmar que ações sensíveis estão sendo registradas

- [ ] Remover APIs legacy:
  - [ ] Avisar clientes sobre HTTP 410 Gone
  - [ ] Documentar migração para novos endpoints

- [ ] Testes de segurança:
  - [ ] Testar força bruta no login (deve bloquear após 5 tentativas)
  - [ ] Verificar rate limiting de registro
  - [ ] Confirmar CORS functioning (testes cross-origin)
  - [ ] Validar token JWT expiração

---

## 🔄 MIGRAÇÃO DE CÓDIGO PARA CLIENTES

### Para Clientes Usando API

**Antes:**
```bash
GET /api/paises/autocomplete/?q=brasil
GET /api/estatisticas/1/
```

**Depois:**
```bash
GET /destinos/api/paises/?search=brasil
GET /destinos/api/planos/?pais_destino=1
```

**Respostas de Deprecation (HTTP 410):**
```json
{
  "erro": "Esta API foi descontinuada.",
  "mensagem": "Use o novo endpoint: GET /destinos/api/paises/?search=<termo>",
  "novo_endpoint": "/destinos/api/paises/?search="
}
```

---

## 📚 DOCUMENTAÇÃO ATUALIZADA

- ✅ API_DOCUMENTATION.md - Senhas removidas
- ✅ QUICK_REFERENCE.md - Senhas removidas
- ✅ Novo: apps/core/throttles.py (docstrings completos)
- ✅ Novo: apps/core/models.py (docstrings + métodos auxiliares)

---

## 🚀 PRÓXIMOS PASSOS RECOMENDADOS

### Curto Prazo (Imediato)
1. Testar todas as rotas em desenvolvimento
2. Confirmar que o banco de dados tem migrações aplicadas
3. Verificar variáveis de ambiente `.env`

### Médio Prazo (Próxima Sprint)
1. Implementar dashboard de segurança (view dos logs de auditoria)
2. Criar alertas para atividades suspeitas (muitas tentativas de login, etc)
3. Adicionar 2FA (autenticação de dois fatores)
4. Testes automatizados para endpoints críticos

### Longo Prazo
1. Implementar cache (Redis) para rate limiting distribuído
2. Adicionar encryption de dados sensíveis em repouso
3. Implementar WAF (Web Application Firewall)
4. Auditoria de segurança profissional

---

## ⚠️ NOTAS IMPORTANTES

1. **Senhas em Variáveis de Ambiente:**
   - Use `.env` separado para produção
   - NUNCA commit `.env` no repositório
   - Adicione `.env` ao `.gitignore`

2. **Token JWT:** 
   - Experiência: 60 minutos
   - Refresh: 7 dias
   - Certifique-se de usar HTTPS em produção

3. **Rate Limiting:**
   - Requer cache Django configurado
   - Em produção, use Redis em vez de cache local
   - Monitore logs para padrões de abuso

4. **Auditoria:**
   - Logs nunca são automaticamente deletados
   - Para manter DB limpo, implemente cleanup policy
   - Considere arquivamento em banco de dados separado

---

**Versão:** Refatoração Completa
**Data:** Março 2026
**Status:** ✅ Pronto para Produção (com configuração adequada)
