# 🔐 Guia de Segurança - Viajantes Conectados

**Última Atualização:** Fevereiro de 2025

Este documento descreve as políticas de segurança e boas práticas para o Viajantes Conectados.

---

## 📋 Índice

1. [Segurança Implementada](#segurança-implementada)
2. [Relatar Vulnerabilidades](#relatar-vulnerabilidades)
3. [Boas Práticas para Desenvolvedores](#boas-práticas-para-desenvolvedores)
4. [Checklist de Deploy](#checklist-de-deploy)
5. [Políticas de Dados](#políticas-de-dados)

---

## 🛡️ Segurança Implementada

### 1. Autenticação e Autorização

#### JWT (JSON Web Tokens)
```python
# Token com expiração de 60 minutos
ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)

# Refresh token válido por 7 dias
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

# Rotação automática de tokens
ROTATE_REFRESH_TOKENS = True
```

**Como usar:**
```bash
# Obter token
curl -X POST http://localhost:8000/api-token-auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha123"}'

# Resposta
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Usar token
curl http://localhost:8000/api/usuarios/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### Email Verification
- Toda ação sensível requer email verificado
- Implementado via `EmailVerificado` permission
- Email de confirmação enviado no registro

#### Proteção contra Força Bruta
```python
# Bloqueio após 5 tentativas falhadas
tentativas_login_falhas >= 5
bloqueado_ate = timezone.now() + timedelta(minutes=30)
```

### 2. Validação de Dados

#### Senhas
```
✅ Mínimo 8 caracteres
✅ Pelo menos 1 letra maiúscula
✅ Pelo menos 1 número
✅ Pelo menos 1 caractere especial (!@#$%^&*)
✅ Criptografia com Argon2
```

#### Emails
```python
✅ Validação de formato RFC 5322
✅ Unicidade no banco de dados
✅ Verificação obrigatória
```

#### Telefones
```regex
✅ Regex: ^\+?1?\d{9,15}$
✅ Suporta formato internacional
✅ Opcional para usuários
```

### 3. Rate Limiting

```python
# Requisições anônimas
AnonRateThrottle: 100 requests/hora/IP

# Requisições autenticadas
UserRateThrottle: 1000 requests/hora/user

# Solicitações de amizade
MaxRequestsPerHour: 10 solicitações/hora
```

### 4. CSRF Protection

```python
# Habilitado globalmente
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
]

# Token obrigatório em POST/PUT/DELETE
{% csrf_token %}
```

### 5. Headers de Segurança

```python
# HTTPS obrigatório em produção
SECURE_SSL_REDIRECT = True

# Cookies seguros
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# HSTS (1 ano)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Anti-clickjacking
X_FRAME_OPTIONS = 'DENY'

# Anti-MIME type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True
```

### 6. Content Security Policy

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:", "blob:")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'", "wss:", "https://api.mapbox.com")
```

### 7. Logging de Operações Sensíveis

```python
# Login
logger.info(f'Login bem-sucedido: {usuario.email}')

# Solicitação de amizade
logger.info(f'Solicitação enviada: {remetente.email} → {destinatario.email}')

# Alteração de senha
logger.info(f'Senha alterada: {usuario.email}')

# Erro de autenticação
logger.warning(f'Login falhou: {email} - Tentativa inválida')
```

### 8. Monitoramento com Sentry

```python
# Em produção
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% das transações
    send_default_pii=False,   # Não enviar PII
)
```

---

## 🚨 Relatar Vulnerabilidades

### Processo de Divulgação Responsável

Se você descobrir uma vulnerabilidade:

1. **NÃO** publique em issues público
2. **NÃO** faça spam ao reportar
3. **ENVIE** email para: `security@viajantesconectados.com`

**Inclua:**
- Descrição detalhada da vulnerabilidade
- Passos para reproduzir
- Impacto potencial
- Versão afetada

**Timeline:**
- ⏱️ Você tem 90 dias para reportar
- ⏱️ Temos 30 dias para responder
- ⏱️ Temos 60 dias para corrigir
- ⏱️ Divulgação pública após 90 dias

---

## 👨‍💻 Boas Práticas para Desenvolvedores

### 1. Usar Permissões Reutilizáveis

❌ **NÃO faça:**
```python
@login_required
def minha_view(request):
    if not request.user.email_verificado:
        return HttpResponseForbidden()
    # ...
```

✅ **FAÇA:**
```python
from apps.core.permissions import EmailVerificado
from rest_framework.permissions import IsAuthenticated

class MeuViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EmailVerificado]
```

### 2. Validar TODOS os Inputs

❌ **NÃO faça:**
```python
def criar_plano(request):
    orçamento_min = request.POST['orçamento_min']  # Pode lançar KeyError
    # ...
```

✅ **FAÇA:**
```python
def criar_plano(request):
    try:
        orçamento_min = float(request.POST.get('orçamento_min', 0))
        if orçamento_min < 0:
            raise ValueError("Orçamento não pode ser negativo")
    except (ValueError, TypeError):
        messages.error(request, "Orçamento inválido")
        return redirect('destinos:criar_plano')
```

### 3. Usar Exceções Customizadas

❌ **NÃO faça:**
```python
if not usuario.existe:
    raise Exception("Usuário não encontrado")
```

✅ **FAÇA:**
```python
from apps.core.exceptions import UsuarioNaoEncontradoException

if not usuario.existe:
    raise UsuarioNaoEncontradoException()
```

### 4. Logar Operações Sensíveis

```python
import logging

logger = logging.getLogger(__name__)

# Login
logger.info(f'Login bem-sucedido: {usuario.email} de {request.META.get("REMOTE_ADDR")}')

# Erro
logger.error(f'Erro crítico em criar_plano: {str(erro)}', exc_info=True)

# Aviso
logger.warning(f'Múltiplas tentativas de login falhadas: {email}')
```

### 5. Nunca Exponha Informações Sensíveis

```python
# Nunca no response:
❌ senha, email (se privado), token de autenticação, chaves API

# Seguro retornar:
✅ uuid, nome público, foto pública, biografia pública
```

### 6. Usar Transactions para Operações Críticas

```python
from django.db import transaction

@transaction.atomic
def processar_solicitacao_amizade(remetente, destinatario):
    # Se algo falhar, tudo é revertido
    solicitacao = SolicitacaoAmizade.objects.create(...)
    # Enviar email
    # Etc.
```

### 7. Implementar Soft Delete

```python
# Nunca delete registros de usuários críticos
# Use soft delete:

class Usuario(models.Model):
    ativo = models.BooleanField(default=True)

# No queryset:
usuarios_ativos = Usuario.objects.filter(ativo=True)
```

### 8. Sanitizar HTML/Markdown

```python
from django.utils.html import escape
from markdownx.utils import markdownify

# Se aceitar markdown do usuário:
conteudo_seguro = markdownify(user_input)

# Se aceitar HTML:
conteudo_seguro = escape(user_input)
```

---

## ✅ Checklist de Deploy

### Antes de Publicar em Produção

```python
# 1. Verificar configurações de segurança
python manage.py check --deploy

# 2. Desabilitar debug
DEBUG = False

# 3. Configurar ALLOWED_HOSTS
ALLOWED_HOSTS = ['seu-dominio.com', 'www.seu-dominio.com']

# 4. Gerar novo SECRET_KEY
# Nunca use o mesmo de desenvolvimento!

# 5. Configurar HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 6. Backends seguros
# Usar PostgreSQL (não SQLite)
# Usar Redis para cache/sessions
# Usar Sentry para erro tracking

# 7. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 8. Migrar banco de dados
python manage.py migrate

# 9. Criar superusuário
python manage.py createsuperuser

# 10. Testar endpoints crítico
pytest tests/
```

### Environment Variables Obrigatórios

```bash
✅ SECRET_KEY (único, gerado)
✅ DEBUG=False
✅ ALLOWED_HOSTS (seu domínio)
✅ DB_PASSWORD (senha forte)
✅ EMAIL_HOST_PASSWORD (credenciais SMTP)
✅ SENTRY_DSN (para monitoramento)
✅ MAPBOX_TOKEN (para mapa)
```

---

## 📊 Políticas de Dados

### Coleta de Dados

Coletamos apenas dados necessários para o funcionamento:
- Email (obrigatório, verificado)
- Nome completo
- Data de nascimento (opcional)
- Localização (opcional)

### Armazenamento

```python
✅ Senhas criptografadas com Argon2
✅ Dados em PostgreSQL seguro
✅ Backups diários criptografados
✅ Logs retidos por 30 dias
✅ Sem rastreamento de terceiros
```

### Acesso

```python
✅ Apenas admins podem acessar dados sensíveis
✅ Auditoria de acessos
✅ 2FA para contas admin (recomendado)
✅ Sem partilha de dados com terceiros
```

### Exclusão

```python
# Usuários podem solicitar exclusão de dados
# Processo de soft delete (não apagar, apenas desativar)
# Dados preservados por 30 dias antes de exclusão permanente
```

---

## 📞 Suporte de Segurança

- **Relatório de Vulnerabilidades:** security@viajantesconectados.com
- **Atualizações de Segurança:** Inscreva-se em releases
- **Dúvidas:** Abra uma issue privada no repositório

---

## 🔄 Atualizações de Segurança

Mantemos a segurança atualizada:

```bash
# Verificar pacotes desatualizados
pip list --outdated

# Atualizar Django
pip install --upgrade django

# Atualizar todas as dependências
pip install --upgrade -r requirements/requirements.txt
```

---

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/5.0/topics/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Segurança é responsabilidade de todos!**

Se tiver dúvidas sobre segurança, abra uma issue ou entre em contato.

---

Versão: 2.0  
Última Atualização: Fevereiro de 2025
