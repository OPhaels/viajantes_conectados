# 👨‍💻 Guia de Desenvolvimento - Viajantes Conectados

**Última Atualização:** Fevereiro de 2025

Guia para manter a qualidade, segurança e consistência do código.

---

## 📋 Padrões de Código

### Python / Django

#### 1. Estrutura de Arquivos

```
app/
├── __init__.py
├── admin.py              # Configuração do Django Admin
├── apps.py               # Configuração da app
├── forms.py              # Django Forms
├── models.py             # Modelos ORM (máx 500 linhas)
├── serializers.py        # DRF Serializers
├── urls.py               # URLs/Rotas
├── views.py              # Views (máx 500 linhas)
├── viewsets.py           # ViewSets da API
├── signals.py            # Django Signals
├── tests.py              # Testes unitários
├── managers.py           # Managers customizados (opcional)
├── permissions.py        # Permissões customizadas (opcional)
└── migrations/           # Migrações banco de dados
```

#### 2. Nomeação

```python
# Classes
class UsuarioViewSet(viewsets.ModelViewSet):
    pass

class PlanoViagem(models.Model):
    pass

# Funções
def processar_solicitacao_amizade():
    pass

def enviar_email_verificacao():
    pass

# Variáveis
usuario_autenticado = request.user
planos_viagem = usuario.planos_viagem.all()

# Constantes
LIMITE_SOLICITACOES_POR_HORA = 10
TEMPO_EXPIRACAO_TOKEN = timedelta(minutes=60)
```

#### 3. Docstrings

```python
def enviar_email_verificacao(usuario):
    """
    Envia um email de verificação para o usuário.

    Args:
        usuario (Usuario): Objeto do usuário para enviar email

    Returns:
        bool: True se enviado com sucesso, False caso contrário

    Raises:
        EmailError: Se houver erro ao enviar email

    Examples:
        >>> usuario = Usuario.objects.get(email='teste@exemplo.com')
        >>> enviar_email_verificacao(usuario)
        True
    """
    pass

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para exibir dados públicos de usuários.

    Atributos:
        - uuid: Identificador único
        - nome_completo: Nome visível
        - foto_perfil: Avatar do usuário
    """
    class Meta:
        model = Usuario
        fields = ['uuid', 'nome_completo', 'foto_perfil']
```

#### 4. Imports

```python
# ✅ BEEM: Agrupar por tipo
# Python stdlib
import logging
from datetime import timedelta
from pathlib import Path

# Third party
from django.db import models
from rest_framework import serializers

# Local
from apps.core.exceptions import ValidacaoDadosException
```

#### 5. Tamanho de Funções/Classes

```python
# ✅ BOM: Função concisa (< 30 linhas)
def validar_email(email):
    """Valida se um email é válido."""
    if not email or '@' not in email:
        raise ValidacaoDadosException("Email inválido")
    return email.lower()

# ❌ RUIM: Função muito grande (> 100 linhas)
def fazer_tudo_nessa_funcao():
    # 200 linhas de código
    # ...
    pass
```

---

## 🔒 Segurança

### 1. Validação de Input

```python
# ✅ BOM
def criar_solicitacao(request):
    email = request.POST.get('email', '').strip()

    if not email:
        raise ValidacaoDadosException("Email é obrigatório")

    if len(email) > 254:
        raise ValidacaoDadosException("Email muito longo")

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        raise UsuarioNaoEncontradoException()

# ❌ RUIM
def criar_solicitacao(request):
    email = request.POST['email']  # Pode lançar KeyError
    usuario = Usuario.objects.get(email=email)  # Sem try/except
```

### 2. Autenticação

```python
# ✅ BOM: Usar permissões
class MeuViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EmailVerificado]

# ❌ RUIM: Verificação manual
def minha_view(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
```

### 3. Autorização

