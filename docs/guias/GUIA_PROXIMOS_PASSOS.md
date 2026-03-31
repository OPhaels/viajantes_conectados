# 🚀 GUIA PRÁTICO - Próximos Passos

## Status Atual
✅ **Código Limpo e Validado** | Sistema Django funcional | Pronto para continuação

---

## 1️⃣ ANTES DE TUDO - Configuração Inicial

### 1.1 Criar arquivo `.env` na raiz do projeto
```bash
# Arquivo: .env
SECRET_KEY=django-insecure-sua-chave-super-secreta-aqui-min-50-caracteres
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,seu-dominio.com

# Database
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# CORS - URLs permitidas
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://seu-dominio.com

# Email (se configurar)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app

# Mapbox (para mapa)
MAPBOX_TOKEN=seu-token-mapbox-aqui

# Sentry (opcional, para produção)
SENTRY_DSN=

# Redis (opcional, para cache em produção)
REDIS_URL=redis://localhost:6379/0
```

**⚠️ IMPORTANTE:** Adicione `.env` ao `.gitignore`:
```bash
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
echo "__pycache__/" >> .gitignore
```

---

## 2️⃣ INICIAR SERVIDOR DE DESENVOLVIMENTO

### 2.1 Ativar Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2.2 Rodar Migrações
```bash
python manage.py migrate
```

### 2.3 Criar Superusuário (Administrador)
```bash
python manage.py createsuperuser
# Email: admin@example.com
# Senha: (criar uma forte)
```

### 2.4 Iniciar Servidor
```bash
python manage.py runserver
```

**URLs:**
- 🏠 Home: http://localhost:8000/
- 🔧 Admin: http://localhost:8000/admin/
- 📚 API: http://localhost:8000/api/

---

## 3️⃣ TESTAR FUNCIONALIDADES CRÍTICAS

### 3.1 Testar Autenticação JWT

**Terminal 1 - Obter Token:**
```bash
curl -X POST http://localhost:8000/api-token-auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "sua-senha"}'

# Resposta:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
# }
```

**Terminal 2 - Usar Token em Requisição Autenticada:**
```bash
curl -X GET http://localhost:8000/usuarios/api/usuarios/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 3.2 Testar Rate Limiting (Login)

Execute 6 tentativas rápidas de login falhado:
```bash
for i in {1..6}; do
  curl -X POST http://localhost:8000/api-token-auth/token/ \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "senha-errada"}'
  echo "Tentativa $i"
done
```

**Esperado:** A 6ª tentativa deve retornar HTTP 429 (Too Many Requests)

### 3.3 Testar Auditoria

1. Acesse http://localhost:8000/admin/
2. Vá para "Core" → "Logs de auditoria"
3. Deve ver registros das tentativas de login

### 3.4 Testar CORS (Cross-Origin)

Crie um arquivo `test_cors.html` e abra no navegador:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Teste CORS</title>
</head>
<body>
    <button onclick="testCORS()">Testar CORS</button>
    <pre id="resultado"></pre>

    <script>
        function testCORS() {
            fetch('http://localhost:8000/usuarios/api/usuarios/', {
                credentials: 'include',
                headers: {
                    'Authorization': 'Bearer SEU_TOKEN_AQUI'
                }
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('resultado').textContent =
                    JSON.stringify(data, null, 2);
            })
            .catch(e => {
                document.getElementById('resultado').textContent = 'Erro: ' + e;
            });
        }
    </script>
</body>
</html>
```

---

## 4️⃣ PRÓXIMAS IMPLEMENTAÇÕES

### 4.1 Adicionar Endpoints Funcionais

Os seguintes endpoints já existem mas podem ser testados:
- ✅ `POST /usuarios/api/usuarios/registrar/` - Registrar novo usuário
- ✅ `GET /destinos/api/paises/?search=brasil` - Buscar países
- ✅ `GET /destinos/api/planos/` - Listar planos de viagem
- ✅ `POST /destinos/api/planos/` - Criar novo plano

### 4.2 Melhorar Templates HTML

Os templates em `templates/` podem ser atualizados para usar CSS novo em `static/css/style.css`:
```html
<!-- NOVO: CSS Responsivo -->
<link rel="stylesheet" href="{% static 'css/style.css' %}">

<!-- USAR CLASSES -->
<div class="container mt-lg">
  <h1>Meu Título</h1>
  <button class="btn btn-primary">Clique aqui</button>
  <div class="grid-3">
    <!-- Cards responsivos -->
  </div>
</div>
```

### 4.3 Implementar Frontend React/Vue

Para integração com frontend separado:
```javascript
// .env frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ORIGIN=http://localhost:3000
```

O CORS já está configurado para aceitar requisições de `http://localhost:3000`.

---

## 5️⃣ SEGURANÇA EM PRODUÇÃO

### 5.1 Checklist Antes de Deploy

```bash
# 1. Executar validação
python manage.py check --deploy

# 2. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 3. Verificar migrações pendentes
python manage.py makemigrations --check

# 4. Criar backup do BD
cp db.sqlite3 db.sqlite3.backup-$(date +%Y%m%d)

# 5. Testar com DEBUG=False localmente
DEBUG=False python manage.py runserver
```

