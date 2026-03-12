# Guia de Testes das APIs REST - Viajantes Conectados

## 1. Autenticação JWT

### Obter Token
```bash
curl -X POST http://localhost:8000/api-token-auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "senha123"
  }'
```

**Resposta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Renovar Token
```bash
curl -X POST http://localhost:8000/api-token-auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "token_refresh_aqui"}'
```

---

## 2. APIs de Usuários

### Registrar Novo Usuário
```bash
curl -X POST http://localhost:8000/usuarios/api/usuarios/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novousuario@example.com",
    "nome_completo": "João Silva",
    "password": "senha123",
    "password2": "senha123",
    "data_nascimento": "1990-05-15",
    "telefone": "+5511999999999",
    "pais_residencia": "Brasil",
    "cidade_residencia": "São Paulo"
  }'
```

### Listar Usuários Públicos
```bash
curl -X GET "http://localhost:8000/usuarios/api/usuarios/?page=1&page_size=20" \
  -H "Authorization: Bearer {access_token}"
```

### Buscar Usuários
```bash
curl -X GET "http://localhost:8000/usuarios/api/usuarios/buscar/?q=joão&pais=brasil" \
  -H "Authorization: Bearer {access_token}"
```

### Obter Dados do Usuário Autenticado
```bash
curl -X GET http://localhost:8000/usuarios/api/usuarios/me/ \
  -H "Authorization: Bearer {access_token}"
```

### Atualizar Perfil
```bash
curl -X PUT http://localhost:8000/usuarios/api/usuarios/update_perfil/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "nome_completo": "João Silva Santos",
    "biografia": "Apaixonado por viagens!",
    "perfil_publico": true,
    "pais_residencia": "Portugal"
  }'
```

### Obter Perfil Público de Usuário
```bash
curl -X GET http://localhost:8000/usuarios/api/usuarios/{uuid}/ \
  -H "Authorization: Bearer {access_token}"
```

---

## 3. APIs de Planos de Viagem

### Criar Novo Plano
```bash
curl -X POST http://localhost:8000/destinos/api/planos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "pais_destino_id": 1,
    "cidade_destino": "Paris",
    "regiao_destino": "Île-de-France",
    "data_inicio": "2024-06-01",
    "data_fim": "2024-06-15",
    "flexibilidade_datas": false,
    "motivo_viagem": "turismo",
    "descricao": "Viajar a Paris com amigos",
    "nivel_privacidade": "publico",
    "orcamento_diario_min": "50.00",
    "orcamento_diario_max": "150.00"
  }'
```

### Listar Meus Planos
```bash
curl -X GET "http://localhost:8000/destinos/api/planos/meus/?page=1" \
  -H "Authorization: Bearer {access_token}"
```

### Buscar Planos (sem o próprio usuário)
```bash
curl -X GET "http://localhost:8000/destinos/api/planos/buscar/?pais=italia&data_inicio=2024-06-01&motivo_viagem=turismo" \
  -H "Authorization: Bearer {access_token}"
```

### Obter Detalhes do Plano
```bash
curl -X GET http://localhost:8000/destinos/api/planos/{uuid}/ \
  -H "Authorization: Bearer {access_token}"
```

### Atualizar Plano
```bash
curl -X PUT http://localhost:8000/destinos/api/planos/{uuid}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "descricao": "Viajar a Paris em junho",
    "nivel_privacidade": "amigos"
  }'
```

### Deletar Plano
```bash
curl -X DELETE http://localhost:8000/destinos/api/planos/{uuid}/ \
  -H "Authorization: Bearer {access_token}"
```

### Marcar Viagem como Concluída
```bash
curl -X POST http://localhost:8000/destinos/api/planos/{uuid}/marcar_concluida/ \
  -H "Authorization: Bearer {access_token}"
```

---

## 4. APIs de Países

### Listar Todos os Países
```bash
curl -X GET "http://localhost:8000/destinos/api/paises/?page=1" \
  -H "Authorization: Bearer {access_token}"
```

### Buscar Países (Autocomplete)
```bash
curl -X GET "http://localhost:8000/destinos/api/paises/search/?q=bra&limit=10" \
  -H "Authorization: Bearer {access_token}"
```

### Obter Detalhes do País
```bash
curl -X GET http://localhost:8000/destinos/api/paises/{id}/ \
  -H "Authorization: Bearer {access_token}"
```

