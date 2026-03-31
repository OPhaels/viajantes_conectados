#!/bin/bash
# Script de Setup Inicial - Viajantes Conectados

echo "================================================"
echo "  Restauração Sistema: Viajantes Conectados"
echo "================================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar Python
echo -e "${YELLOW}[1]${NC} Verificando Python..."
python --version || { echo -e "${RED}Python não encontrado!${NC}"; exit 1; }
echo -e "${GREEN}✓ Python OK${NC}"
echo ""

# 2. Verificar Django
echo -e "${YELLOW}[2]${NC} Verificando Django..."
python -m django --version || { echo -e "${RED}Django não instalado!${NC}"; exit 1; }
echo -e "${GREEN}✓ Django OK${NC}"
echo ""

# 3. Criar Migrations
echo -e "${YELLOW}[3]${NC} Criando migrações..."
python manage.py makemigrations
echo -e "${GREEN}✓ Migrações criadas${NC}"
echo ""

# 4. Executar Migrations
echo -e "${YELLOW}[4]${NC} Executando migrações..."
python manage.py migrate
echo -e "${GREEN}✓ Banco de dados atualizado${NC}"
echo ""

# 5. Criar Superuser
echo -e "${YELLOW}[5]${NC} Criando superuser..."
echo "Execute: python manage.py createsuperuser"
echo ""

# 6. Carregar Países (opcional)
echo -e "${YELLOW}[6]${NC} (Opcional) Carregar países padrão..."
echo "python manage.py loaddata countries"
echo ""

# 7. Testes
echo -e "${YELLOW}[7]${NC} Executando testes..."
python manage.py test

# 8. Instalar Pre-commit Hooks
echo -e "${YELLOW}[8]${NC} Instalando pre-commit hooks..."
pip install pre-commit
pre-commit install

echo -e "${GREEN}✓ Pre-commit hooks instalados${NC}"
echo ""

echo -e "${GREEN}🎉 Setup concluído!${NC}"
echo ""
echo "Para executar análise de código manualmente:"
echo "  python manage.py code_analysis"
echo ""
echo "Para executar apenas verificação de segurança:"
echo "  python manage.py code_analysis --security-only"
echo ""
echo "Para corrigir problemas automaticamente:"
echo "  python manage.py code_analysis --fix"
echo ""
echo "Para usar o bot com GitHub:"
echo "  python scripts/bot_code_analysis.py --create-issues --github-repo usuario/repo"
python manage.py test --verbosity=2
echo ""

echo "================================================"
echo -e "${GREEN}Setup Completo!${NC}"
echo "================================================"
echo ""
echo "Próximas etapas:"
echo "1. Criar conta de superuser: python manage.py createsuperuser"
echo "2. Iniciar servidor: python manage.py runserver"
echo "3. Acessar admin: http://localhost:8000/admin/"
echo ""
echo "Documentação: Ver IMPLEMENTACAO.md para detalhes das APIs"
echo ""
