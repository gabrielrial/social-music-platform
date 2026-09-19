# Rate API - Test Project

## Estructura del Proyecto

```
app_test/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── database.py        # Configuración de base de datos
├── models/
│   ├── __init__.py
│   └── user.py            # Modelo de Usuario
├── schemas/
│   ├── __init__.py
│   └── user.py            # Schemas Pydantic
├── routers/
│   ├── __init__.py
│   └── users.py           # Endpoints de usuarios
├── dependencies.py        # Dependencias (get_db)
└── main.py               # Aplicación FastAPI
```

## Requisitos

- Python 3.10+
- PostgreSQL
- FastAPI
- SQLAlchemy
- uvicorn

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Asegurarse que PostgreSQL está corriendo con la BD "forumdb":
```bash
# Verificar credenciales en config/database.py
# DATABASE_URL = "postgresql://admin:password@localhost:5432/forumdb"
```

## Ejecutar

```bash
# Opción 1: Desde main.py
python app_test/main.py

# Opción 2: Con uvicorn
uvicorn app_test.main:app --reload

# Opción 3: Especificar host y puerto
uvicorn app_test.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## Endpoints

- `GET /` - Mensaje de bienvenida
- `POST /users/` - Crear usuario
  ```json
  {"username": "john_doe"}
  ```
- `GET /users/` - Listar todos los usuarios
- `GET /users/{user_id}` - Obtener usuario por ID

## Documentación Interactiva

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Resolución de Problemas

### Error de conexión a BD
```
ensure el servicio PostgreSQL está corriendo
verificar credenciales en config/database.py
crear la BD "forumdb" si no existe
```

### Error de importación
```
Verificar que estés en la raíz del proyecto (/Users/gabrielrial/Desktop/git/Rate)
Verificar el PYTHONPATH incluya la carpeta Rate
```