---

## 5. Testes com Postman

### 1. Importar Collection
Abra Postman e importe esta collection JSON:

```json
{
  "info": {
    "name": "Viajantes Conectados API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Get Token",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api-token-auth/token/",
            "body": {
              "mode": "raw",
              "raw": "{\"email\": \"{{email}}\", \"password\": \"{{password}}\"}"
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000"},
    {"key": "access_token", "value": ""},
    {"key": "email", "value": "usuario@example.com"},
    {"key": "password", "value": "senha123"}
  ]
}
```

### 2. Configurar Variáveis
- `base_url`: http://localhost:8000
- `access_token`: Obtenha após autenticar
- Salve o token após login

### 3. Usar Authorization
Em cada requisição, vá para a aba "Authorization":
- Type: Bearer Token
- Token: {{access_token}}

---

## 6. Exemplos com Python

### Usar requests library

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Autenticar
response = requests.post(
    f"{BASE_URL}/api-token-auth/token/",
    json={
        "email": "usuario@example.com",
        "password": "senha123"
    }
)

token = response.json()["access"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Listar planos
response = requests.get(
    f"{BASE_URL}/destinos/api/planos/meus/",
    headers=headers
)

planos = response.json()
print(json.dumps(planos, indent=2))

# 3. Buscar planos (sem o próprio usuário)
response = requests.get(
    f"{BASE_URL}/destinos/api/planos/buscar/?pais=italia&motivo_viagem=turismo",
    headers=headers
)

print(response.json())

# 4. Buscar viajantes
response = requests.get(
    f"{BASE_URL}/usuarios/api/usuarios/buscar/?q=joão&pais=brasil",
    headers=headers
)

print(response.json())
```

---

## 7. Testes de Filtros

### Filtrar Planos por Período
```bash
curl -X GET "http://localhost:8000/destinos/api/planos/buscar/?data_inicio=2024-06-01&data_fim=2024-06-30" \
  -H "Authorization: Bearer {access_token}"
```

### Filtrar Planos por Motivo
```bash
curl -X GET "http://localhost:8000/destinos/api/planos/buscar/?motivo_viagem=trabalho" \
  -H "Authorization: Bearer {access_token}"
```

### Paginar Resultados
```bash
curl -X GET "http://localhost:8000/destinos/api/planos/?page=2&page_size=10" \
  -H "Authorization: Bearer {access_token}"
```

---

## 8. Tratamento de Erros

### Erro 401 - Não Autenticado
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Solução**: Adicione o header `Authorization: Bearer {token}`

### Erro 403 - Permissão Negada
```json
{
  "detail": "You do not have permission to perform this action."
}
```
**Solução**: Verifique se você é o proprietário do recurso

### Erro 404 - Não Encontrado
```json
{
  "detail": "Not found."
}
```
**Solução**: Verifique o UUID/ID do recurso

### Erro 400 - Dados Inválidos
```json
{
  "field_name": ["Este campo é obrigatório."]
}
```
**Solução**: Revise os dados enviados conforme o schema

---

## 9. Dicas de Debugging

### Ver Logs Django
```bash
python manage.py runserver --verbosity=3
```

### Acessar Console Django
```bash
python manage.py shell

>>> from apps.usuarios.models import Usuario
>>> Usuario.objects.all()
```

### Ver Queries SQL
```python
from django.db import connection
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def minha_view():
    # seu código aqui
    print(connection.queries)
```

---

## 10. Checklist de Testes

- [ ] Registrar novo usuário
- [ ] Autenticar com credenciais válidas
- [ ] Obter token JWT
- [ ] Renovar token
- [ ] Listar usuários públicos (sem o próprio)
- [ ] Buscar usuários por nome/país/cidade
- [ ] Obter perfil do usuário autenticado
- [ ] Atualizar perfil (nome, bio, foto)
- [ ] Criar novo plano de viagem
- [ ] Listar meus planos
- [ ] Buscar planos de viagem (sem os próprios)
- [ ] Filtrar por país, data, motivo
- [ ] Obter detalhes do plano
- [ ] Atualizar plano
- [ ] Marcar viagem como concluída
- [ ] Deletar plano
- [ ] Listar países
- [ ] Buscar países com autocomplete

---

