<div align="center">

![Nexovo](https://nexovo.com.co/light_logo.png)

# **Nexovo Booking API**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python\&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-🚀-009688?logo=fastapi\&logoColor=white)](#)
[![Uvicorn](https://img.shields.io/badge/ASGI-Uvicorn-4B8BBE?logo=python\&logoColor=white)](#)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063)](#)
[!\[Traefik\](https://img.shields.io/badge/Edge- Traefik-24A1C1?logo=traefikmesh\&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-Proprietary-8A2BE2)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#)

Servicio **FastAPI** para gestionar **alojamientos**, **habitaciones**, **disponibilidad**, **reservas** y **subidas de archivos**. Incluye **JWT Bearer**, **CORS** para todos los subdominios de `nexovo.com.co`, **logging profesional** con **Request‑ID**, compresión **GZip** y documentación **OpenAPI**.

</div>

---

## ⚡️ TL;DR (Quickstart)

```bash
# 1) Crear entorno e instalar deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2) Ejecutar en local (con logs útiles)
LOG_LEVEL=DEBUG uvicorn app.main:app \
  --host 0.0.0.0 --port 5000 --reload --proxy-headers

# 3) Ver documentación
open http://127.0.0.1:5000/api/v1/docs
```

> **Base Path:** todas las rutas se exponen bajo **`/api/v1`**.

---

## 🧩 Arquitectura y tecnologías

* **FastAPI + Starlette** (ASGI)
* **Uvicorn** (dev) / **Traefik** (edge en prod vía Dokploy)
* **Pydantic v2** (modelado y validación)
* **JWT Bearer** (auth), **GZip**, **CORS**, **Request‑ID**, **HTTP Access Logs**
* **OpenAPI** (Swagger UI y ReDoc)

```text
┌───────────────────────────────────────────────────────────────┐
│                       Client / Frontend                      │
└───────────────▲───────────────────────────────▲──────────────┘
                │ Origin: https://booking.nexovo.com.co
                │
        ┌───────┴────────┐        CORS + TLS        ┌────────────┐
        │   Traefik      │ ───────────────────────▶ │  FastAPI   │
        │ (Dokploy Edge) │  PathPrefix /api/v1/*   │  (Uvicorn) │
        └───────┬────────┘                          └─────┬──────┘
                │  Logs, Metrics (rid)                    │
                └──────────────────────────────────────────┘
```

---

## ✨ Características principales

* **API versionada** → prefijo **`/api/v1`**
* **Módulos** → *Accommodations, Rooms, Availability, Bookings, Uploads*
* **Uploads** → presigned **POST/GET** + subida server‑side
* **CORS** → dominio raíz y **todos los subdominios** de `nexovo.com.co`
* **OpenAPI con branding** → logo, tags, servers relativos
* **Observabilidad** → Request‑ID, latencia (`in_ms`), size, UA, IP, origin
* **Health** → `GET /api/v1/health`

---

## 🗂️ Estructura del proyecto

```text
app/
├─ main.py                      # App FastAPI: middlewares, OpenAPI, routers
├─ core/
│  ├─ config.py                 # Settings/entorno
│  ├─ errors.py                 # Handlers de excepciones
│  └─ logging_config.py         # dictConfig + filtros/formatters
├─ middleware/
│  ├─ auth_middleware.py        # Bearer JWT (exenciones públicas)
│  ├─ request_id.py             # X-Request-ID (contextvar + header)
│  └─ http_logger.py            # Logs de acceso (latencia, status, etc.)
├─ booking/
│  ├─ routes/
│  │  ├─ __init__.py            # Exporta routers
│  │  ├─ accommodations.py      # /accommodations
│  │  ├─ rooms.py               # /rooms
│  │  ├─ availability.py        # /availability
│  │  └─ booking.py             # /bookings
│  ├─ uploads/
│  │  └─ routes.py              # /uploads
│  └─ schemas/                  # Pydantic models (Create/Update/Out)
└─ ...
```

---

## ⚙️ Configuración

### 🔐 Variables de entorno

| Variable       | Valores                    | Default | Descripción                                  |
| -------------- | -------------------------- | ------: | -------------------------------------------- |
| `LOG_LEVEL`    | `DEBUG`\|`INFO`\|`WARNING` |  `INFO` | Nivel de log                                 |
| `LOG_FORMAT`   | `plain`\|`json`            | `plain` | Requiere `python-json-logger` si `json`      |
| `LOG_BODY`     | `true`\|`false`            | `false` | Log del body (POST/PUT/PATCH) **solo debug** |
| `LOG_BODY_MAX` | entero                     |  `2048` | Bytes máximos del body a loguear             |

> Añade aquí los secretos/keys que use tu `AuthMiddleware` o servicios externos.

### 🌍 CORS (App)

```python
allow_origin_regex = r"^https:\/\/(?:[a-z0-9-]+\.)*nexovo\.com\.co$"
allow_origins = [
  "http://localhost", "http://127.0.0.1",
  "http://localhost:3000", "http://localhost:5000", "http://localhost:5173"
]
```

> **Recomendado:** habilitar **CORS también en Traefik** para que en 404/5xx del proxy sigan saliendo headers CORS.

### 📜 OpenAPI / Swagger

* UI → `GET /api/v1/docs`
* ReDoc → `GET /api/v1/redoc`
* Esquema → `GET /api/v1/openapi.json`
* **Servers**: usar `"/"` (relativo) para evitar duplicar `/api/v1`.

### 🛡️ Autenticación

* **Bearer JWT** global (definido en componentes OpenAPI)
* `AuthMiddleware` **protege** rutas por defecto y **excluye**: `/`, `/api/v1/health`, `/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json` y opcionalmente `/api/v1/_debug/echo`.

### 📈 Logging y observabilidad

`RequestIDMiddleware` genera o propaga `X-Request-ID` y lo añade a los logs.

Ejemplo de línea de log de acceso:

```text
INFO [app.http] [rid=4f1e…] | access method=GET path=/api/v1/_debug/echo status=200 in_ms=1.23 ip=… host=… origin=… ua="…" size=260 user_id=-
```

Probar local:

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload --proxy-headers
curl -i -H "Origin: https://booking.nexovo.com.co" http://127.0.0.1:5000/api/v1/_debug/echo
```

---

## 🧪 Ejecución local

**Requisitos**: Python 3.12+
**Opcional**: `python-json-logger` para logs JSON.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload --proxy-headers
```

Checks rápidos:

```bash
curl -i http://127.0.0.1:5000/api/v1/health
curl -s http://127.0.0.1:5000/api/v1/openapi.json | jq '.info.title,.servers'
```

---

## 🚀 Despliegue (Dokploy / Traefik)

### Router por prefijos a FastAPI + CORS en proxy

```yaml
services:
  booking_api:
    labels:
      - traefik.enable=true

      # HTTPS (ajusta Host si usas otro dominio)
      - traefik.http.routers.bookingapi.rule=Host(`booking.nexovo.com.co`) && (PathPrefix(`/api/v1/_debug`) || PathPrefix(`/api/v1/accommodations`) || PathPrefix(`/api/v1/rooms`) || PathPrefix(`/api/v1/availability`) || PathPrefix(`/api/v1/bookings`) || PathPrefix(`/api/v1/uploads`) || PathPrefix(`/api/v1/health`) || PathPrefix(`/api/v1/docs`) || PathPrefix(`/api/v1/openapi.json`) || PathPrefix(`/api/v1/redoc`))
      - traefik.http.routers.bookingapi.entrypoints=websecure
      - traefik.http.routers.bookingapi.tls=true
      - traefik.http.routers.bookingapi.priority=200
      - traefik.http.services.bookingapi.loadbalancer.server.port=5000

      # Aplica CORS a este router
      - traefik.http.routers.bookingapi.middlewares=cors-headers@docker

      # Middleware CORS (definición)
      - traefik.http.middlewares.cors-headers.headers.accessControlAllowCredentials=true
      - traefik.http.middlewares.cors-headers.headers.accessControlAllowMethods=GET,POST,PUT,DELETE,OPTIONS,PATCH
      - traefik.http.middlewares.cors-headers.headers.accessControlAllowHeaders=Authorization,Content-Type,*
      - traefik.http.middlewares.cors-headers.headers.accessControlExposeHeaders=*
      - traefik.http.middlewares.cors-headers.headers.addVaryHeader=true
      - traefik.http.middlewares.cors-headers.headers.accessControlMaxAge=600
      - traefik.http.middlewares.cors-headers.headers.accessControlAllowOriginList=https://nexovo.com.co
      - traefik.http.middlewares.cors-headers.headers.accessControlAllowOriginListRegex=^https://(?:[a-z0-9-]+\.)*nexovo\.com\.co$
```

**Notas**

* **No** uses `StripPrefix` (la app espera `/api/v1/...`).
* Si otro router captura el mismo host, sube `priority` aquí.
* Mantén CORS **también** en la app para respuestas generadas por FastAPI.

---

## 🔎 Rutas principales (resumen)

> Detalle en `/api/v1/docs`.

| Método | Ruta                                                | Descripción                        |
| ------ | --------------------------------------------------- | ---------------------------------- |
| GET    | `/api/v1/health`                                    | Healthcheck                        |
| GET    | `/api/v1/accommodations/`                           | Listar alojamientos                |
| POST   | `/api/v1/accommodations/`                           | Crear alojamiento *(Auth)*         |
| GET    | `/api/v1/accommodations/{id}`                       | Obtener por ID                     |
| PUT    | `/api/v1/accommodations/{id}`                       | Actualizar *(Auth)*                |
| DELETE | `/api/v1/accommodations/{id}`                       | Eliminar *(Auth)*                  |
| GET    | `/api/v1/accommodations/my`                         | Mis alojamientos *(Auth)*          |
| GET    | `/api/v1/accommodations/search`                     | Buscar (nombre, precio, servicios) |
| GET    | `/api/v1/rooms/`                                    | Listar habitaciones                |
| POST   | `/api/v1/rooms/`                                    | Crear habitación *(Auth)*          |
| GET    | `/api/v1/rooms/{room_id}`                           | Obtener por ID                     |
| PUT    | `/api/v1/rooms/{room_id}`                           | Actualizar *(Auth)*                |
| DELETE | `/api/v1/rooms/{room_id}`                           | Eliminar *(Auth)*                  |
| GET    | `/api/v1/rooms/by_accommodation/{accommodation_id}` | Habitaciones por alojamiento       |
| POST   | `/api/v1/availability/`                             | Crear disponibilidad *(Auth)*      |
| GET    | `/api/v1/availability/room/{room_id}`               | Disponibilidad por habitación      |
| GET    | `/api/v1/availability/{availability_id}`            | Obtener por ID                     |
| PUT    | `/api/v1/availability/{availability_id}`            | Actualizar *(Auth)*                |
| DELETE | `/api/v1/availability/{availability_id}`            | Eliminar *(Auth)*                  |
| GET    | `/api/v1/bookings/`                                 | Listar reservas *(según permisos)* |
| POST   | `/api/v1/bookings/`                                 | Crear reserva *(Auth)*             |
| GET    | `/api/v1/bookings/{booking_id}`                     | Obtener por ID                     |
| PUT    | `/api/v1/bookings/{booking_id}`                     | Actualizar *(Auth)*                |
| DELETE | `/api/v1/bookings/{booking_id}`                     | Eliminar *(Auth)*                  |
| GET    | `/api/v1/bookings/report`                           | Reporte por periodo                |
| GET    | `/api/v1/bookings/my/calendar`                      | Calendario del host *(Auth)*       |
| GET    | `/api/v1/bookings/my/earnings`                      | Ganancias del host *(Auth)*        |
| POST   | `/api/v1/uploads/file`                              | Upload server‑side *(Auth)*        |
| POST   | `/api/v1/uploads/presign`                           | Pre‑signed POST                    |
| GET    | `/api/v1/uploads/url`                               | Pre‑signed GET                     |
| DELETE | `/api/v1/uploads`                                   | Eliminar objeto                    |

---

## 🛠️ Debug & Troubleshooting

> Guía rápida para problemas frecuentes

* ❌ **404 con `server: daphne`** → la request va a otro servicio. Ajusta **Traefik** con `PathPrefix(...)` y `priority`.
* ⚠️ **CORS header missing** en 404/5xx → habilita CORS **en Traefik** además de la app.
* 🔁 **Doble `/api/v1` en Swagger** → usa `servers=[{"url":"/"}]` en OpenAPI.
* ⛳ **Slash final** → `redirect_slashes=True`; si hace falta, expón ambos paths.
* 🧵 **Correlación** → usa `X-Request-ID` en cliente y busca el mismo `rid` en logs.

---

## 📄 Licencia y contacto

* **Licencia**: Proprietary (ver `license_info` en la app)
* **Contacto**: Nexovo Dev Team — [support@nexovo.com](mailto:support@nexovo.com) — [https://nexovo.com.co/developers](https://nexovo.com.co/developers)
