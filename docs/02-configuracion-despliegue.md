# 6. Documentación del proceso de configuración del despliegue

### 6.1 Configuración AWS

#### 6.1.1 Recursos creados

1. **VPC** — `10.0.0.0/16` en la región indicada por el profesor.
2. **Subred pública** — `10.0.1.0/24` con ruta a Internet Gateway.
3. **Subred privada** — `10.0.2.0/24` sin acceso directo a Internet.
4. **Internet Gateway** — conectado a la VPC, referenciado en la tabla de rutas pública.
5. **Elastic IP** — asociada a la instancia EC2 del balanceador.
6. **Route tables** — una pública (con `0.0.0.0/0 → IGW`) y una privada (con NAT Gateway opcional).

#### 6.1.2 Instancias EC2

| Instancia | AMI | Tipo | Subred | Security Group | Contenedor |
|---|---|---|---|---|---|
| Balanceador | Ubuntu Server LTS | `t2.micro` | Pública | `sg-lb` | `nginx-lb` |
| Web Server 1 | Ubuntu Server LTS | `t2.micro` | Privada | `sg-web` | `web-en` |
| Web Server 2 | Ubuntu Server LTS | `t2.micro` | Privada | `sg-web` | `web-es` |
| Base de datos | Ubuntu Server LTS | `t2.micro` | Privada | `sg-db` | `db` |
| Estadísticas | Ubuntu Server LTS | `t2.micro` | Privada | `sg-stats` | `stats` |

> **Modo laboratorio:** Se puede usar una sola EC2 pública con `docker compose up -d --build` para levantar todos los contenedores. Solo se exponen puertos 80 y 443 del balanceador; Flask/PostgreSQL quedan sin puertos publicados al host.

#### 6.1.3 Instalación de Docker en cada EC2 (Ubuntu)

```bash
# Actualizar paquetes
sudo apt update
sudo apt install -y ca-certificates curl gnupg openssl git

# Agregar clave GPG de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar repositorio Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine + Compose
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Agregar usuario al grupo docker
sudo usermod -aG docker ubuntu
```

Cerrar y volver a abrir la sesión SSH para aplicar el grupo `docker`.

### 6.2 Configuración DNS

#### 6.2.1 Objetivo

Crear un nombre público que resuelva a la IP pública (Elastic IP) del balanceador NGINX.

```
www.[dominio] → Registro A → Elastic IP del balanceador
```

#### 6.2.2 Opciones de proveedor DNS (gratuitas/académicas)

| Proveedor | Tipo | URL |
|---|---|---|
| DuckDNS | Subdominio gratuito bajo `duckdns.org` | https://www.duckdns.org/ |
| No-IP | Hostname gratuito de entrada | https://www.noip.com/free |
| FreeDNS (afraid.org) | DNS y subdominios gratuitos | https://freedns.afraid.org/ |
| Dominio institucional | Según permiso del profesor | — |

#### 6.2.3 Registro DNS requerido

| Tipo | Nombre | Valor | TTL |
|---|---|---|---|
| A | `www` | IP pública del balanceador | 300 |
| A | `@` | IP pública del balanceador | 300 |

Ejemplo con DuckDNS:
```
proyecto-telematica.duckdns.org → Elastic IP del balanceador
```

#### 6.2.4 Comprobación DNS

```bash
nslookup www.[dominio]
ping www.[dominio]
curl -k https://www.[dominio]
```

Resultado esperado:
- `nslookup` devuelve la IP pública del balanceador.
- `ping` resuelve el nombre (puede fallar respuesta ICMP si AWS lo bloquea).
- `curl -k` carga el HTML de una de las dos aplicaciones web.

### 6.3 Certificado HTTPS

#### 6.3.1 Opción recomendada: Let's Encrypt con Certbot

**Instalación (Ubuntu):**

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/local/bin/certbot
```

**Generar certificado:**

```bash
# Detener NGINX temporalmente para usar modo standalone
docker compose stop nginx-lb

# Generar certificado
sudo certbot certonly --standalone -d www.[dominio] -d [dominio]

