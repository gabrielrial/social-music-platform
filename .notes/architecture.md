forum-project/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   │
│   ├── models/                         # Define cómo se ven en la base de datos.
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── like.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── auth.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── post_repository.py
│   │   └── comment_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── post_service.py
│   │   └── comment_service.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   │
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── posts.py
│   │       └── comments.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── post_detail.html
│   │   └── profile.html
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── utils/
│       ├── pagination.py
│       └── validators.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_posts.py
│   └── test_comments.py
│
├── docker/
│   └── postgres/
│
├── .env
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── README.md