```python
# ✅ BOM: Usar permissions
class MeuViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, EhProprietario]

# ❌ RUIM
def update_view(request, pk):
    objeto = MeuModel.objects.get(pk=pk)
    if objeto.usuario == request.user:
        # Atualizar
        pass
```

### 4. Senhas

```python
# ✅ BOM: Usuario.objects.create_user() hash automaticamente
usuario = Usuario.objects.create_user(
    email='novo@exemplo.com',
    password='SenhaForte123!'
)

# ❌ RUIM: Nunca faça assim
usuario = Usuario(
    email='novo@exemplo.com',
    password='SenhaForte123!'  # Senha em plain text!
)
usuario.save()
```

### 5. SQL Injection

```python
# ✅ BOM: ORM do Django
usuarios = Usuario.objects.filter(
    email__icontains=search_term
)

# ❌ RUIM: SQL raw
usuarios = Usuario.objects.raw(
    f"SELECT * FROM usuarios WHERE email LIKE '%{search_term}%'"
)
```

---

## 🧪 Testes

### Estrutura de Testes

```python
# tests.py ou tests/
class UsuarioModelTests(TestCase):
    """Testes para o modelo Usuario."""

    def setUp(self):
        """Executado antes de cada teste."""
        self.usuario = Usuario.objects.create_user(
            email='teste@exemplo.com',
            password='Teste123!',
            nome_completo='Teste User'
        )

    def test_usuario_criacao(self):
        """Testa se usuário é criado corretamente."""
        self.assertEqual(self.usuario.email, 'teste@exemplo.com')
        self.assertTrue(self.usuario.check_password('Teste123!'))

    def test_email_unico(self):
        """Testa se email é único."""
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='teste@exemplo.com',
                password='Outro123!'
            )


class UsuarioAPITests(APITestCase):
    """Testes para a API de usuários."""

    def test_registrar_usuario(self):
        """Testa endpoint de registro."""
        response = self.client.post(
            '/usuarios/api/usuarios/registrar/',
            {
                'email': 'novo@exemplo.com',
                'nome_completo': 'Novo User',
                'password': 'NovaPassword123!',
                'password2': 'NovaPassword123!'
            }
        )
        self.assertEqual(response.status_code, 201)
```

### Coverage

```bash
# Instalar
pip install coverage

# Rodar
coverage run --source='.' manage.py test
coverage report
coverage html  # Gera relatório HTML

# Meta: > 80% coverage
```

---

## 📦 Dependências

### Adicionar Nova Dependência

```bash
# 1. Pesquise a biblioteca
pip search django-rest-framework

# 2. Instale
pip install django-rest-framework==3.14.0

# 3. Adicione ao requirements
echo "django-rest-framework==3.14.0" >> requirements/requirements.txt

# 4. Atualize Lock file
pip freeze > requirements/requirements.txt
```

### Atualizar Dependências

```bash
# Verificar desatualizadas
pip list --outdated

# Atualizar uma
pip install --upgrade django

# Atualizar todas
pip install --upgrade -r requirements/requirements.txt
```

---

## 🔧 Ferramentas de Desenvolvimento

### Instalação

```bash
# Code formatter
pip install black

# Linter
pip install flake8

# Type checking
pip install mypy

# Sorting imports
pip install isort
```

### Uso

```bash
# Formatar código
black apps/

# Verificar linting
flake8 apps/ --max-line-length=200

# Type checking
mypy apps/usuarios/models.py

# Ordenar imports
isort apps/
```

### Pre-commit Hook

```bash
# Instalar
pip install pre-commit

# Criar .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

---

## 🚀 Performance

### Database Queries

```python
# ✅ BOM: Usar select_related
planos = PlanoViagem.objects.select_related('usuario', 'pais_destino').all()

# ✅ BOM: Usar prefetch_related
usuarios = Usuario.objects.prefetch_related('planos_viagem').all()

# ❌ RUIM: N+1 queries
for plano in PlanoViagem.objects.all():
    print(plano.usuario.nome)  # Query por item!
