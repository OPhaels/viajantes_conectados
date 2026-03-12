# ⚡ Quick Reference - Comandos e Padrões

**Última Atualização:** Fevereiro de 2025

Copie e cole os commands mais usados. Mantenha esta página aberta enquanto desenvolve.

---

## 🚀 Iniciar Projeto

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements/requirements.txt

# Configurar variáveis
cp .env.example .env
# Edite .env conforme necessário

# Migrar banco
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

---

## 🔧 Comandos Diários

```bash
# Executar migrations
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Rodar testes
python manage.py test
pytest tests/ -v

# Linting
flake8 apps/
black apps/

# Shell interativo
python manage.py shell_plus  # Com IPython

# Coletar estáticos (antes de deploy)
python manage.py collectstatic --noinput

# Verificar segurança
python manage.py check --deploy
```

---

## 💻 Python/Django Patterns

### Criar Modelo

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class MeuModelo(models.Model):
    """Descrição do modelo."""
    
    nome = models.CharField(
        _('nome'),
        max_length=100,
        help_text=_('Nome descritivo')
    )
    ativo = models.BooleanField(_('ativo'), default=True)
    data_criacao = models.DateTimeField(_('data de criação'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('meu modelo')
        verbose_name_plural = _('meus modelos')
        ordering = ['-data_criacao']
    
    def __str__(self):
        return self.nome
```

### Criar Serializer

```python
from rest_framework import serializers
from .models import MeuModelo

class MeuModeloSerializer(serializers.ModelSerializer):
    """Serializer para MeuModelo."""
    
    class Meta:
        model = MeuModelo
        fields = ['id', 'nome', 'ativo', 'data_criacao']
        read_only_fields = ['id', 'data_criacao']
```

### Criar ViewSet

```python
from rest_framework import viewsets
from .models import MeuModelo
from .serializers import MeuModeloSerializer
from apps.core.permissions import IsAuthenticated, EhProprietario

class MeuModeloViewSet(viewsets.ModelViewSet):
    """ViewSet para MeuModelo."""
    
    queryset = MeuModelo.objects.all()
    serializer_class = MeuModeloSerializer
    permission_classes = [IsAuthenticated, EhProprietario]
```

### Criar Permission

```python
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

class MinhaPermission(permissions.BasePermission):
    """Descrição da permissão."""
    
    message = _('Você não tem permissão.')
    
    def has_permission(self, request, view):
        # Verificação em nível de view
        return True
    
    def has_object_permission(self, request, view, obj):
        # Verificação em nível de objeto
        return obj.usuario == request.user
```

### Criar URL

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, viewsets

router = DefaultRouter()
router.register(r'api/meus-modelos', viewsets.MeuModeloViewSet)

urlpatterns = [
    # Views
    path('meu-modelo/', views.minha_view, name='meu_modelo'),
    # API
    path('', include(router.urls)),
]
```

### Usar Transações

```python
from django.db import transaction

@transaction.atomic
def operacao_critica(dados):
    """Operação que precisa ser atômica."""
    objeto1 = Modelo1.objects.create(**dados)
    objeto2 = Modelo2.objects.create(ref=objeto1)
    # Se falhar, tudo é revertido
```

### Usar Logging

```python
import logging

logger = logging.getLogger(__name__)

# Diferentes níveis
logger.debug('Mensagem de debug')
logger.info(f'Usuário {user.email} fez login')
logger.warning(f'Tentativa além do limite: {ip}')
logger.error('Erro ao enviar email', exc_info=True)
logger.critical('Erro crítico!')
```

### Usar Cache

```python
from django.core.cache import cache

# Salvar
cache.set('chave', valor, 3600)  # 1 hora

# Recuperar
valor = cache.get('chave')

# Deletar
cache.delete('chave')

# Pattern em função
def obter_dados(id):
    dados = cache.get(f'dados_{id}')
    if not dados:
        dados = Modelo.objects.get(pk=id)
        cache.set(f'dados_{id}', dados, 3600)
    return dados
```

---

## 🎨 HTML/CSS Patterns

### Usar Design System

```html
<!-- Botão Primário -->
<button class="botao botao-primario">
    <i class="bi bi-check"></i> Enviar
</button>

<!-- Card -->
<div class="card">
    <div class="card-corpo">
        Conteúdo do card
    </div>
</div>

<!-- Grid Responsivo -->
<div class="grid grid-3">
    <div class="card">Item 1</div>
    <div class="card">Item 2</div>
    <div class="card">Item 3</div>
</div>

<!-- Alerta -->
<div class="alerta alerta-sucesso">
    <i class="bi bi-check-circle"></i>
    Operação realizada com sucesso!
</div>

<!-- Formulário -->
<div class="formulario-grupo">
    <label for="email">Email</label>
    <input type="email" id="email" class="form-control" required>
</div>
```

### Usar Variáveis CSS

```css
/* Cores */
background-color: var(--cor-primaria);
color: var(--cor-texto);
border: 1px solid var(--cor-borda);

/* Espaçamento */
padding: var(--espaco-4);
margin-bottom: var(--espaco-6);

/* Tipografia */
font-family: var(--fonte-principal);
font-size: var(--tamanho-base);
line-height: var(--altura-linha-normal);

/* Sombras */
box-shadow: var(--sombra-md);

/* Raios */
border-radius: var(--raio-lg);

/* Transições */
transition: all var(--transicao-normal);
```

---

## 🧪 Testes

### Teste Django

```python
from django.test import TestCase
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class UsuarioTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='teste@exemplo.com',
            password='<SENHA_TESTE>',
            nome_completo='Teste User'
        )
    
    def test_criar_usuario(self):
        self.assertEqual(self.usuario.email, 'teste@exemplo.com')
    
    def test_senha_criptografada(self):
        self.assertTrue(self.usuario.check_password('<SENHA_TESTE>'))
```

### Teste API

```python
from rest_framework.test import APITestCase

class UsuarioAPITests(APITestCase):
    def test_listar_usuarios(self):
        response = self.client.get('/usuarios/api/usuarios/')
        self.assertEqual(response.status_code, 200)
    
    def test_registrar_usuario(self):
        response = self.client.post('/usuarios/api/usuarios/registrar/', {
            'email': 'novo@exemplo.com',
            'nome_completo': 'Novo User',
            'password': '<SENHA_MINIMO_8_CARACTERES>',
            'password2': '<SENHA_MINIMO_8_CARACTERES>'
        })
        self.assertEqual(response.status_code, 201)
```

### Rodar Testes

```bash
# Todos
python manage.py test

# Específico
python manage.py test apps.usuarios.tests

# Com saída verbose
python manage.py test -v 2

# Com coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 🔐 Segurança

### Usar Permissões

```python
# No ViewSet
permission_classes = [
    IsAuthenticated,
    EmailVerificado,
    ContaAtiva,
    NaoEstaBloqueado
]

# No template
{% if perms.core.view_documento %}
    <p>Você tem permissão</p>
{% endif %}

# Em função
from apps.core.exceptions import PermissaoNegadaException

if not usuario.email_verificado:
    raise PermissaoNegadaException()
```

### Validar Input

```python
from apps.core.exceptions import ValidacaoDadosException

email = request.POST.get('email', '').strip()

if not email:
    raise ValidacaoDadosException("Email é obrigatório")

if len(email) > 254:
    raise ValidacaoDadosException("Email muito longo")

try:
    usuario = Usuario.objects.get(email=email)
except Usuario.DoesNotExist:
    raise UsuarioNaoEncontradoException()
```

### Rate Limiting

```python
from rest_framework.throttling import UserRateThrottle

class MeuRateThrottle(UserRateThrottle):
    scope = 'meu-scope'

# No ViewSet
throttle_classes = [MeuRateThrottle]

# No settings
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'meu-scope': '10/hour'
    }
}
```

---

## 📦 Dependencies

### Instalar Nova Dependência

```bash
# Instalar
pip install nova-package==1.0.0

