## 7. Documentación de las aplicaciones

### 7.1 Balanceador de carga — NGINX

#### 7.1.1 Rol

NGINX cumple dos funciones exigidas por el proyecto:

1. **Proxy inverso:** recibe solicitudes HTTPS del cliente externo y las reenvía a los servicios internos por HTTP en el puerto 5000.
2. **Balanceador de carga:** reparte solicitudes entre Web Server 1 (inglés) y Web Server 2 (español) con política **round-robin** (por defecto en NGINX).

#### 7.1.2 Archivo de configuración completo (`nginx/nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    keepalive_timeout 65;
    server_tokens off;

    # UPSTREAM: Round Robin entre los dos servidores web
    upstream backend_web {
        # Round robin es la política por defecto de NGINX.
        # No se necesita directiva adicional.
        server web-en:5000;
        server web-es:5000;
    }

    # UPSTREAM: Servicio de estadísticas
    upstream stats_app {
        server stats:5000;
    }

    # Servidor HTTP (puerto 80) — Redirección a HTTPS
    server {
        listen 80;
        server_name _;

        # Soporte para validación Let's Encrypt
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirigir todo el tráfico HTTP a HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # Servidor HTTPS (puerto 443) — Principal
    server {
        listen 443 ssl;
        http2 on;
        server_name _;

        # Certificados SSL/TLS
        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;

        # Headers de seguridad
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options SAMEORIGIN always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;

        # Verificación básica de NGINX
        location = /nginx-health {
            access_log off;
            return 200 "nginx ok\n";
        }

        # Panel de estadísticas → proxy a stats:5000
        location /admin/ {
            proxy_pass http://stats_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }

        # Formulario de registro → round robin a web-en/web-es
        location / {
            proxy_pass http://backend_web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
```

#### 7.1.3 Explicación de la configuración

| Directiva/Bloque | Propósito |
|---|---|
| `upstream backend_web` | Define el pool de servidores web. Round-robin es la política por defecto. |
| `upstream stats_app` | Define el servicio de estadísticas como backend separado. |
| `listen 80` + `return 301` | Redirige todo el tráfico HTTP a HTTPS. |
| `listen 443 ssl` + `http2 on` | Escucha HTTPS con soporte HTTP/2. |
| `ssl_protocols TLSv1.2 TLSv1.3` | Solo permite protocolos TLS modernos y seguros. |
| `server_tokens off` | Oculta la versión de NGINX en las respuestas. |
| `proxy_set_header Host` | Reenvía el nombre de host original al backend. |
| `proxy_set_header X-Real-IP` | Reenvía la IP real del cliente al backend. |
| `proxy_set_header X-Forwarded-For` | Mantiene la cadena de proxies para trazabilidad. |
| `proxy_set_header X-Forwarded-Proto` | Informa al backend que la conexión externa es HTTPS. |
| `location /admin/` | Dirige las rutas de administración al servicio de estadísticas. |
| `location /` | Dirige las solicitudes generales a los servidores web con round-robin. |

#### 7.1.4 Rutas de NGINX

| Ruta | Destino | Descripción |
|---|---|---|
| `/` | `backend_web` (round-robin) | Formulario de registro, alterna entre web-en y web-es |
| `/admin/stats` | `stats_app` | Dashboard de estadísticas |
| `/admin/send-email` | `stats_app` | Envío de reporte por correo |
| `/nginx-health` | Respuesta directa NGINX | Verificación de salud del balanceador |

#### 7.1.5 Validación de configuración

```bash
# Validar sintaxis de nginx.conf
docker compose exec nginx-lb nginx -t

# Verificar salud del balanceador
curl -k https://www.[dominio]/nginx-health
```

---

### 7.2 Aplicación Web Server 1 — Inglés (`web-en`)

#### 7.2.1 Descripción general

Aplicación web desarrollada en **Python Flask** que se despliega en el contenedor `web-en`. Toda la interfaz está en **inglés**. Se accede a través de la ruta `/` cuando NGINX redirige al contenedor `web-en` según la política round-robin.

#### 7.2.2 Tecnologías

| Tecnología | Versión | Propósito |
|---|---|---|
| Python | 3.12 | Lenguaje de programación |
| Flask | ≥3.0, <4 | Framework web |
| Gunicorn | ≥22, <24 | Servidor WSGI de producción |
| psycopg2-binary | ≥2.9, <3 | Driver PostgreSQL para Python |

#### 7.2.3 Estructura de archivos

```
web-en/
├── Dockerfile           # Imagen Docker basada en python:3.12-slim
├── app.py               # Aplicación Flask principal
├── requirements.txt     # Dependencias: Flask, gunicorn, psycopg2-binary
├── static/
│   └── style.css        # Estilos CSS de la interfaz
└── templates/
    └── index.html       # Template HTML del formulario (Jinja2)
```

#### 7.2.4 Campos del formulario

| Campo en inglés | Nombre del campo (`name`) | Tipo de input | Opciones |
|---|---|---|---|
| Name | `name` | Text input (max 120 caracteres) | Texto libre |
| Commune zone | `commune` | Select | Commune 1 a Commune 10 |
| Date/time of entry | `entry_at` | Datetime-local | Selector de fecha y hora |
| Undergraduate program of interest | `program` | Select | Medicine, Engineering, Law, Bachelor / Education |

#### 7.2.5 Indicador de servidor

La página muestra un badge/etiqueta con el texto:

```
Served by Web Server 1 - English
```

Este indicador permite comprobar visualmente el balanceo round-robin al alternar con el Web Server 2 en español.

#### 7.2.6 Funcionalidad de la aplicación (`app.py`)

1. **Ruta `GET /`**: Renderiza el formulario de registro vacío con la fecha/hora actual.
2. **Ruta `POST /`**: Procesa el formulario:
   - Valida que el nombre tenga al menos 2 caracteres.
   - Valida que la comuna y la carrera sean valores válidos.
   - Valida el formato de la fecha de ingreso.
   - Si todo es válido, inserta un registro en PostgreSQL con: `name`, `commune`, `program`, `language` (English), `entry_at`, `served_by` y `client_ip`.
   - Retorna el ID de registro asignado como confirmación de éxito.
3. **Ruta `GET /health`**: Endpoint de salud que retorna `{"status": "ok", "served_by": "..."}` en formato JSON.

#### 7.2.7 Diseño de la interfaz

La interfaz utiliza un diseño moderno con:
- Fuente **Inter** (sans-serif).
- Fondo con gradiente sutil azul/naranja.
- Panel central blanco con sombra (`box-shadow`).
- Formulario en cuadrícula de 2 columnas (responsive, 1 columna en móvil).
- Badge de servidor en azul claro.
- Alertas de error (rojo) y éxito (verde).
- Botón para ver las estadísticas (`/admin/stats`).

---

### 7.3 Aplicación Web Server 2 — Español (`web-es`)

#### 7.3.1 Descripción general

Aplicación web desarrollada en **Python Flask** que se despliega en el contenedor `web-es`. Toda la interfaz está en **español**. Se accede a través de la ruta `/` cuando NGINX redirige al contenedor `web-es` según la política round-robin.

#### 7.3.2 Tecnologías

Las mismas que Web Server 1: Python 3.12, Flask, Gunicorn y psycopg2-binary.

#### 7.3.3 Estructura de archivos

```
web-es/
├── Dockerfile           # Imagen Docker basada en python:3.12-slim
├── app.py               # Aplicación Flask principal
├── requirements.txt     # Dependencias: Flask, gunicorn, psycopg2-binary
├── static/
│   └── style.css        # Estilos CSS de la interfaz
└── templates/
    └── index.html       # Template HTML del formulario (Jinja2)
```

#### 7.3.4 Campos del formulario

| Campo en español | Nombre del campo (`name`) | Tipo de input | Opciones |
|---|---|---|---|
| Nombre | `name` | Text input (max 120 caracteres) | Texto libre |
| Zona de comuna | `commune` | Select | Comuna 1 a Comuna 10 |
| Fecha de ingreso | `entry_at` | Datetime-local | Selector de fecha y hora |
| Carrera de interés | `program` | Select | Medicina, Ingeniería, Abogacía, Licenciatura |

#### 7.3.5 Indicador de servidor

```
Atendido por Web Server 2 - Espanol
```

#### 7.3.6 Diferencias con Web Server 1

| Aspecto | Web Server 1 (`web-en`) | Web Server 2 (`web-es`) |
|---|---|---|
| Idioma | Inglés | Español |
| Etiqueta del servidor | `Served by Web Server 1 - English` | `Atendido por Web Server 2 - Espanol` |
| Variable `APP_LANGUAGE` | `English` | `Espanol` |
| Mensajes de error | En inglés | En español |
| Mensajes de éxito | En inglés | En español |
| Opciones de comuna | Commune 1–10 | Comuna 1–10 |
| Opciones de carrera | Medicine, Engineering, Law, Bachelor/Education | Medicina, Ingeniería, Abogacía, Licenciatura |
| `<html lang>` | `en` | `es` |
| `<title>` | Admissions Registration | Registro de Aspirantes |

#### 7.3.7 Funcionalidad

Idéntica a Web Server 1 en su lógica de backend: valida el formulario, inserta en PostgreSQL con el idioma `Espanol` y el identificador `Atendido por Web Server 2 - Espanol`. Los datos se almacenan en la **misma tabla** `registrations` que el Web Server 1, permitiendo estadísticas unificadas.

---

### 7.4 Aplicación de Reporte de Estadísticas (`stats`)

#### 7.4.1 Descripción general

Aplicación web en **Python Flask** que consulta la base de datos PostgreSQL, genera gráficas estadísticas con **Matplotlib** y **Chart.js**, y permite enviar el reporte completo por correo electrónico vía SMTP a `ialondonoo@eafit.edu.co`.

Se accede a través de la URL:

```
https://www.[dominio]/admin/stats
```

NGINX redirige las solicitudes `/admin/` al contenedor `stats` en el puerto 5000.

#### 7.4.2 Tecnologías

| Tecnología | Versión | Propósito |
|---|---|---|
| Python | 3.12 | Lenguaje de programación |
| Flask | ≥3.0, <4 | Framework web |
| Gunicorn | ≥22, <24 | Servidor WSGI |
| Matplotlib | ≥3.8, <4 | Generación de gráficas de barras (PNG) |
| Chart.js | CDN | Gráfica interactiva de barras agrupadas (comuna/carrera) |
| psycopg2-binary | ≥2.9, <3 | Driver PostgreSQL |
| smtplib (stdlib) | — | Envío de correo SMTP |

#### 7.4.3 Estructura de archivos

```
stats/
├── Dockerfile           # Imagen Docker con MPLBACKEND=Agg
├── app.py               # Aplicación Flask con gráficas y SMTP
├── requirements.txt     # Flask, gunicorn, matplotlib, psycopg2-binary
└── templates/
    └── stats.html       # Template HTML del dashboard (Jinja2)
```

#### 7.4.4 Funciones de estadísticas

La aplicación ejecuta las siguientes consultas SQL:

| Estadística | Consulta SQL |
|---|---|
| Total de usuarios registrados | `SELECT COUNT(*) FROM registrations` |
| Total por comuna | `SELECT commune, COUNT(*) ... GROUP BY commune ORDER BY commune` |
| Total por carrera | `SELECT program, COUNT(*) ... GROUP BY program ORDER BY total DESC` |
| Total por comuna y carrera | `SELECT commune, program, COUNT(*) ... GROUP BY commune, program` |
| Últimos 10 registros | `SELECT id, name, commune, program, language, entry_at, served_by ... LIMIT 10` |

#### 7.4.5 Gráficas generadas

1. **Gráfica de barras por comuna** — Generada con Matplotlib como imagen PNG (codificada en base64 e incrustada en el HTML).
2. **Gráfica de barras por carrera** — Generada con Matplotlib como imagen PNG.
3. **Gráfica interactiva de barras agrupadas por comuna y carrera** — Generada con Chart.js en el navegador del cliente.

#### 7.4.6 Panel de estadísticas (dashboard)

El dashboard muestra:

- **Métrica principal:** total de usuarios registrados.
- **Sección 1:** gráfica de barras por comuna (Matplotlib).
- **Sección 2:** gráfica de barras por carrera (Matplotlib).
- **Sección 3:** gráfica interactiva de barras agrupadas por comuna y carrera (Chart.js).
- **Tabla 1:** total de usuarios por comuna.
- **Tabla 2:** total de usuarios por comuna y carrera.
- **Tabla 3:** últimos 10 registros con ID, nombre, comuna, carrera, idioma, fecha de ingreso y servidor.
- **Botón:** "Enviar estadísticas por correo" para enviar el reporte por SMTP.

#### 7.4.7 Envío de correo por SMTP

**Rutas:**

| Ruta | Método | Descripción |
|---|---|---|
| `/admin/stats` | GET | Muestra el dashboard de estadísticas |
| `/admin/send-email` | POST | Envía el reporte por correo electrónico |
| `/health` | GET | Endpoint de salud |

**Proceso de envío:**

1. Se verifican las variables SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO`.
2. Se consultan las estadísticas actualizadas de la base de datos.
3. Se generan las gráficas de barras con Matplotlib (formato PNG).
4. Se construye un correo con:
   - **Asunto:** "Estadísticas acumuladas - Proyecto Telematica"
   - **Cuerpo de texto:** resumen con total de usuarios, desglose por comuna, desglose por comuna/carrera, y créditos.
   - **Adjuntos:** dos imágenes PNG (usuarios por comuna y usuarios por carrera).
5. Se envía usando `smtplib.SMTP` con STARTTLS (puerto 587) o `smtplib.SMTP_SSL` (puerto 465).
6. El destinatario es: `ialondonoo@eafit.edu.co`

**Configuración SMTP para Gmail:**

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@gmail.com
SMTP_PASSWORD=app_password_de_16_caracteres
SMTP_FROM=correo@gmail.com
SMTP_TO=ialondonoo@eafit.edu.co
```

> Se debe generar un "App Password" en la configuración de seguridad de la cuenta de Google, no usar la contraseña normal.

#### 7.4.8 Seguridad del panel

El panel de estadísticas está protegido por un `ADMIN_TOKEN` opcional. Si `ADMIN_TOKEN` está configurado (y no es el valor por defecto `change_this_admin_token`), el acceso requiere enviar el token como:
- Header HTTP: `X-Admin-Token`
- Query parameter: `?token=<valor>`

---

### 7.5 Base de datos — PostgreSQL

#### 7.5.1 Configuración

- **Motor:** PostgreSQL 16 (imagen `postgres:16-alpine`)
- **Base de datos:** `telematica`
- **Usuario:** `telematica_user`
- **Puerto:** `5432` (solo accesible internamente)
- **Volumen persistente:** `db_data` montado en `/var/lib/postgresql/data`
- **Healthcheck:** `pg_isready` cada 10 segundos

#### 7.5.2 Esquema de la tabla `registrations`

```sql
CREATE TABLE IF NOT EXISTS registrations (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    commune     VARCHAR(20) NOT NULL,
    program     VARCHAR(50) NOT NULL,
    language    VARCHAR(20) NOT NULL,
    entry_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    served_by   VARCHAR(50),
    client_ip   VARCHAR(80)
);

CREATE INDEX IF NOT EXISTS idx_registrations_commune ON registrations (commune);
CREATE INDEX IF NOT EXISTS idx_registrations_program ON registrations (program);
CREATE INDEX IF NOT EXISTS idx_registrations_entry_at ON registrations (entry_at);
```

#### 7.5.3 Descripción de columnas

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL | Identificador único autoincremental |
| `name` | VARCHAR(120) | Nombre del aspirante |
| `commune` | VARCHAR(20) | Comuna seleccionada (ej: "Comuna 1" o "Commune 1") |
| `program` | VARCHAR(50) | Carrera de interés |
| `language` | VARCHAR(20) | Idioma del servidor que atendió (English/Espanol) |
| `entry_at` | TIMESTAMP | Fecha/hora de ingreso seleccionada por el usuario |
| `created_at` | TIMESTAMP | Fecha/hora de creación del registro (automática) |
| `served_by` | VARCHAR(50) | Identificador del servidor web que procesó el registro |
| `client_ip` | VARCHAR(80) | IP del cliente (obtenida de `X-Forwarded-For`) |

#### 7.5.4 Verificación

```bash
docker compose exec db psql -U telematica_user -d telematica \
  -c "SELECT id, name, commune, program, language, entry_at, served_by FROM registrations ORDER BY id DESC;"
```

#### 7.5.5 Backup

```bash
./scripts/backup-db.sh
# El respaldo queda en backups/<nombre_db>-<timestamp>.sql
```