```

### Caching

```python
# ✅ BOM: Cache com Redis
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutos
def lista_paises(request):
    return JsonResponse(Pais.objects.values())

# ✅ BOM: Cache manual
from django.core.cache import cache

def obter_usuario(uuid):
    usuario = cache.get(f'usuario_{uuid}')
    if not usuario:
        usuario = Usuario.objects.get(uuid=uuid)
        cache.set(f'usuario_{uuid}', usuario, 3600)
    return usuario
```

### Paginação

```python
# ✅ BOM: Usar paginação
class UsuarioViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination

    def get_paginated_response(self, data):
        # Retorna count, next, previous, results
        pass

# ❌ RUIM: Carregar tudo
usuarios = Usuario.objects.all()  # Pode ser milh ões
```

---

## 📝 Logging

### Estrutura

```python
import logging

logger = logging.getLogger(__name__)

# Info
logger.info(f'Usuário criado: {usuario.email}')

# Warning
logger.warning(f'Email inválido detectado: {email}')

# Error
logger.error(f'Erro ao enviar email: {str(erro)}', exc_info=True)

# Debug
logger.debug(f'Valor de variável: {valor}')
```

### Níveis

```
DEBUG:   Informação para debug
INFO:    Informações gerais
WARNING: Algo inesperado mas sem erro
ERROR:   Erro em operação
CRITICAL: Erro crítico do sistema
```

---

## 🔄 Versionamento

### Commits

```bash
# ✅ BOM
git commit -m "feat: adicionar validação de email"
git commit -m "fix: corrigir bug ao enviar solicitação"
git commit -m "docs: atualizar README"
git commit -m "style: formatar código com black"
git commit -m "refactor: simplificar lógica de validação"
git commit -m "test: adicionar testes para utils"

# ❌ RUIM
git commit -m "alterações"
git commit -m "fix bug"
git commit -m "aaa"
```

### Branches

```bash
# Feature
git checkout -b feature/nova-funcionalidade

# Bug fix
git checkout -b bugfix/corrigir-algo

# Development
git checkout -b develop
```

---

## 📊 Code Review Checklist

Antes de fazer push/PR, verifique:

- [ ] Código segue o style guide
- [ ] Nenhuma variável não usada
- [ ] Nenhuma função > 100 linhas
- [ ] Docstrings para funções públicas
- [ ] Testes adicionados/atualizados
- [ ] Tests passando (`pytest`)
- [ ] Sem warnings de linting (`flake8`)
- [ ] Type hints corretos (`mypy`)
- [ ] Sem dados sensíveis no código
- [ ] Commit messages descritivas

---

## 🐛 Debug

### Django Shell

```bash
python manage.py shell_plus

# Com histórico de comandos
python manage.py shell_plus --ipython
```

### Debug Toolbar

```python
# Em development, enable:
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Acessar em http://localhost:8000/__debug__/
```

### Logging

```python
# Ver logs em temps real
tail -f logs/django.log

# Filtrar por erro
tail -f logs/django.log | grep ERROR
```

---

## 📚 Recursos Úteis

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---
## 🤖 Bot de Análise de Código

O projeto inclui um sistema automatizado de análise de código que ajuda a manter qualidade, segurança e consistência.

### Ferramentas Integradas

- **Black**: Formatação automática de código Python
- **Flake8**: Linting e verificação de estilo
- **Bandit**: Análise de segurança para código Python
- **Pre-commit**: Hooks automáticos para execução antes de commits

### Como Usar

#### Comando Django (Recomendado)
```bash
# Análise completa
python manage.py code_analysis

# Apenas verificação de segurança
python manage.py code_analysis --security-only

# Apenas linting
python manage.py code_analysis --lint-only

# Corrigir problemas automaticamente
python manage.py code_analysis --fix
```

#### Bot Standalone
```bash
# Análise completa com relatórios detalhados
python scripts/bot_code_analysis.py

