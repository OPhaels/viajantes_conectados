## Estrutura do Projeto

```bash
viajantes_conectados/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── usuarios/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── signals.py
│   │   └── tests.py
│   │
│   ├── destinos/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests.py
│   │
│   ├── conexoes/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── tests.py
│   │
│   └── chat/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── consumers.py
│       ├── routing.py
│       └── tests.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── templates/
│   ├── base.html
│   ├── usuarios/
│   ├── destinos/
│   ├── conexoes/
│   └── chat/
│
└── media/
    └── fotos_perfil/