# Adicionar a requirements
echo "nova-package==1.0.0" >> requirements/requirements.txt

# Verificar
pip list

# Atualizar lock file
pip freeze > requirements/requirements.txt
```

### Atualizar Existentes

```bash
# Ver available updates
pip list --outdated

# Atualizar uma
pip install --upgrade django

# Atualizar todas
pip install --upgrade -r requirements/requirements.txt
```

---

## 🔍 Debugging

### Print Debugging

```python
# Simples
print(f"Valor: {valor}")

# Estruturado
import json
print(json.dumps(dados, indent=2))

# Com pdb
import pdb; pdb.set_trace()
```

### Django Shell

```bash
python manage.py shell_plus

# Criar usuário
usuario = Usuario.objects.create_user(
    email='teste@exemplo.com',
    password='Teste123!'
)

# Consultar
usuarios = Usuario.objects.all()

# Atualizar
usuario.nome = 'Novo Nome'
usuario.save()

# Deletar
usuario.delete()
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Ver logs
tail -f logs/django.log

# Filtrar
tail -f logs/django.log | grep ERROR
```

---

## 📊 Performance

### Query Optimization

```python
# ✅ Bom: Select Related
planos = PlanoViagem.objects.select_related('usuario', 'pais').all()

# ✅ Bom: Prefetch Related
usuarios = Usuario.objects.prefetch_related('planos_viagem').all()