# Apenas linting
python scripts/bot_code_analysis.py --lint-only

# Apenas segurança
python scripts/bot_code_analysis.py --security-only

# Corrigir automaticamente
python scripts/bot_code_analysis.py --fix

# Criar issues no GitHub
python scripts/bot_code_analysis.py --create-issues --github-repo usuario/repo --github-token YOUR_TOKEN
```

#### Integração com GitHub

O bot pode criar e gerenciar issues automaticamente no GitHub:

```bash
# Configurar token do GitHub (recomendado)
export GITHUB_TOKEN=your_personal_access_token

# Executar com criação de issues
python scripts/bot_code_analysis.py --create-issues --github-repo seu-usuario/viajantes_conectados

# Ou especificar token diretamente
python scripts/bot_code_analysis.py --create-issues --github-repo seu-usuario/viajantes_conectados --github-token YOUR_TOKEN
```

**Funcionalidades do GitHub:**
- 📝 **Criação automática de issues** para problemas detectados
- 🔄 **Atualização de issues** existentes com novos detalhes
- ✅ **Fechamento automático** quando problemas são resolvidos
- 🏷️ **Labels automáticas**: `code-analysis`, `automated`, `black`, `flake8`, `bandit`, etc.

#### Pre-commit Hooks
Os hooks são executados automaticamente antes de cada commit:
```bash
# Instalar hooks (feito automaticamente no setup)
pre-commit install

# Executar manualmente em todos os arquivos
pre-commit run --all-files
```

### Relatórios

Os relatórios são salvos em `logs/code_analysis/`:
- **JSON**: Dados estruturados para processamento automatizado
- **Markdown**: Relatórios legíveis para humanos

### Configuração

- **Black**: Linha máxima de 88 caracteres
- **Flake8**: Ignora E203, W503 (conflitos com Black)
- **Bandit**: Exclui migrations e __pycache__

### Configuração do GitHub

Para usar as funcionalidades de issues do GitHub:

1. **Criar Personal Access Token:**
   - Vá para [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Crie um token com permissões `repo` (para repositórios privados) ou `public_repo` (para públicos)
   - Copie o token gerado

2. **Configurar variável de ambiente:**
   ```bash
   export GITHUB_TOKEN=seu_token_aqui
   ```

3. **Ou passar diretamente:**
   ```bash
   python scripts/bot_code_analysis.py --github-token seu_token_aqui --github-repo usuario/repo
   ```

4. **Permissões necessárias:**
   - `Issues`: read/write (para criar, atualizar e fechar issues)
   - `Repository`: read (para acessar informações do repositório)

### Integração CI/CD

Para integração com GitHub Actions ou outros sistemas de CI:

```yaml
name: Code Analysis
on: [push, pull_request]

jobs:
  code-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run code analysis
      run: python scripts/bot_code_analysis.py --no-tests
    - name: Create GitHub issues (optional)
      if: failure()
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        python scripts/bot_code_analysis.py --create-issues --github-repo ${{ github.repository }} --no-tests
```

**Variáveis de ambiente necessárias:**
- `GITHUB_TOKEN`: Token automático fornecido pelo GitHub Actions
- Para repositórios privados, configure um Personal Access Token como secret

### Desenvolvimento

Para adicionar novas ferramentas ou modificar configurações:

1. Edite `.pre-commit-config.yaml` para hooks
2. Modifique `apps/core/management/commands/code_analysis.py` para o comando Django
3. Atualize `scripts/bot_code_analysis.py` para o bot standalone

---
## 🎯 Resumo das Boas Práticas

```
✅ Código limpo e legível
✅ Comentários e docstrings
✅ Validação de input
✅ Tratamento de erros
✅ Testes
✅ Performance
✅ Segurança
✅ Logging
✅ Versionamento
✅ Code review
```

---

Desenvolvido com ❤️ para manter a qualidade do código.

Última Atualização: Fevereiro de 2025
