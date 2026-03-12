# Documentação da API - Viajantes Conectados

## 📋 Visão Geral

A API REST do Viajantes Conectados é uma plataforma para conectar viajantes que compartilham os mesmos destinos. Todos os endpoints requerem autenticação via JWT, exceto os de registro e login.

**URL Base:** `https://api.viajantesconectados.com/`  
**Versão:** 1.0  
**Formato de Resposta:** JSON

---

## 🔐 Autenticação

### Obter Token JWT

```http
POST /api-token-auth/token/
Content-Type: application/json

{
  "email": "usuario@exemplo.com",
  "password": "<INSIRA_SUA_SENHA>"
}
```

**Resposta (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Usar o Token

Inclua o token JWT no header `Authorization`:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Renovar Token

```http
POST /api-token-auth/refresh/
Content-Type: application/json

{
  "refresh": "seu_refresh_token"
}
```

---

## 👤 Endpoints de Usuários

### Registrar Novo Usuário

```http
POST /usuarios/api/usuarios/registrar/
Content-Type: application/json

{
  "email": "novo_usuario@exemplo.com",
  "nome_completo": "João Silva",
  "password": "<SENHA_MINIMO_8_CARACTERES>",
  "password2": "<SENHA_MINIMO_8_CARACTERES>",
  "data_nascimento": "1990-05-15",
  "telefone": "+5511999999999",
  "pais_residencia": "Brasil",
  "cidade_residencia": "São Paulo"
}
```

**Respostas:**
- `201 Created`: Usuário registrado com sucesso
- `400 Bad Request`: Dados inválidos

---

### Listar Usuários (Pública)

```http
GET /usuarios/api/usuarios/
Authorization: Bearer {token}
```

**Parâmetros de Query:**
- `search`: Buscar por nome ou país (ex: `?search=Brasil`)
- `pais_residencia`: Filtrar por país
- `page`: Número da página (paginação automática)

**Resposta (200 OK):**
```json
{
  "count": 150,
  "next": "https://api.viajantesconectados.com/usuarios/api/usuarios/?page=2",
  "previous": null,
  "results": [
    {
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "nome_completo": "Maria Santos",
      "foto_perfil": "https://cdn.site.com/fotos/maria.jpg",
      "pais_residencia": "Brasil",
      "cidade_residencia": "Rio de Janeiro",
      "biografia": "Mochileira apaixonada por viagens!"
    }
  ]
}
```

---

### Obter Dados do Usuário Autenticado

```http
GET /usuarios/api/usuarios/me/
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@exemplo.com",
  "nome_completo": "João Silva",
  "data_nascimento": "1990-05-15",
  "telefone": "+5511999999999",
  "pais_residencia": "Brasil",
  "cidade_residencia": "São Paulo",
  "biografia": "Apaixonado por viagens e novas culturas",
  "foto_perfil": "https://cdn.site.com/fotos/joao.jpg",
  "perfil_publico": true,
  "mostrar_email": false,
  "mostrar_telefone": false,
  "email_verificado": true,
  "ativo": true,
  "data_criacao": "2024-01-15T10:30:00Z",
  "ultimo_acesso": "2025-02-10T14:25:00Z"
}
```

---

### Atualizar Perfil do Usuário

```http
PUT /usuarios/api/usuarios/me/
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome_completo": "João Silva Santos",
  "biografia": "Viajante profissional",
  "pais_residencia": "Portugal",
  "perfil_publico": true
}
```

**Resposta (200 OK):** Dados atualizados

---

### Obter Perfil Público de um Usuário

```http
GET /usuarios/api/usuarios/{uuid}/perfil/
Authorization: Bearer {token}
```

**Respostas:**
- `200 OK`: Perfil encontrado
- `403 Forbidden`: Perfil é privado
- `404 Not Found`: Usuário não encontrado

---

## 🌍 Endpoints de Destinos

### Listar Países

```http
GET /destinos/api/paises/
```

**Parâmetros de Query:**
- `search`: Buscar por nome ou continente
- `ativo`: Filtrar apenas países ativos (`?ativo=true`)
- `continente`: Filtrar por continente

**Resposta (200 OK):**
```json
{
  "count": 195,
  "results": [
    {
      "id": 1,
      "codigo_iso": "BR",
      "nome": "Brasil",
      "nome_completo": "República Federativa do Brasil",
      "continente": "América do Sul",
      "latitude": "-14.2350",
      "longitude": "-51.9253",
      "imagem": "https://cdn.site.com/paises/brasil.jpg",
      "ativo": true
    }
  ]
}
```

---

### Criar Plano de Viagem

```http
POST /destinos/api/planos/
Authorization: Bearer {token}
Content-Type: application/json

{
  "pais_destino_id": 1,
  "cidade_destino": "Rio de Janeiro",
  "regiao_destino": "Sudeste",
  "data_inicio": "2025-06-01",
  "data_fim": "2025-06-15",
  "flexibilidade_datas": true,
  "motivo_viagem": "turismo",
  "descricao": "Férias na praia e visitação de pontos turísticos",
  "nivel_privacidade": "publico",
  "orcamento_diario_min": 50,
  "orcamento_diario_max": 150
}
```

**Resposta (201 Created):**
```json
{
  "uuid": "660f8401-f30c-41d4-b817-556755551111",
  "usuario": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "nome_completo": "João Silva"
  },
  "pais_destino": {
    "id": 1,
    "nome": "Brasil"
  },
  "cidade_destino": "Rio de Janeiro",
  "data_inicio": "2025-06-01",
  "data_fim": "2025-06-15",
  "duracao_dias": 14,
  "status": "ativo"
}
```

---

### Listar Planos de Viagem (Meus Planos)

```http
GET /destinos/api/planos/?usuario_id=me
Authorization: Bearer {token}
```

**Resposta (200 OK):** Lista de planos do usuário autenticado

---

### Buscar Viajantes com Planos Similares

```http
GET /destinos/api/planos/?pais_destino=1&data_inicio__gte=2025-06-01
Authorization: Bearer {token}
```

---

### Obter Detalhes de um Plano

```http
GET /destinos/api/planos/{uuid}/
Authorization: Bearer {token}
```

---

## 🤝 Endpoints de Conexões

### Enviar Solicitação de Amizade

```http
POST /conexoes/enviar-solicitacao/{uuid_usuario}/
Authorization: Bearer {token}
Content-Type: application/x-www-form-urlencoded

mensagem=Gostaria de compartilhar as experiências de viagem!
```

**Respostas:**
- `302 Found`: Redirecionado (sucesso)
- `403 Forbidden`: Você já é amigo ou já existe solicitação
- `429 Too Many Requests`: Limite de solicitações atingido

---

### Listar Solicitações de Amizade

```http
GET /conexoes/solicitacoes/
Authorization: Bearer {token}
```

**Resposta (200 OK):** Página HTML com solicitações pendentes

---

### Responder Solicitação de Amizade

```http
POST /conexoes/responder-solicitacao/{uuid_solicitacao}/{acao}/
Authorization: Bearer {token}
```

**Valores de {acao}:**
- `aceitar` - Aceita a solicitação
- `recusar` - Recusa a solicitação

---

### Listar Amigos

```http
GET /conexoes/amigos/
Authorization: Bearer {token}
```

---

## 💬 Endpoints de Chat

### Listar Conversas

```http
GET /chat/conversas/
Authorization: Bearer {token}
```

---

### Obter Conversa com um Usuário

```http
GET /chat/conversa/{uuid_conversa}/
Authorization: Bearer {token}
```

---

### Iniciar Conversa

```http
POST /chat/iniciar/{uuid_usuario}/
Authorization: Bearer {token}
```

---

## 📊 Códigos de Status HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 204 | No Content - Sucesso, sem conteúdo na resposta |
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Autenticação necessária |
| 403 | Forbidden - Acesso negado |
| 404 | Not Found - Recurso não encontrado |
| 409 | Conflict - Violação de unicidade |
| 422 | Unprocessable Entity - Erro de validação |
| 429 | Too Many Requests - Limite de taxa excedido |
| 500 | Internal Server Error - Erro do servidor |

---

## 🔒 Segurança

### Validações Implementadas

- ✅ Autenticação JWT com expiração
- ✅ CSRF Protection em formulários
- ✅ Rate Limiting (máx 10 solicitações/hora por IP)
- ✅ Validação de email para operações sensíveis
- ✅ Criptografia de senhas com Argon2
- ✅ HTTPS obrigatório em produção
- ✅ Controle de Acesso Baseado em Papéis (RBAC)

### Boas Práticas

1. **Nunca exponha dados sensíveis** na API pública
2. **Use HTTPS** em todos os ambientes
3. **Valide** todos os dados de entrada
4. **Rate limit** para prevenir abuso
5. **Mantenha tokens** confidenciais
6. **Log** de todas as operações sensíveis

---

## 📝 Exemplos Completos

### Fluxo Completo de Registro e Busca

```bash
# 1. Registrar novo usuário
curl -X POST https://api.site.com/usuarios/api/usuarios/registrar/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novo@exemplo.com",
    "nome_completo": "Maria Silva",
    "password": "<SENHA_MINIMO_8_CARACTERES>",
    "password2": "<SENHA_MINIMO_8_CARACTERES>"
  }'

# 2. Fazer login
curl -X POST https://api.site.com/api-token-auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novo@exemplo.com",
    "password": "SenhaForte123!"
  }'

# 3. Usar o token para buscar usuários
curl -X GET "https://api.site.com/usuarios/api/usuarios/?search=Brasil" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# 4. Enviar solicitação de amizade
curl -X POST https://api.site.com/conexoes/enviar-solicitacao/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d "mensagem=Vamos viajar juntos!"
```

---

## 🐛 Tratamento de Erros

Toda resposta de erro segue este padrão:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados fornecidos são inválidos",
    "details": {
      "email": ["Um usuário com este email já existe"],
      "password": ["As senhas não correspondem"]
    }
  }
}
```

---

## 📞 Suporte

Para dúvidas ou reportar bugs:
- Email: support@viajantesconectados.com
- Issue Tracker: https://github.com/seu-repo/issues

---

**Última Atualização:** Fevereiro de 2025
