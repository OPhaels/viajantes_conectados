# 🌍 Viajantes Conectados

**Plataforma para conectar viajantes que compartilham o mesmo destino**

---

## 🚀 Início Rápido

Beta - https://viajantesconectados.com/

### Pré-requisitos
- Python 3.11
- Django 5.0+
- PostgreSQL (sugerido para produção)

### Instalação
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/viajantes_conectados.git
cd viajantes_conectados

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env (veja docs/desenvolvimento/)
cp .env.example .env

# 5. Execute migrações
python manage.py migrate

# 6. Inicie servidor
python manage.py runserver
```

**App está rodando em:** http://localhost:8000/

---

## 📚 Documentação

Toda documentação está organizada em `/docs`:

### 📋 Guias Rápidos
- [Próximos Passos](docs/guias/GUIA_PROXIMOS_PASSOS.md) - Comece aqui! ⭐
- [Resumo de Limpeza](docs/guias/RESUMO_EXECUCAO.md) - O que foi feito
- [Changelog](docs/guias/CHANGELOG_LIMPEZA.md) - Mudanças detalhadas

### 🔌 API & Desenvolvimento
- [Documentação API](docs/api/API_DOCUMENTATION.md) - Todos os endpoints
- [Guia Desenvolvimento](docs/desenvolvimento/DEVELOPMENT_GUIDE.md) - Setup local
- [Referência Rápida](docs/api/QUICK_REFERENCE.md) - Comandos úteis
- [Testes API](docs/api/API_TESTES.md) - Exemplos de requisições

### 🔒 Segurança
- [Guia Segurança](docs/seguranca/SECURITY_GUIDE.md) - Práticas recomendadas
- [Configurações Segurança](docs/seguranca/SECURITY.md) - Implementação

### 📈 Desenvolvimento
- [Melhorias Planejadas](docs/desenvolvimento/IMPROVEMENTS.md) - Roadmap
- [Índice Documentação](docs/DOCS_INDEX.md) - Mapa completo

---

## ✨ Features Principais

- ✅ **Autenticação JWT** - Login seguro com tokens
- ✅ **Planos de Viagem** - Crie e compartilhe seus destinos
- ✅ **Sistema de Amizade** - Conecte-se com outros viajantes
- ✅ **Chat em Tempo Real** - WebSockets com Django Channels
- ✅ **Filtros Avançados** - Busque viagens por país, data, orçamento
- ✅ **Responsivo** - Funciona em mobile, tablet e desktop
- ✅ **Auditoria Completa** - Todas as ações são registradas
- ✅ **Rate Limiting** - Proteção contra abuso

---

## 🏗️ Estrutura do Projeto

```
viajantes_conectados/
├── apps/                    # Apps Django
│   ├── usuarios/           # Autenticação e perfis
│   ├── destinos/           # Planos de viagem
│   ├── conexoes/           # Amizades e conexões
│   ├── chat/               # Mensagens em tempo real
│   └── core/               # Utilitários centralizados
├── config/                 # Configuração Django
├── templates/              # Templates HTML
├── static/                 # CSS, JS, imagens
│   └── css/style.css      # Design system responsivo
├── docs/                   # 📚 Documentação organizada
│   ├── guias/             # Guias práticos
│   ├── api/               # Documentação API
│   ├── seguranca/         # Segurança
│   └── desenvolvimento/    # Setup e desenvolvimento
├── tests/                  # Testes automatizados
├── requirements/          # Dependências Python
└── manage.py              # Django CLI

```

---

## 👨‍💻 Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Django 5.0, Django REST Framework |
| **Auth** | JWT (rest-framework-simplejwt) |
| **Real-time** | Django Channels, WebSockets |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Cache** | Redis (produção) |
| **Frontend** | HTML5, Bootstrap 5, CSS Responsivo |
| **API** | REST com versionamento |

---

## 🔐 Segurança

O projeto foi completamente refatorado com foco em segurança:

- ✅ **Tokens JWT seguros** com expiração
- ✅ **Rate limiting** em todos endpoints críticos
- ✅ **Auditoria completa** de ações
- ✅ **CORS configurado** corretamente
- ✅ **Content Security Policy (CSP)** ativa
- ✅ **Senhas seguras** com validação forte
- ✅ **Proteção contra força bruta** no login

👉 Leia [Guia de Segurança](docs/seguranca/SECURITY_GUIDE.md)

---

## 📖 Como Usar a Documentação

1. **Começando?** → Vá para [Próximos Passos](docs/guias/GUIA_PROXIMOS_PASSOS.md) ⭐
2. **Desenvolvendo?** → Veja [Guia Desenvolvimento](docs/desenvolvimento/DEVELOPMENT_GUIDE.md)
3. **Usando a API?** → Consulte [Documentação API](docs/api/API_DOCUMENTATION.md)
4. **Preocupado com segurança?** → Leia [Guia Segurança](docs/seguranca/SECURITY_GUIDE.md)
5. **Procurando algo?** → Veja [Índice Completo](docs/DOCS_INDEX.md)

---

## 🤝 Contribuir

Contribuições são bem-vindas!

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 License

Este projeto está sob a licença MIT. Veja [LICENSE.md](LICENSE.md) para detalhes.

---

## 📞 Suporte

- 📚 **Documentação:** `/docs`
- 🐛 **Issues:** GitHub Issues
- 💬 **Discussões:** GitHub Discussions

---

## ✅ Status

- **Código:** ✅ Limpo (Zero duplicidades)
- **Segurança:** ✅ Implementada
- **Testes:** ✅ Validação completa
- **Documentação:** ✅ Organizada
- **Pronto para Produção:** ✅ Sim

**Última atualização:** Março 2026 | **Versão:** 1.0