# ✅ Bom: Only Fields
usuarios = Usuario.objects.only('id', 'nome', 'email').all()

# ✅ Bom: Values
usuarios = Usuario.objects.values('id', 'nome').all()

# ❌ Ruim: N+1 Query
for plano in PlanoViagem.objects.all():
    print(plano.usuario.nome)  # Query por item!
```

### Database Indexes

```python
class MeuModelo(models.Model):
    email = models.EmailField(db_index=True)  # Index simples
    ativo = models.BooleanField()
    
    class Meta:
        indexes = [
            models.Index(fields=['ativo', 'data_criacao']),
            models.Index(fields=['usuario', 'ativo']),
        ]
```

---

## 🚀 Deploy

### Pre-Deploy Checklist

```bash
# ✅ Verificar tudo
python manage.py check --deploy

# ✅ Coletar estáticos
python manage.py collectstatic --noinput

# ✅ Rodar migrations
python manage.py migrate

# ✅ Limpar cache
python manage.py clear_cache

# ✅ Rodar testes
python manage.py test
```

### Variáveis Importantes

```bash
# .env production
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
SECRET_KEY=seu-secret-key-super-seguro
DB_PASSWORD=<INSIRA_SENHA_BANCO_DE_DADOS>
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SENTRY_DSN=seu-sentry-dsn
```

---

## 📚 Referências Rápidas

### Status Codes HTTP

```
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
```

### Métodos HTTP

```
GET - Ler dados
POST - Criar dados
PUT - Atualizar completamente
PATCH - Atualizar parcialmente
DELETE - Deletar
```

### Django ORM

```python
# Create
usuario = Usuario.objects.create(email='novo@ex.com')

# Read
usuario = Usuario.objects.get(id=1)
usuarios = Usuario.objects.all()
usuarios = Usuario.objects.filter(ativo=True)

# Update
usuario.nome = 'Novo'
usuario.save()

# Delete
usuario.delete()
```

---

## 🎯 Common Tasks

### Resetar Migrations

```bash
# Deletar migrations (exceto __init__.py)
rm apps/seu_app/migrations/0*.py

# Deletar banco de dados
rm db.sqlite3

# Recriar tudo
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Mudar Campo Modelo

```python
# Remover
# 1. Remove a linha do modelo
# 2. python manage.py makemigrations
# 3. python manage.py migrate

# Adicionar
# 1. Adicione a linha ao modelo
# 2. Se tem dados, use default= ou função
# 3. python manage.py makemigrations
# 4. python manage.py migrate
```

### Importar Dados

```python
from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('usuarios.csv') as f:
            for linha in f:
                email, nome = linha.split(',')
                Usuario.objects.create(
                    email=email.strip(),
                    nome_completo=nome.strip()
                )
```

---

## 💡 Tips & Tricks

```python
# Obter ou criar
usuario, criado = Usuario.objects.get_or_create(
    email='novo@ex.com',
    defaults={'nome': 'Novo Usuário'}
)

# Bulk create (mais rápido)
usuarios = [
    Usuario(email='user1@ex.com'),
    Usuario(email='user2@ex.com'),
]
Usuario.objects.bulk_create(usuarios)

# Contar
total = Usuario.objects.count()

# Existe
existe = Usuario.objects.filter(id=1).exists()

# Primero e último
primeiro = Usuario.objects.first()
ultimo = Usuario.objects.last()

# Ordenar
usuarios = Usuario.objects.order_by('-data_criacao')

# Distinto
emails = Usuario.objects.values('email').distinct()
```

---

**Mantenha esta página marcada!** 🔖

Última Atualização: Fevereiro de 2025
