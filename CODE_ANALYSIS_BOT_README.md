# 🤖 Bot de Análise de Código - Viajantes Conectados

Sistema automatizado de análise de código que corrige problemas, cria revisões e mantém a segurança ativa no projeto Django "Viajantes Conectados".

## ✨ Funcionalidades

- 🔧 **Correção Automática**: Formatação de código com Black
- 🔍 **Linting**: Detecção de problemas de estilo com Flake8
- 🛡️ **Segurança**: Análise de vulnerabilidades com Bandit
- 📝 **Issues no GitHub**: Criação e gerenciamento automático de issues
- 📊 **Relatórios**: Geração de relatórios detalhados em JSON e Markdown
- 🔄 **CI/CD**: Integração com GitHub Actions
- 🪝 **Pre-commit**: Hooks automáticos antes de commits

## 🚀 Instalação Rápida

1. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar pre-commit:**
   ```bash
   pre-commit install
   ```

3. **Executar análise:**
   ```bash
   python manage.py code_analysis
   ```

## 📋 Como Usar

### Comando Django (Recomendado)
```bash
# Análise completa
python manage.py code_analysis

# Apenas segurança
python manage.py code_analysis --security-only

# Corrigir automaticamente
python manage.py code_analysis --fix
```

### Bot Standalone com GitHub
```bash

# Executar com criação de issues
python scripts/bot_code_analysis.py --create-issues --github-repo OPhaels/viajantes_conectados

python manage.py code_analysis --fix # para correções automáticas
```

### Pre-commit Hooks
Executado automaticamente antes de cada commit.

## 🔧 Configuração do GitHub

### 1. Criar Personal Access Token
1. Vá para [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Crie um token com permissões:
   - `repo` (para repositórios privados)
   - `public_repo` (para públicos)
3. Copie o token

### 2. Configurar Token
```bash
# Variável de ambiente (recomendado)
export GITHUB_TOKEN=seu_token_aqui

```

### 3. Funcionalidades do GitHub
- 📝 **Criação automática** de issues para problemas detectados
- 🔄 **Atualização** de issues existentes
- ✅ **Fechamento automático** quando problemas são resolvidos
- 🏷️ **Labels automáticas**: `code-analysis`, `automated`, `black`, `flake8`, `bandit`

## 📊 Relatórios

Os relatórios são salvos em `logs/code_analysis/`:
- **JSON**: Dados estruturados para processamento automatizado
- **Markdown**: Relatórios legíveis para humanos

Exemplo de relatório:
```
🤖 Relatório de Análise de Código

📊 Resumo
- Ferramentas executadas: 3
- Sucesso: 1
- Falhas: 2

❌ BLACK
Erros: would reformat apps/usuarios/models.py

❌ FLAKE8
Erros: apps/chat/models.py:15:1: F401 'django.utils' imported but unused

✅ BANDIT
Nenhum problema de segurança encontrado
```

## 🔄 Integração CI/CD

### GitHub Actions
O workflow `.github/workflows/code-analysis.yml` executa automaticamente:

- **Push/PR**: Análise em pushes e pull requests
- **Schedule**: Verificação diária às 6:00 UTC
- **Manual**: Execução sob demanda

### Configuração Personalizada
```yaml
- name: Code Analysis
  run: python scripts/bot_code_analysis.py --create-issues --github-repo ${{ github.repository }}
```

## 🛠️ Desenvolvimento

### Adicionar Nova Ferramenta
1. Edite `scripts/bot_code_analysis.py`
2. Adicione método para a nova ferramenta
3. Atualize `.pre-commit-config.yaml`
4. Modifique `apps/core/management/commands/code_analysis.py`

### Personalizar Configurações
- **Black**: Edite `--line-length` em `.pre-commit-config.yaml`
- **Flake8**: Modifique `--extend-ignore` nas configurações
- **Bandit**: Ajuste `--exclude` para pastas

## 📚 Documentação

- [Guia de Desenvolvimento](docs/desenvolvimento/DEVELOPMENT_GUIDE.md)
- [Guia de Segurança](docs/seguranca/SECURITY_GUIDE.md)
- [API Documentation](docs/api/API_DOCUMENTATION.md)

## 🤝 Contribuição

1. Execute `python manage.py code_analysis --fix` antes de commitar
2. Certifique-se que todos os checks passam
3. Siga os padrões definidos no [Development Guide](docs/desenvolvimento/DEVELOPMENT_GUIDE.md)

---
