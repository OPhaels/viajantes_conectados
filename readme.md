viajantes_conectados/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── usuarios/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── signals.py
│   │   └── tests.py
│   ├── destinos/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests.py
│   ├── conexoes/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── tests.py
│   └── chat/
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── consumers.py
│       ├── routing.py
│       └── tests.py
├── static/
│   ├── css/
│   │   ├── main.css
│   │   └── animations.css
│   ├── js/
│   │   ├── main.js
│   │   ├── mapa.js
│   │   └── chat.js
│   └── img/
├── templates/
│   ├── base.html
│   ├── usuarios/
│   │   ├── cadastro.html
│   │   ├── login.html
│   │   ├── perfil.html
│   │   └── editar_perfil.html
│   ├── destinos/
│   │   ├── buscar.html
│   │   ├── lista_viajantes.html
│   │   └── detalhes_destino.html
│   ├── conexoes/
│   │   ├── solicitacoes.html
│   │   └── lista_amigos.html
│   └── chat/
│       └── conversa.html
└── media/
    └── fotos_perfil/