### 5.2 Variáveis de Ambiente Obrigatórias

Em produção, certifique-se de que estão definidas:
```bash
# Geral
SECRET_KEY=<gere com python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Segurança
SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True

# Database (considere usar PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=viajantes_db
DB_USER=viajantes_user
DB_PASSWORD=<gere-senha-forte>
DB_HOST=localhost
DB_PORT=5432

# Cache/Rate Limiting (use Redis em produção)
REDIS_URL=redis://usuario:senha@localhost:6379/0
```

### 5.3 HTTPS Obrigatório

```python
# settings.py (já configurado para não-DEBUG)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

---

## 6️⃣ ACOMPANHAMENTO E MONITORAMENTO

### 6.1 Ver Logs de Auditoria

```bash
# Django Admin
http://localhost:8000/admin/core/logauditoria/

# Filtros disponíveis:
# - Tipo de ação (login, registro, erro, etc)
# - Resultado (sucesso/falha)
# - Data
# - Requer investigação (flag para atividades suspeitas)
```

### 6.2 Contar Tentativas Falhadas de Login

```python
# Terminal Python
python manage.py shell

from apps.core.models import TentativaLoginFalhado

# Tentativas no último minuto
TentativaLoginFalhado.contar_tentativas_recentes('192.168.1.1', minutos=1)

# Tentativas por email
TentativaLoginFalhado.contar_tentativas_recentes('usuario@email.com', minutos=60)
```

### 6.3 Monitorar Performance

```bash
# Ver quantidade de queries (adicione Debug Toolbar)
pip install django-debug-toolbar

# Então veja o tempo de cada requisição
# http://localhost:8000/?__debug__=True
```

---

## 7️⃣ ARQUIVOS IMPORTANTES PARA CONSULTA

| Arquivo | Propósito | Leia Primeiro |
|---------|-----------|---------------|
| [CHANGELOG_LIMPEZA.md](CHANGELOG_LIMPEZA.md) | Detalhes técnicos da limpeza | ⭐⭐⭐ |
| [RESUMO_EXECUCAO.md](RESUMO_EXECUCAO.md) | Resumo executivo | ⭐⭐ |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Endpoints da API | ⭐⭐⭐ |
| [README.md](README.md) | Introdução ao projeto | ⭐ |
| `apps/core/models.py` | Auditoria e tentativas login | ⭐⭐ |
| `apps/core/throttles.py` | Rate limiting | ⭐⭐ |
| `apps/core/utils.py` | Funções auxiliares | ⭐ |
| `config/settings.py` | Configurações Django | ⭐⭐ |
| `static/css/style.css` | CSS responsivo | ⭐ |

---

## 8️⃣ DÚVIDAS FREQUENTES

### P: Como resetar rate limiting de um usuário?
```python
from django.utils import timezone
from apps.core.models import TentativaLoginFalhado

# Deletar tentativas recentes de um email
TentativaLoginFalhado.objects.filter(
    email_tentativa='usuario@email.com'
).delete()
```

### P: Como gerar token de teste para um usuário?
```python
from rest_framework_simplejwt.tokens import RefreshToken
from apps.usuarios.models import Usuario

user = Usuario.objects.get(email='admin@example.com')
refresh = RefreshToken.for_user(user)
print(f"Access: {refresh.access_token}")
print(f"Refresh: {refresh}")
```

### P: Como registrar uma ação manual na auditoria?
```python
from apps.core.models import LogAuditoria

LogAuditoria.registrar_acao(
    tipo_acao='criar_plano_viagem',
    usuario=user,
    request=request,  # Objeto da requisição Django
    resultado=True,
    descricao='Plano para Brasil criado manualmente',
    dados_alterados={'pais': 'Brasil', 'datas': '2026-01-01 a 2026-01-31'}
)
```

### P: Como habilitar modo dark automaticamente?
O CSS já suporta:
```css
@media (prefers-color-scheme: dark) {
    /* Cores automáticas para tema escuro */
}
```

Isso segue a preferência do SO do usuário.

---

## 9️⃣ COMANDOS ÚTEIS

```bash
# Verificar banco de dados
python manage.py dbshell

# Executar testes
python manage.py test

# Criar nova migração
python manage.py makemigrations app_name

# Aplicar migrações
python manage.py migrate

# Ver modelos de um app
python manage.py show_migrations app_name

# Shell interativo Django
python manage.py shell

# Rolar dados de teste
python manage.py loaddata fixture.json

# Dumpar dados
python manage.py dumpdata > dados_backup.json
```

---

## 🔟 CONTATO

Se tiver dúvidas sobre as mudanças realizadas, consulte:
1. ✅ [CHANGELOG_LIMPEZA.md](CHANGELOG_LIMPEZA.md) - Documentação técnica
2. ✅ Docstrings dos arquivos novos
3. ✅ Admin Django para ver logs de auditoria
4. ✅ Comandos `python manage.py shell` para testes rápidos

---

**Status:** ✅ Código Pronto | 🚀 Pronto para Deployment | 🔒 Seguro

**Última atualização:** Março 2026
