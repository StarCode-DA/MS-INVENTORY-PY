# 📦 Eclipse Bar — Microservicio de Inventario (MS-INVENTORY-PY)

Microservicio encargado de la gestión de inventario por sede del sistema **Eclipse Bar**. Permite controlar el stock de productos del catálogo maestro de forma independiente por cada sede.

---

## 📋 Tabla de contenido

- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Endpoints](#endpoints)
- [Validaciones](#validaciones)
- [Permisos por rol](#permisos-por-rol)
- [Modelos de base de datos](#modelos-de-base-de-datos)
- [Relación con otros microservicios](#relación-con-otros-microservicios)
- [Correr con Docker](#correr-con-docker)

---

## 🛠 Tecnologías

- [FastAPI](https://fastapi.tiangolo.com/) — Framework web
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM para base de datos
- [PostgreSQL](https://www.postgresql.org/) — Base de datos
- [Pydantic V2](https://docs.pydantic.dev/) — Validación de datos
- [Uvicorn](https://www.uvicorn.org/) — Servidor ASGI

---

## ✅ Requisitos previos

- Python >= 3.11
- PostgreSQL corriendo (o usar Docker)
- Base de datos `eclipsebar_db` inicializada con `init.sql`
- Tabla `inventory` creada (ver script en [Modelos de base de datos](#modelos-de-base-de-datos))
- Token JWT válido generado por `MS-AUTH-PY` para endpoints protegidos

---

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone 
cd MS-INVENTORY-PY

# Instalar dependencias
pip install -r requirements.txt

# Correr el servidor
uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

---

## 🔧 Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://eb_user:eb_pass@localhost:5437/eclipsebar_db
```

---

## 📁 Estructura del proyecto

src/
├── models/
│   └── inventarios.py       # Modelo SQLAlchemy de la tabla inventory
├── routers/
│   └── inventarios.py       # Endpoints REST del microservicio
├── schemas/
│   └── inventario.py        # Schemas Pydantic (validación de datos)
├── utils/
├── database.py              # Configuración de conexión a PostgreSQL
├── main.py                  # Punto de entrada de la aplicación
└── config.py                # Configuracion del servicio

---

## 📡 Endpoints

Base URL: `http://localhost:8004`

| Método | Endpoint | Rol requerido | Descripción |
|--------|----------|---------------|-------------|
| GET | `/inventory/` | Admin, Cajero | Listar inventario de una sede |
| POST | `/inventory/` | Admin, Cajero | Agregar producto al inventario |
| PUT | `/inventory/{id}` | Admin, Cajero | Actualizar stock de un producto |
| PATCH | `/inventory/{id}/toggle-activo` | Admin, Cajero | Activar o desactivar un producto |

### GET `/inventory/`

Retorna el inventario completo de una sede.

**Query params:**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `sede_id` | int | ✅ | ID de la sede |

```json
// Response
[
  {
    "id": 1,
    "product_id": 3,
    "sede_id": 1,
    "stock": 50.0,
    "activo": true
  }
]
```

---

### POST `/inventory/`

Agrega un producto al inventario de una sede.

```json
// Request
{
  "product_id": 3,
  "sede_id": 1,
  "stock": 50.0
}

// Response
{
  "id": 1,
  "product_id": 3,
  "sede_id": 1,
  "stock": 50.0,
  "activo": true
}
```

**Errores:**
- `400` — El producto ya existe en esa sede.

---

### PUT `/inventory/{id}`

Reemplaza el stock actual de un producto en el inventario.

```json
// Request
{
  "stock": 35.0
}

// Response
{
  "id": 1,
  "product_id": 3,
  "sede_id": 1,
  "stock": 35.0,
  "activo": true
}
```

**Errores:**
- `404` — Item no encontrado.

---

### PATCH `/inventory/{id}/toggle-activo`

Activa o desactiva un producto del inventario de una sede.

```json
// Response
{
  "id": 1,
  "activo": false
}
```

**Errores:**
- `404` — Item no encontrado.

---

## ✔️ Validaciones

- `stock` no puede ser negativo en ningún endpoint.
- No se puede agregar el mismo producto dos veces en la misma sede — el par `(product_id, sede_id)` es único.

---

## 👥 Permisos por rol

| Acción | Administrador | Cajero | Mesero |
|--------|---------------|--------|--------|
| Ver inventario | ✅ Todas las sedes | ✅ Solo su sede | ✅ Solo su sede |
| Agregar producto | ✅ | ✅ | ❌ |
| Actualizar stock | ✅ | ✅ | ❌ |
| Activar / Desactivar | ✅ | ✅ | ❌ |

> ⚠️ El control de permisos por rol se gestiona en el frontend. El backend no valida el rol en este microservicio.

---

## 🗄️ Modelos de base de datos

| Tabla | Descripción |
|-------|-------------|
| `inventory` | Stock de productos por sede |

### Script de creación

```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    sede_id INT NOT NULL REFERENCES sedes(id),
    stock NUMERIC DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, sede_id)
);

CREATE INDEX idx_inventory_sede ON inventory(sede_id);
CREATE INDEX idx_inventory_product ON inventory(product_id);
```

---

## 🔗 Relación con otros microservicios

Este microservicio **no almacena información del producto** (nombre, unidad, categoría). Solo guarda `product_id` como referencia al catálogo maestro gestionado por **MS-PRODUCT-PY**.

El frontend une ambos microservicios para mostrar la información completa:
MS-INVENTORY-PY  →  product_id, sede_id, stock
MS-PRODUCT-PY    →  name, unit, category, price, cost

> Si un producto es modificado en MS-PRODUCT-PY, los cambios se reflejan automáticamente en el inventario sin necesidad de actualizar ningún dato en este microservicio.

---

## 🐳 Correr con Docker

```bash
# Construir imagen
docker build -t eb-inventory .

# Correr contenedor
docker run -p 8004:8004 --env-file .env eb-inventory
```

O usar el Docker Compose del repositorio `INFRA-EB-DK`:

```bash
cd INFRA-EB-DK/compose
docker compose up -d inventory
```

---

## 📖 Documentación automática

FastAPI genera documentación automática disponible en:

- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`