# Copiar certificados al directorio de Docker
sudo cp /etc/letsencrypt/live/www.[dominio]/fullchain.pem nginx/certs/fullchain.pem
sudo cp /etc/letsencrypt/live/www.[dominio]/privkey.pem nginx/certs/privkey.pem
sudo chown "$USER":"$USER" nginx/certs/fullchain.pem nginx/certs/privkey.pem

# Reiniciar NGINX
docker compose up -d nginx-lb
```

**Renovación:**

```bash
sudo certbot renew --dry-run
# Si se renueva, copiar nuevos .pem y recargar:
docker compose exec nginx-lb nginx -s reload
```

#### 6.3.2 Opción alternativa: certificado autofirmado (solo laboratorio)

```bash
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem \
  -subj "/CN=localhost"
```

> **Nota:** El certificado autofirmado genera advertencia en el navegador porque la autoridad emisora no es de confianza. No se recomienda para la entrega final si el proyecto exige certificado público válido.

#### 6.3.3 Detalles del certificado utilizado

El proyecto implementa un certificado autofirmado con los siguientes detalles:

| Propiedad | Valor |
|-----------|-------|
| **Dominio** | localhost |
| **Tipo** | Certificado autofirmado (para laboratorio) |
| **Validez** | 21 de mayo 2026 - 20 de junio 2026 |
| **Algoritmo** | RSA 2048-bit |
| **Uso** | SSL/TLS para HTTPS |
| **Ubicación** | `nginx/certs/fullchain.pem` (público) y `nginx/certs/privkey.pem` (privado) |

#### 6.3.4 Configuración en NGINX

El certificado se configura en `nginx/nginx.conf` (líneas 48-49):

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name _;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
}
```

**Explicación:**
- `listen 443 ssl`: Escucha conexiones HTTPS en puerto 443
- `http2 on`: Activa protocolo HTTP/2 para mejor rendimiento
- `ssl_certificate`: Certificado público (puede compartirse)
- `ssl_certificate_key`: Llave privada (CONFIDENCIAL, nunca compartir)
- `ssl_protocols TLSv1.2 TLSv1.3`: Solo protocolos HTTPS modernos

#### 6.3.5 Montaje en Docker

En `docker-compose.yml` (líneas 10-11), se monta el certificado:

```yaml
volumes:
  - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  - ./nginx/certs:/etc/nginx/certs:ro
```

El sufijo `:ro` (read-only) significa que el contenedor puede leer pero no modificar estos archivos.

#### 6.3.6 Para producción en AWS con Let's Encrypt

En despliegue real en AWS, se debe usar **Let's Encrypt** (certificado público válido y gratuito):

```bash
# Instalar Certbot
sudo snap install --classic certbot

# Generar certificado válido
sudo certbot certonly --standalone -d midominio.com -d www.midominio.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/midominio.com/fullchain.pem ./nginx/certs/
sudo cp /etc/letsencrypt/live/midominio.com/privkey.pem ./nginx/certs/

# Recargar NGINX
docker compose exec nginx-lb nginx -s reload
```

La renovación automática se hace con:

```bash
sudo certbot renew
```

### 6.4 Configuración Docker y Docker Compose

#### 6.4.1 Archivo `docker-compose.yml`

El archivo define 5 servicios, 2 redes y 1 volumen persistente:

