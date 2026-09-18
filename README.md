# 🎵 Rate API — Social Music Backend

Backend de una plataforma social de música: los usuarios se registran, se autentican y publican posts sobre los que se pueden comentar. Construido con **FastAPI** y **PostgreSQL**.

---

## 🧱 Stack

- **Framework:** FastAPI
- **Base de datos:** PostgreSQL 17
- **ORM:** SQLAlchemy
- **Autenticación:** JWT (`python-jose`)
- **Hash de contraseñas:** Passlib + bcrypt
- **Contenedores:** Docker / Docker Compose (solo para la base de datos, ver más abajo)

---

## 📁 Estructura del proyecto

```
app/
├── main.py                  # Punto de entrada de la API (FastAPI app)
├── api/routes/               # Endpoints (users, posts, comments)
├── services/                 # Lógica de negocio (auth, users)
├── utils/security.py         # Hash de contraseñas y config JWT
└── database/
    ├── conf/                 # Conexión a la BD (SQLAlchemy) y dependencias
    ├── models/                # Modelos ORM (user, post, comment, genre)
    └── schema/                # Esquemas Pydantic (request/response)

docker/
├── docker-compose.yml        # Levanta el contenedor de PostgreSQL
├── fast_api/Dockerfile       # (vacío por ahora, no se usa)
└── postgre_sql/Dockerfile    # (vacío por ahora, no se usa)

requirements.txt              # Dependencias Python
```

> Nota: existe también una carpeta `rate/` en la raíz con un `pyproject.toml` suelto (gestionado con `uv`). No forma parte de la app activa (`app/`) — parece un experimento aparte y puede ignorarse o eliminarse.

---

## ⚙️ Requisitos previos

- Python 3.10+ (recomendado)
- Docker y Docker Compose (para la base de datos)
- `pip`

---

## 🚀 Cómo levantar el proyecto

### 1. Clonar e instalar dependencias

```bash
git clone <url-del-repo>
cd Rate
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install python-jose             # necesario para JWT, falta en requirements.txt
```

### 2. Levantar la base de datos (PostgreSQL) con Docker

```bash
cd docker
docker-compose up -d
```

Esto crea un contenedor Postgres con:

| Variable         | Valor      |
|------------------|------------|
| Usuario          | `admin`    |
| Contraseña       | `password` |
| Base de datos    | `forumdb`  |
| Puerto           | `5432`     |

> ⚠️ El `docker-compose.yml` solo levanta la **base de datos**. La API (FastAPI) no corre en Docker todavía — los `Dockerfile` de `fast_api/` y `postgre_sql/` están vacíos —, así que se ejecuta aparte con Uvicorn (paso siguiente).

### 3. Levantar la API

Desde la raíz del proyecto, con la base de datos ya corriendo:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API quedará disponible en:

```
http://localhost:8000
```

Docs interactivas (Swagger) en:

```
http://localhost:8000/docs
```

Las tablas se crean automáticamente al arrancar (`Base.metadata.create_all`), no hace falta correr migraciones aparte.

### ⚠️ Configuración de la base de datos

La cadena de conexión está **hardcodeada** en `app/database/conf/alch_conf.py`:

```python
DATABASE_URL = "postgresql://admin:password@localhost:5432/forumdb"
```

Si cambias usuario, contraseña, host o nombre de la base en `docker-compose.yml`, tenés que actualizar también esta línea (todavía no usa variables de entorno / `.env`).

---

## 📡 Endpoints disponibles

### Usuarios (`/users`)

| Método | Ruta             | Descripción                              | Auth |
|--------|------------------|-------------------------------------------|------|
| POST   | `/users/signup`  | Registrar nuevo usuario                   | No   |
| POST   | `/users/login`   | Login, devuelve JWT                       | No   |
| GET    | `/users/me`      | Usuario autenticado actual                | Sí   |
| GET    | `/users/{id}`    | Obtener usuario por ID                    | No   |
| GET    | `/users/`        | Listar todos los usuarios                 | Sí   |

### Posts (`/posts`)

| Método | Ruta                     | Descripción                          | Auth |
|--------|--------------------------|----------------------------------------|------|
| GET    | `/posts/`                | Listar posts (más recientes primero)   | No   |
| GET    | `/posts/{id}`             | Obtener post por ID                    | No   |
| POST   | `/posts/`                 | Crear post                             | Sí   |
| PATCH  | `/posts/{id}`             | Actualizar post                        | No*  |
| DELETE | `/posts/{id}`             | Eliminar post                          | No*  |
| GET    | `/posts/user/{user_id}`   | Posts de un usuario                    | No   |

\* `PATCH` y `DELETE` de posts todavía no exigen autenticación ni validan que el usuario sea el autor — pendiente de reforzar.

### Comentarios (`/comment`)

El router de comentarios (`app/api/routes/comment.py`) existe pero **todavía no está registrado en `main.py`** y tiene errores pendientes (usa una variable `post_id` no definida, y un endpoint `POST` sin función implementada). No está operativo por ahora.

---

## 🔐 Autenticación

1. El usuario se registra en `POST /users/signup` (contraseña hasheada con bcrypt).
2. Hace login en `POST /users/login` (formato `OAuth2PasswordRequestForm`: `username` + `password`) y recibe un JWT.
3. Ese token se envía como `Authorization: Bearer <token>` en los endpoints protegidos.
4. El token expira a los **2 minutos** (`ACCESS_TOKEN_DURATION = 2` en `app/utils/security.py`) — útil tenerlo en cuenta al probar la API, puede convenir subir este valor en desarrollo.

> La clave secreta (`SECRET`) está hardcodeada en el código fuente (`security.py` y `user.py`). Antes de llevar esto a producción conviene moverla a una variable de entorno.

---

## 🧪 Próximos pasos sugeridos

- Mover `DATABASE_URL` y `SECRET` a variables de entorno (`.env`).
- Completar y registrar el router de comentarios.
- Añadir Dockerfile real para la API y sumarla al `docker-compose.yml`.
- Proteger `PATCH`/`DELETE` de posts con autenticación y verificación de autor.
- Añadir dependencia `python-jose` a `requirements.txt`.
- Tests (existe carpeta `.tests/` y `.pytest_cache/`, revisar cobertura actual).