```yaml
services:
  nginx-lb:           # Balanceador NGINX con HTTPS
    image: nginx:stable-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on: [web-en, web-es, stats]
    networks: [public, backend]

  web-en:             # Web Server 1 — Inglés
    build: ./web-en
    env_file: .env
    environment:
      DB_HOST: db
      SERVED_BY: Served by Web Server 1 - English
      APP_LANGUAGE: English
    expose: ["5000"]
    depends_on:
      db: { condition: service_healthy }
    networks: [backend]

  web-es:             # Web Server 2 — Español
    build: ./web-es
    env_file: .env
    environment:
      DB_HOST: db
      SERVED_BY: Atendido por Web Server 2 - Espanol
      APP_LANGUAGE: Espanol
    expose: ["5000"]
    depends_on:
      db: { condition: service_healthy }
    networks: [backend]

  stats:              # Aplicación de estadísticas + SMTP
    build: ./stats
    env_file: .env
    environment:
      DB_HOST: db
      MPLBACKEND: Agg
    expose: ["5000"]
    depends_on:
      db: { condition: service_healthy }
    networks: [backend]

  db:                 # PostgreSQL con healthcheck
    image: postgres:16-alpine
    env_file: .env
    environment:
      POSTGRES_DB: ${DB_NAME:-telematica}
      POSTGRES_USER: ${DB_USER:-telematica_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change_me_in_production}
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$${POSTGRES_USER}\" -d \"$${POSTGRES_DB}\""]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [backend]

networks:
  public:   { driver: bridge }
  backend:  { driver: bridge, internal: false }

volumes:
  db_data:
```

#### 6.4.2 Redes Docker

| Red | Propósito |
|---|---|
| `public` | Conecta el balanceador NGINX con el host para publicar puertos 80 y 443 |
| `backend` | Conecta NGINX, Flask (web-en, web-es), stats y PostgreSQL internamente |

Los servicios web y base de datos usan `expose` (no `ports`), por lo tanto **no quedan publicados directamente al host**.

#### 6.4.3 Variables de entorno (`.env`)

```env
# Dominio
DOMAIN_NAME=localhost
PUBLIC_URL=https://localhost

# PostgreSQL
DB_HOST=db
DB_PORT=5432
DB_NAME=telematica
DB_USER=telematica_user
DB_PASSWORD=change_me_in_production

# Flask/Gunicorn
FLASK_ENV=production

# SMTP para envío de estadísticas
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<correo@gmail.com>
SMTP_PASSWORD=<app_password>
SMTP_FROM=<correo@gmail.com>
SMTP_TO=ialondonoo@eafit.edu.co

# Token de administrador para panel de estadísticas
ADMIN_TOKEN=change_this_admin_token
```

#### 6.4.4 Dockerfiles

Los tres servicios construidos (web-en, web-es, stats) utilizan el mismo patrón de Dockerfile:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

> El servicio `stats` agrega adicionalmente `ENV MPLBACKEND=Agg` para que Matplotlib funcione sin display gráfico.

#### 6.4.5 Comandos de despliegue

**Despliegue automatizado:**

```bash
# Linux/macOS
./scripts/deploy.sh

# Windows PowerShell
.\scripts\deploy.ps1
```

El script `deploy.sh` / `deploy.ps1`:
1. Copia `.env.example` a `.env` si no existe.
2. Genera un certificado autofirmado si no hay certificados en `nginx/certs/`.
3. Ejecuta `docker compose up -d --build`.
4. Muestra el estado de los contenedores con `docker compose ps`.

**Comandos manuales:**

```bash
# Levantar todos los servicios
docker compose up -d --build

# Ver estado
docker compose ps

# Ver logs
docker compose logs -f nginx-lb
docker compose logs -f web-en
docker compose logs -f web-es
docker compose logs -f stats
docker compose logs -f db

# Detener
docker compose down

# Detener y eliminar datos (precaución)
docker compose down -v
```

#### 6.4.6 Despliegue con múltiples EC2

Para una sustentación estricta con instancias separadas:

1. Clonar el repositorio en cada instancia EC2.
2. En Web Server 1: ejecutar solo `web-en`.
3. En Web Server 2: ejecutar solo `web-es`.
4. En la instancia de BD: ejecutar `db`.
5. En la instancia de stats: ejecutar `stats`.
6. En el balanceador, editar `nginx/nginx.conf` reemplazando los nombres Docker por IPs privadas reales:

```nginx
upstream backend_web {
    server 10.0.2.11:5000;   # IP real de Web Server 1
    server 10.0.2.12:5000;   # IP real de Web Server 2
}

upstream stats_app {
    server 10.0.2.30:5000;   # IP real del servidor de stats
}
```

7. Reiniciar NGINX: `docker compose restart nginx-lb`
